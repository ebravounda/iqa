from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import os
import logging

from database import db
from auth import get_current_admin, check_role
from models import SaaSPlanCreate, SaaSPlanUpdate, BroadcastCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

SAAS_FEATURE_KEYS = [
    "has_qr_access", "has_guest_passes", "has_classes", "has_pos",
    "has_analytics", "has_gamification", "has_routines", "has_email_smtp",
    "has_stripe_members", "has_mercadopago", "has_iframes", "has_advanced_accounting"
]

# ==================== SaaS PLANS ====================

@router.post("/saas/plans")
async def create_saas_plan(plan: SaaSPlanCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin"])
    plan_dict = plan.model_dump()
    plan_dict["id"] = str(uuid.uuid4())
    plan_dict["active"] = True
    plan_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.saas_plans.insert_one(plan_dict)
    plan_dict.pop("_id", None)
    return plan_dict

@router.get("/saas/plans")
async def get_saas_plans(admin: dict = Depends(get_current_admin)):
    plans = await db.saas_plans.find({"active": True}, {"_id": 0}).to_list(50)
    return plans

@router.put("/saas/plans/{plan_id}")
async def update_saas_plan(plan_id: str, plan_update: SaaSPlanUpdate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin"])
    raw = plan_update.model_dump()
    update_data = {}
    for k, v in raw.items():
        if v is not None:
            update_data[k] = v
        elif k in SAAS_FEATURE_KEYS:
            # For feature flags, treat None as "not sent" but include False explicitly
            pass
    # Ensure boolean feature flags are always written when present in the request body
    for k in SAAS_FEATURE_KEYS:
        if raw.get(k) is not None:
            update_data[k] = raw[k]
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.saas_plans.update_one({"id": plan_id}, {"$set": update_data})
    plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
    return plan

@router.delete("/saas/plans/{plan_id}")
async def delete_saas_plan(plan_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin"])
    await db.saas_plans.update_one({"id": plan_id}, {"$set": {"active": False}})
    return {"message": "Plan SaaS eliminado"}

@router.put("/gyms/{gym_id}/saas-plan")
async def assign_saas_plan(gym_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin"])
    plan_id = body.get("saas_plan_id")
    if not plan_id:
        raise HTTPException(status_code=400, detail="saas_plan_id requerido")
    plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan SaaS no encontrado")
    await db.gyms.update_one({"id": gym_id}, {"$set": {
        "saas_plan_id": plan_id,
        "saas_plan_name": plan["name"],
        "max_members": plan["max_members"],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }})
    return {"message": f"Plan '{plan['name']}' asignado al gimnasio"}

@router.get("/gyms/{gym_id}/saas-features")
async def get_gym_saas_features(gym_id: str, admin: dict = Depends(get_current_admin)):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    plan_id = gym.get("saas_plan_id")
    if not plan_id:
        return {
            **{k: False for k in SAAS_FEATURE_KEYS},
            "has_qr_access": True,
            "max_members": gym.get("max_members", 500),
            "plan_name": "Sin Plan",
            "price_monthly": 0,
            "currency": "EUR",
            "description": None
        }
    plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        return {
            **{k: False for k in SAAS_FEATURE_KEYS},
            "has_qr_access": True,
            "max_members": gym.get("max_members", 500),
            "plan_name": "Plan no encontrado",
            "price_monthly": 0,
            "currency": "EUR",
            "description": None
        }
    result = {k: plan.get(k, False) for k in SAAS_FEATURE_KEYS}
    result["max_members"] = plan.get("max_members", 500)
    result["plan_name"] = plan.get("name", "")
    result["price_monthly"] = plan.get("price_monthly", 0)
    result["currency"] = plan.get("currency", "EUR")
    result["description"] = plan.get("description")
    return result

# ==================== SaaS SUBSCRIPTION (Gym pays Platform) ====================

@router.get("/saas/my-subscription")
async def get_my_subscription(admin: dict = Depends(get_current_admin)):
    """Gym Admin gets their current SaaS subscription details"""
    gym_id = admin.get("gym_id")
    if not gym_id:
        raise HTTPException(status_code=400, detail="No gym_id asociado")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    plan_id = gym.get("saas_plan_id")
    plan = None
    if plan_id:
        plan = await db.saas_plans.find_one({"id": plan_id, "active": True}, {"_id": 0})
    member_count = await db.members.count_documents({"gym_id": gym_id, "status": {"$ne": "deleted"}})
    last_payment = await db.saas_payments.find_one(
        {"gym_id": gym_id, "status": "completed"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    return {
        "gym_name": gym.get("name"),
        "plan": plan,
        "member_count": member_count,
        "max_members": gym.get("max_members", 500),
        "last_payment": last_payment,
        "saas_plan_id": plan_id
    }

@router.get("/saas/available-plans")
async def get_available_saas_plans():
    """Public endpoint - get available SaaS plans for gyms to subscribe"""
    plans = await db.saas_plans.find({"active": True}, {"_id": 0}).to_list(20)
    return plans

@router.post("/saas/subscribe")
async def subscribe_saas_plan(request: Request, admin: dict = Depends(get_current_admin)):
    """Gym Admin subscribes to a SaaS plan via Stripe (pays Platform owner)"""
    gym_id = admin.get("gym_id")
    if not gym_id:
        raise HTTPException(status_code=400, detail="Solo Gym Admins pueden suscribirse")
    body = await request.json()
    plan_id = body.get("plan_id")
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id requerido")
    plan = await db.saas_plans.find_one({"id": plan_id, "active": True}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan SaaS no encontrado")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    platform_stripe_key = os.environ.get("PLATFORM_STRIPE_KEY", "")
    if not platform_stripe_key:
        raise HTTPException(status_code=500, detail="Stripe de la plataforma no configurado. Contacta al administrador.")
    try:
        import stripe
        stripe.api_key = platform_stripe_key
        currency = plan.get("currency", "EUR").lower()
        amount = int(plan["price_monthly"] * 100)
        if amount <= 0:
            await db.gyms.update_one({"id": gym_id}, {"$set": {
                "saas_plan_id": plan_id,
                "saas_plan_name": plan["name"],
                "max_members": plan["max_members"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }})
            return {"message": "Plan gratuito asignado", "free": True}
        frontend_url = "https://app.ingresoqr.com"
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": f"IngresoQR - {plan['name']}",
                        "description": plan.get("description", f"Plan SaaS para {gym['name']}")
                    },
                    "unit_amount": amount,
                    "recurring": {"interval": "month"}
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{frontend_url}/admin/settings?saas_payment=success",
            cancel_url=f"{frontend_url}/admin/settings?saas_payment=cancel",
            metadata={
                "gym_id": gym_id,
                "saas_plan_id": plan_id,
                "type": "saas_subscription"
            },
            customer_email=admin.get("email") or gym.get("email"),
        )
        payment_record = {
            "id": str(uuid.uuid4()),
            "stripe_session_id": session.id,
            "gym_id": gym_id,
            "saas_plan_id": plan_id,
            "amount": plan["price_monthly"],
            "currency": currency,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.saas_payments.insert_one(payment_record)
        return {"payment_url": session.url, "session_id": session.id}
    except ImportError:
        raise HTTPException(status_code=500, detail="Stripe SDK no instalado")
    except Exception as e:
        logger.error(f"SaaS Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)}")

@router.post("/saas/stripe-webhook")
async def saas_stripe_webhook(request: Request):
    """Webhook for SaaS subscription payments"""
    body = await request.json()
    event_type = body.get("type")
    if event_type in ("checkout.session.completed", "invoice.paid"):
        session = body.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        if metadata.get("type") == "saas_subscription":
            gym_id = metadata.get("gym_id")
            plan_id = metadata.get("saas_plan_id")
            if gym_id and plan_id:
                plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
                if plan:
                    await db.gyms.update_one({"id": gym_id}, {"$set": {
                        "saas_plan_id": plan_id,
                        "saas_plan_name": plan["name"],
                        "max_members": plan["max_members"],
                        "saas_subscription_active": True,
                        "saas_last_payment": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }})
                    await db.saas_payments.update_one(
                        {"stripe_session_id": session.get("id")},
                        {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
                    )
                    logger.info(f"[SAAS] Plan '{plan['name']}' activated for gym {gym_id}")
    return {"received": True}

# ==================== BROADCAST ====================

@router.post("/broadcast")
async def create_broadcast(broadcast: BroadcastCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin"])
    broadcast_dict = {
        "id": str(uuid.uuid4()),
        "title": broadcast.title,
        "message": broadcast.message,
        "priority": broadcast.priority,
        "created_by": admin["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "active": True,
        "dismissed_by": []
    }
    await db.broadcasts.insert_one(broadcast_dict)
    broadcast_dict.pop("_id", None)
    return broadcast_dict

@router.get("/broadcast/active")
async def get_active_broadcasts(admin: dict = Depends(get_current_admin)):
    broadcasts = await db.broadcasts.find({"active": True}, {"_id": 0}).sort("created_at", -1).to_list(10)
    user_id = admin.get("id", "")
    result = []
    for b in broadcasts:
        if user_id not in b.get("dismissed_by", []):
            result.append(b)
    return result

@router.post("/broadcast/{broadcast_id}/dismiss")
async def dismiss_broadcast(broadcast_id: str, admin: dict = Depends(get_current_admin)):
    await db.broadcasts.update_one(
        {"id": broadcast_id},
        {"$addToSet": {"dismissed_by": admin["id"]}}
    )
    return {"message": "Broadcast dismissed"}

@router.delete("/broadcast/{broadcast_id}")
async def delete_broadcast(broadcast_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin"])
    await db.broadcasts.update_one({"id": broadcast_id}, {"$set": {"active": False}})
    return {"message": "Broadcast eliminado"}
