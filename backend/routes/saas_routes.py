from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from database import db
from auth import get_current_admin, check_role
from models import SaaSPlanCreate, SaaSPlanUpdate, BroadcastCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

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
    update_data = {k: v for k, v in plan_update.model_dump().items() if v is not None}
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
            "has_pos": False, "has_mercadopago": False, "has_iframes": False,
            "has_advanced_accounting": False, "max_members": gym.get("max_members", 500),
            "plan_name": "Sin Plan"
        }
    plan = await db.saas_plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        return {
            "has_pos": False, "has_mercadopago": False, "has_iframes": False,
            "has_advanced_accounting": False, "max_members": gym.get("max_members", 500),
            "plan_name": "Plan no encontrado"
        }
    return {
        "has_pos": plan.get("has_pos", False),
        "has_mercadopago": plan.get("has_mercadopago", False),
        "has_iframes": plan.get("has_iframes", False),
        "has_advanced_accounting": plan.get("has_advanced_accounting", False),
        "max_members": plan.get("max_members", 500),
        "plan_name": plan.get("name", "")
    }

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
