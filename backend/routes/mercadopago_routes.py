from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
import uuid
import os
import logging

from database import db
from auth import get_current_admin, security, decode_jwt_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

MP_API_BASE = "https://api.mercadopago.com"

async def get_mp_token(gym_id: str) -> str:
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    token = (gym or {}).get("mercadopago_access_token")
    if not token:
        token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=400, detail="MercadoPago no configurado para este gimnasio")
    return token

@router.post("/mercadopago/create-preference")
async def create_mp_preference(
    request: Request,
    plan_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    gym = await db.gyms.find_one({"id": plan["gym_id"]}, {"_id": 0})
    access_token = await get_mp_token(plan["gym_id"])
    
    origin_url = request.headers.get("origin", str(request.base_url).rstrip('/'))
    external_ref = f"gym_{plan['gym_id']}_member_{member_id}_plan_{plan_id}_{uuid.uuid4().hex[:8]}"
    
    preference_data = {
        "items": [{
            "id": plan_id,
            "title": f"{(gym or {}).get('name', 'Gimnasio')} - {plan['name']}",
            "description": plan.get("description", f"Membresia {plan['name']}"),
            "quantity": 1,
            "currency_id": "CLP",
            "unit_price": int(plan["price"]),
        }],
        "payer": {
            "name": member.get("name", ""),
            "email": member.get("email", ""),
        },
        "back_urls": {
            "success": f"{origin_url}/app/payment-success?provider=mercadopago",
            "pending": f"{origin_url}/app/payment-pending",
            "failure": f"{origin_url}/app/payment-failure",
        },
        "notification_url": f"{str(request.base_url).rstrip('/')}/api/webhook/mercadopago",
        "external_reference": external_ref,
        "auto_return": "approved",
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{MP_API_BASE}/checkout/preferences",
            json=preference_data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": str(uuid.uuid4()),
            }
        )
        if resp.status_code != 201:
            logger.error(f"MercadoPago preference error: {resp.status_code} - {resp.text}")
            raise HTTPException(status_code=500, detail=f"Error al crear preferencia de pago: {resp.text}")
        result = resp.json()
    
    transaction = {
        "id": str(uuid.uuid4()),
        "preference_id": result.get("id"),
        "member_id": member_id,
        "plan_id": plan_id,
        "gym_id": plan["gym_id"],
        "amount": plan["price"],
        "currency": "CLP",
        "status": "pending",
        "payment_status": "initiated",
        "payment_method": "mercadopago",
        "external_reference": external_ref,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {
        "url": result.get("init_point"),
        "preference_id": result.get("id"),
        "sandbox_url": result.get("sandbox_init_point"),
    }

@router.post("/webhook/mercadopago")
async def mp_webhook(request: Request):
    try:
        body = await request.json()
        logger.info(f"MercadoPago webhook: {body}")
        
        action = body.get("action") or body.get("type")
        data = body.get("data", {})
        payment_id = data.get("id") or body.get("data.id")
        
        if not payment_id and action == "payment.created":
            payment_id = data.get("id")
        
        if payment_id:
            # Try to find by external_reference or by mp payment_id
            # Fetch payment details from MP API
            token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN")
            if token:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(
                        f"{MP_API_BASE}/v1/payments/{payment_id}",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if resp.status_code == 200:
                        mp_data = resp.json()
                        ext_ref = mp_data.get("external_reference", "")
                        status = mp_data.get("status")
                        
                        transaction = await db.payment_transactions.find_one(
                            {"external_reference": ext_ref}, {"_id": 0}
                        )
                        if transaction and status == "approved" and transaction.get("payment_status") != "paid":
                            await db.payment_transactions.update_one(
                                {"id": transaction["id"]},
                                {"$set": {
                                    "status": "completed",
                                    "payment_status": "paid",
                                    "mp_payment_id": str(payment_id),
                                    "paid_at": datetime.now(timezone.utc).isoformat()
                                }}
                            )
                            # Activate membership
                            plan = await db.plans.find_one({"id": transaction["plan_id"]})
                            if plan:
                                await db.memberships.update_many(
                                    {"member_id": transaction["member_id"], "status": "active"},
                                    {"$set": {"status": "expired"}}
                                )
                                start_date = datetime.now(timezone.utc)
                                end_date = start_date + timedelta(days=plan["duration_days"])
                                membership = {
                                    "id": str(uuid.uuid4()),
                                    "member_id": transaction["member_id"],
                                    "plan_id": transaction["plan_id"],
                                    "gym_id": transaction["gym_id"],
                                    "start_date": start_date.isoformat(),
                                    "end_date": end_date.isoformat(),
                                    "status": "active",
                                    "payment_id": transaction["id"],
                                    "payment_method": "mercadopago",
                                    "created_at": datetime.now(timezone.utc).isoformat()
                                }
                                await db.memberships.insert_one(membership)
                                await db.members.update_one(
                                    {"id": transaction["member_id"], "status": "suspended"},
                                    {"$set": {"status": "active", "suspension_reason": None}}
                                )
                            logger.info(f"MercadoPago payment approved: {ext_ref}")
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"MercadoPago webhook error: {e}")
        return {"status": "error"}

@router.get("/mercadopago/payment-status")
async def get_mp_payment_status(
    external_reference: Optional[str] = None,
    preference_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    query = {"payment_method": "mercadopago"}
    if external_reference:
        query["external_reference"] = external_reference
    elif preference_id:
        query["preference_id"] = preference_id
    else:
        raise HTTPException(status_code=400, detail="Se requiere external_reference o preference_id")
    
    transaction = await db.payment_transactions.find_one(query, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaccion no encontrada")
    return transaction

@router.get("/gyms/{gym_id}/mercadopago-config")
async def get_mp_config(gym_id: str, admin: dict = Depends(get_current_admin)):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    has_token = bool(gym.get("mercadopago_access_token"))
    masked = ""
    if has_token:
        t = gym["mercadopago_access_token"]
        masked = t[:12] + "..." + t[-4:] if len(t) > 16 else "****"
    return {"has_mercadopago": has_token, "masked_token": masked}

@router.put("/gyms/{gym_id}/mercadopago-config")
async def update_mp_config(gym_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    update_data = {}
    if "mercadopago_access_token" in body and body["mercadopago_access_token"]:
        update_data["mercadopago_access_token"] = body["mercadopago_access_token"]
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.gyms.update_one({"id": gym_id}, {"$set": update_data})
    return {"message": "Configuracion de MercadoPago actualizada"}
