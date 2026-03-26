from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import os
import logging

from database import db
from auth import get_current_admin, check_role, security, decode_jwt_token
from models import ManualPayment

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.post("/payments/checkout")
async def create_checkout(
    request: Request, plan_id: str,
    credentials = Depends(security)
):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    gym = await db.gyms.find_one({"id": plan["gym_id"]}, {"_id": 0})
    api_key = (gym or {}).get("stripe_secret_key") or os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="No se ha configurado la pasarela de pagos para este gimnasio")
    currency = (gym or {}).get("stripe_currency") or (gym or {}).get("currency") or "usd"
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    origin_url = request.headers.get("origin", host_url)
    success_url = f"{origin_url}/app/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/app/membership"
    checkout_request = CheckoutSessionRequest(
        amount=float(plan["price"]), currency=currency,
        success_url=success_url, cancel_url=cancel_url,
        metadata={"member_id": member_id, "plan_id": plan_id, "gym_id": plan["gym_id"]}
    )
    session = await stripe_checkout.create_checkout_session(checkout_request)
    transaction = {
        "id": str(uuid.uuid4()), "session_id": session.session_id,
        "member_id": member_id, "plan_id": plan_id, "gym_id": plan["gym_id"],
        "amount": plan["price"], "currency": currency, "status": "pending",
        "payment_status": "initiated", "payment_method": "stripe",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    return {"url": session.url, "session_id": session.session_id}

@router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, credentials = Depends(security)):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    api_key = os.environ.get("STRIPE_API_KEY")
    if transaction:
        gym = await db.gyms.find_one({"id": transaction.get("gym_id")}, {"_id": 0})
        if gym and gym.get("stripe_secret_key"):
            api_key = gym["stripe_secret_key"]
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    status = await stripe_checkout.get_checkout_status(session_id)
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if transaction and status.payment_status == "paid" and transaction["payment_status"] != "paid":
        plan = await db.plans.find_one({"id": transaction["plan_id"]})
        if plan:
            await db.memberships.update_many(
                {"member_id": transaction["member_id"], "status": "active"},
                {"$set": {"status": "expired"}}
            )
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=plan["duration_days"])
            membership = {
                "id": str(uuid.uuid4()), "member_id": transaction["member_id"],
                "plan_id": transaction["plan_id"], "gym_id": transaction["gym_id"],
                "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
                "status": "active", "payment_id": transaction["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.memberships.insert_one(membership)
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": status.status, "payment_status": status.payment_status}}
        )
    return {"status": status.status, "payment_status": status.payment_status,
            "amount_total": status.amount_total, "currency": status.currency}

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    api_key = os.environ.get("STRIPE_API_KEY")
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        logger.info(f"Webhook received: {webhook_response.event_type}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

@router.get("/gyms/{gym_id}/stripe-config")
async def get_stripe_config(gym_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] not in ["super_admin", "gym_admin"] or (admin["role"] == "gym_admin" and admin.get("gym_id") != gym_id):
        raise HTTPException(status_code=403, detail="Access denied")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    has_key = bool(gym.get("stripe_secret_key"))
    masked_key = ""
    if has_key:
        key = gym["stripe_secret_key"]
        masked_key = key[:7] + "..." + key[-4:] if len(key) > 11 else "****"
    return {"has_stripe_key": has_key, "masked_key": masked_key, "currency": gym.get("stripe_currency", gym.get("currency", "usd"))}

@router.put("/gyms/{gym_id}/stripe-config")
async def update_stripe_config(gym_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    if admin["role"] not in ["super_admin", "gym_admin"] or (admin["role"] == "gym_admin" and admin.get("gym_id") != gym_id):
        raise HTTPException(status_code=403, detail="Access denied")
    update_data = {}
    if "stripe_secret_key" in body and body["stripe_secret_key"]:
        update_data["stripe_secret_key"] = body["stripe_secret_key"]
    if "stripe_currency" in body:
        update_data["stripe_currency"] = body["stripe_currency"]
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.gyms.update_one({"id": gym_id}, {"$set": update_data})
    return {"message": "Stripe configuration updated"}

@router.get("/gyms/{gym_id}/has-payments")
async def gym_has_payments(gym_id: str):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        return {"has_payments": False}
    has_key = bool(gym.get("stripe_secret_key")) or bool(os.environ.get("STRIPE_API_KEY")) or bool(gym.get("mercadopago_access_token"))
    return {"has_payments": has_key, "currency": gym.get("currency", gym.get("stripe_currency", "usd"))}

@router.get("/payments/history")
async def get_payment_history(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    for t in transactions:
        member = await db.members.find_one({"id": t.get("member_id")}, {"_id": 0, "name": 1, "code": 1, "email": 1})
        t["member"] = member
        plan = await db.plans.find_one({"id": t.get("plan_id")}, {"_id": 0, "name": 1})
        t["plan"] = plan
    return transactions

@router.post("/payments/manual")
async def create_manual_payment(payment: ManualPayment, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    member = await db.members.find_one({"id": payment.member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    plan = await db.plans.find_one({"id": payment.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    gym_id = member.get("gym_id")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    currency = (gym or {}).get("currency", "eur")
    transaction = {
        "id": str(uuid.uuid4()), "member_id": payment.member_id,
        "member_name": member.get("name"), "plan_id": payment.plan_id,
        "plan_name": plan.get("name"), "gym_id": gym_id,
        "amount": payment.amount, "currency": currency,
        "payment_method": payment.payment_method, "status": "completed",
        "payment_status": "paid", "notes": payment.notes,
        "registered_by": admin["id"], "registered_by_name": admin.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    transaction.pop("_id", None)
    await db.memberships.update_many(
        {"member_id": payment.member_id, "status": "active"},
        {"$set": {"status": "expired"}}
    )
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=plan["duration_days"])
    membership = {
        "id": str(uuid.uuid4()), "member_id": payment.member_id, "plan_id": payment.plan_id,
        "gym_id": gym_id, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
        "status": "active", "payment_id": transaction["id"], "payment_method": payment.payment_method,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.memberships.insert_one(membership)
    membership.pop("_id", None)
    await db.members.update_one(
        {"id": payment.member_id, "status": "suspended"},
        {"$set": {"status": "active", "suspension_reason": None, "suspended_at": None}}
    )
    return {"transaction": transaction, "membership": membership, "message": "Pago registrado y membresia activada"}
