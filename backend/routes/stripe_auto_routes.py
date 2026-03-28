from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging

from database import db
from auth import get_current_admin
from routes.misc_routes import send_gym_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# ==================== Stripe Payment Links ====================

@router.post("/payments/create-link")
async def create_payment_link(request: Request, admin: dict = Depends(get_current_admin)):
    body = await request.json()
    member_id = body.get("member_id")
    plan_id = body.get("plan_id")
    if not member_id or not plan_id:
        raise HTTPException(status_code=400, detail="member_id y plan_id requeridos")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    gym = await db.gyms.find_one({"id": member.get("gym_id")}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    stripe_key = gym.get("stripe_secret_key") or os.environ.get("STRIPE_API_KEY")
    if not stripe_key:
        raise HTTPException(status_code=400, detail="Stripe no configurado para este gimnasio. Configura tu clave secreta en Ajustes o en el archivo .env")
    try:
        import stripe
        stripe.api_key = stripe_key
        currency = gym.get("stripe_currency", gym.get("currency", "eur")).lower()
        amount = int(plan["price"] * 100)
        frontend_url = gym.get("frontend_url", "https://app.ingresoqr.com")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": f"{plan['name']} - {gym['name']}"},
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{frontend_url}/app/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/app/membership",
            metadata={
                "member_id": member_id,
                "plan_id": plan_id,
                "gym_id": gym["id"],
            },
            customer_email=member.get("email"),
        )
        payment_record = {
            "id": str(uuid.uuid4()),
            "stripe_session_id": session.id,
            "member_id": member_id,
            "plan_id": plan_id,
            "gym_id": gym["id"],
            "amount": plan["price"],
            "currency": currency,
            "status": "pending",
            "payment_url": session.url,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.stripe_payments.insert_one(payment_record)
        return {"payment_url": session.url, "session_id": session.id}
    except ImportError:
        raise HTTPException(status_code=500, detail="Stripe SDK no instalado")
    except Exception as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Error de Stripe: {str(e)}")

@router.post("/payments/send-payment-email")
async def send_payment_email(request: Request, admin: dict = Depends(get_current_admin)):
    body = await request.json()
    member_id = body.get("member_id")
    plan_id = body.get("plan_id")
    if not member_id or not plan_id:
        raise HTTPException(status_code=400, detail="member_id y plan_id requeridos")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member or not member.get("email"):
        raise HTTPException(status_code=400, detail="Socio sin email")
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    gym = await db.gyms.find_one({"id": member.get("gym_id")}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if not gym.get("stripe_secret_key") and not os.environ.get("STRIPE_API_KEY"):
        raise HTTPException(status_code=400, detail="Stripe no configurado")
    try:
        import stripe
        stripe.api_key = gym.get("stripe_secret_key") or os.environ.get("STRIPE_API_KEY")
        currency = gym.get("stripe_currency", gym.get("currency", "eur")).lower()
        amount = int(plan["price"] * 100)
        frontend_url = gym.get("frontend_url", "https://app.ingresoqr.com")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price_data": {"currency": currency, "product_data": {"name": f"{plan['name']} - {gym['name']}"}, "unit_amount": amount}, "quantity": 1}],
            mode="payment",
            success_url=f"{frontend_url}/app/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{frontend_url}/app/membership",
            metadata={"member_id": member_id, "plan_id": plan_id, "gym_id": gym["id"]},
            customer_email=member.get("email"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear sesion de Stripe: {str(e)}")
    color = gym.get("primary_color", "#E1FF01")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:30px;background:#09090B;color:#fff;border-radius:16px;">
        <div style="text-align:center;margin-bottom:20px;">
            <h1 style="color:{color};margin:0;font-size:24px;">{gym.get('name','IngresoQR')}</h1>
        </div>
        <h2 style="color:#FAFAFA;text-align:center;">Realiza el pago de tu membresia ahora!</h2>
        <p>Hola <strong>{member.get('name','Socio')}</strong>,</p>
        <p>Tu plan <strong>{plan['name']}</strong> esta listo para ser activado. Haz click en el boton para realizar el pago de forma segura:</p>
        <div style="text-align:center;margin:30px 0;">
            <a href="{session.url}" style="display:inline-block;background:{color};color:#000;padding:16px 40px;border-radius:50px;font-weight:bold;text-decoration:none;font-size:16px;">
                Pagar {plan['price']} {currency.upper()} Ahora
            </a>
        </div>
        <div style="background:#18181B;padding:16px;border-radius:12px;margin:20px 0;">
            <p style="margin:0;color:#a1a1aa;font-size:14px;"><strong>Plan:</strong> {plan['name']}</p>
            <p style="margin:4px 0 0;color:#a1a1aa;font-size:14px;"><strong>Duracion:</strong> {plan.get('duration_days',30)} dias</p>
            <p style="margin:4px 0 0;color:#a1a1aa;font-size:14px;"><strong>Monto:</strong> {plan['price']} {currency.upper()}</p>
        </div>
        <p style="color:#71717A;font-size:12px;text-align:center;">Este enlace es seguro y valido por 24 horas.</p>
    </div>
    """
    try:
        await send_gym_email(gym["id"], member["email"], f"Paga tu membresia - {gym['name']}", html)
    except Exception as e:
        return {"message": "Link creado pero no se pudo enviar email", "payment_url": session.url, "email_error": str(e)}
    return {"message": "Email de pago enviado correctamente", "payment_url": session.url}

# ==================== Stripe Webhook ====================

@router.post("/payments/stripe-webhook")
async def stripe_webhook(request: Request):
    body = await request.json()
    event_type = body.get("type")
    if event_type == "checkout.session.completed":
        session = body.get("data", {}).get("object", {})
        metadata = session.get("metadata", {})
        member_id = metadata.get("member_id")
        plan_id = metadata.get("plan_id")
        gym_id = metadata.get("gym_id")
        if member_id and plan_id:
            plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
            if plan:
                now = datetime.now(timezone.utc)
                membership = {
                    "id": str(uuid.uuid4()),
                    "member_id": member_id,
                    "plan_id": plan_id,
                    "gym_id": gym_id,
                    "start_date": now.isoformat(),
                    "end_date": (now + timedelta(days=plan.get("duration_days", 30))).isoformat(),
                    "status": "active",
                    "payment_method": "stripe",
                    "amount_paid": session.get("amount_total", 0) / 100,
                    "stripe_session_id": session.get("id"),
                    "created_at": now.isoformat(),
                }
                await db.memberships.insert_one(membership)
                await db.members.update_one({"id": member_id}, {"$set": {"status": "active"}})
                await db.stripe_payments.update_one(
                    {"stripe_session_id": session.get("id")},
                    {"$set": {"status": "completed"}}
                )
                logger.info(f"[STRIPE] Membership activated for member {member_id}, plan {plan_id}")
    return {"received": True}
