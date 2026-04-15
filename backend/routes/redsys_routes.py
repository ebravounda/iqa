"""
Redsys TPV Virtual - Payment routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging
import os

from database import db
from auth import get_current_admin, check_role
from redsys_utils import (
    generate_order_number, create_redsys_form_data, verify_redsys_response,
    get_response_message,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ── Admin: Configure Redsys per gym ──

@router.get("/gyms/{gym_id}/redsys-config")
async def get_redsys_config(gym_id: str, admin: dict = Depends(get_current_admin)):
    """Get Redsys configuration status for a gym"""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")

    has_redsys = bool(gym.get("redsys_merchant_code") and gym.get("redsys_secret_key"))
    masked_code = ""
    if gym.get("redsys_merchant_code"):
        code = gym["redsys_merchant_code"]
        masked_code = code[:3] + "****" + code[-2:] if len(code) > 5 else "****"

    return {
        "enabled": gym.get("redsys_enabled", False),
        "has_credentials": has_redsys,
        "masked_merchant_code": masked_code,
        "terminal": gym.get("redsys_terminal", ""),
        "environment": gym.get("redsys_environment", "sandbox"),
    }


@router.put("/gyms/{gym_id}/redsys-config")
async def update_redsys_config(gym_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    """Update Redsys configuration for a gym. Only super_admin (including impersonation)."""
    if admin["role"] != "super_admin" and admin.get("original_role") != "super_admin":
        raise HTTPException(status_code=403, detail="Solo el super admin puede configurar Redsys")

    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")

    update_data = {}

    if "redsys_enabled" in body:
        update_data["redsys_enabled"] = bool(body["redsys_enabled"])

    if "redsys_merchant_code" in body and body["redsys_merchant_code"]:
        update_data["redsys_merchant_code"] = body["redsys_merchant_code"].strip()

    if "redsys_terminal" in body and body["redsys_terminal"]:
        update_data["redsys_terminal"] = body["redsys_terminal"].strip()

    if "redsys_secret_key" in body and body["redsys_secret_key"]:
        update_data["redsys_secret_key"] = body["redsys_secret_key"].strip()

    if "redsys_environment" in body and body["redsys_environment"] in ("sandbox", "production"):
        update_data["redsys_environment"] = body["redsys_environment"]

    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.gyms.update_one({"id": gym_id}, {"$set": update_data})

    return {"success": True, "message": "Configuracion de Redsys actualizada"}


# ── Member: Initiate Redsys payment ──

@router.post("/redsys/initiate")
async def initiate_redsys_payment(body: dict, request: Request):
    """
    Create a Redsys payment form for a member to pay for a plan.
    Body: { member_id, plan_id, gym_id }
    Returns JSON with form_url and form fields for frontend to redirect.
    """
    member_id = body.get("member_id")
    plan_id = body.get("plan_id")
    gym_id = body.get("gym_id")

    if not member_id or not plan_id or not gym_id:
        raise HTTPException(status_code=400, detail="member_id, plan_id y gym_id requeridos")

    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    plan = await db.plans.find_one({"id": plan_id, "gym_id": gym_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")

    if not gym.get("redsys_enabled"):
        raise HTTPException(status_code=400, detail="Redsys no esta habilitado para este gimnasio")

    merchant_code = gym.get("redsys_merchant_code")
    terminal = gym.get("redsys_terminal", "001")
    secret_key = gym.get("redsys_secret_key")

    if not merchant_code or not secret_key:
        raise HTTPException(status_code=400, detail="Credenciales de Redsys no configuradas")

    is_sandbox = gym.get("redsys_environment", "sandbox") == "sandbox"

    # Amount
    price = float(plan.get("price", 0))
    if price <= 0:
        raise HTTPException(status_code=400, detail="El plan no tiene un precio valido")

    order_number = generate_order_number()

    # Build URLs
    base_url = gym.get("app_url", "https://app.ingresoqr.com")
    backend_url = gym.get("backend_url", "https://c.ingresoqr.com")

    notification_url = f"{backend_url}/api/redsys/notification"
    url_ok = f"{base_url}/app/membership?redsys_result=ok&order={order_number}"
    url_ko = f"{base_url}/app/membership?redsys_result=ko&order={order_number}"

    logger.info(f"Redsys initiate: order={order_number} plan={plan.get('name')} price={price} merchant={merchant_code} terminal={terminal} env={'sandbox' if is_sandbox else 'production'}")

    form_data = create_redsys_form_data(
        secret_key=secret_key,
        merchant_code=merchant_code,
        terminal=terminal,
        order_number=order_number,
        amount=price,
        sandbox=is_sandbox,
        merchant_name=gym.get("name", ""),
        product_description=f"{plan.get('name', 'Plan')} - {gym.get('name', '')}",
        titular=member.get("name", ""),
        notification_url=notification_url,
        url_ok=url_ok,
        url_ko=url_ko,
    )

    # Save pending payment
    payment = {
        "id": str(uuid.uuid4()),
        "order_number": order_number,
        "member_id": member_id,
        "member_name": member.get("name"),
        "plan_id": plan_id,
        "plan_name": plan.get("name"),
        "gym_id": gym_id,
        "amount": price,
        "amount_cents": int(round(price * 100)),
        "currency": "eur",
        "payment_method": "redsys",
        "status": "pending",
        "payment_status": "pending",
        "redsys_environment": "sandbox" if is_sandbox else "production",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payment_transactions.insert_one(payment)
    payment.pop("_id", None)

    form_data["order_number"] = order_number
    return form_data


# ── Notification callback (server-to-server from Redsys) ──

@router.post("/redsys/notification")
async def redsys_notification(request: Request):
    """
    Server-to-server notification from Redsys after payment completion.
    Verifies signature, updates payment and activates membership.
    """
    try:
        form = await request.form()
        ds_params = form.get("Ds_MerchantParameters", "")
        ds_signature = form.get("Ds_Signature", "")
        ds_version = form.get("Ds_SignatureVersion", "HMAC_SHA256_V1")

        if not ds_params or not ds_signature:
            logger.warning("Redsys notification: missing parameters")
            return JSONResponse(content={"status": "error"}, status_code=400)

        # Decode params to get order number first
        import base64, json
        params = json.loads(base64.b64decode(ds_params).decode('utf-8'))
        order_number = params.get("Ds_Order", "")
        response_code = params.get("Ds_Response", "9999")
        amount = params.get("Ds_Amount", "0")

        logger.info(f"Redsys notification: order={order_number} response={response_code} amount={amount}")

        # Find payment
        payment = await db.payment_transactions.find_one({"order_number": order_number})
        if not payment:
            logger.warning(f"Redsys notification: payment not found for order {order_number}")
            return JSONResponse(content={"status": "not_found"}, status_code=404)

        # Get gym credentials to verify signature
        gym = await db.gyms.find_one({"id": payment["gym_id"]}, {"_id": 0})
        if not gym or not gym.get("redsys_secret_key"):
            logger.error(f"Redsys notification: gym credentials not found for {payment['gym_id']}")
            return JSONResponse(content={"status": "error"}, status_code=500)

        # Verify signature using official library
        is_sandbox = gym.get("redsys_environment", "sandbox") == "sandbox"
        try:
            response_data = verify_redsys_response(
                gym["redsys_secret_key"], ds_signature, ds_params, ds_version, is_sandbox
            )
            is_paid = response_data.get("is_paid", False)
        except Exception as sig_err:
            logger.warning(f"Redsys notification: signature verification failed for order {order_number}: {sig_err}")
            # Fallback: check response code directly
            response_int = int(response_code) if response_code.isdigit() else 9999
            is_paid = 0 <= response_int <= 99

        update_data = {
            "redsys_response_code": response_code,
            "redsys_response_message": get_response_message(response_code),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        if is_paid:
            update_data["status"] = "completed"
            update_data["payment_status"] = "paid"
            update_data["paid_at"] = datetime.now(timezone.utc).isoformat()

            # Activate membership
            member_id = payment["member_id"]
            plan_id = payment["plan_id"]
            gym_id = payment["gym_id"]

            plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
            duration_days = plan.get("duration_days", 30) if plan else 30

            now = datetime.now(timezone.utc)
            membership = {
                "id": str(uuid.uuid4()),
                "member_id": member_id,
                "plan_id": plan_id,
                "gym_id": gym_id,
                "start_date": now.isoformat(),
                "end_date": (now + timedelta(days=duration_days)).strftime("%Y-%m-%d"),
                "status": "active",
                "payment_status": "paid",
                "payment_method": "redsys",
                "payment_id": payment["id"],
                "created_at": now.isoformat(),
            }
            await db.memberships.insert_one(membership)
            membership.pop("_id", None)

            # Activate member
            await db.members.update_one(
                {"id": member_id},
                {"$set": {"status": "active"}, "$unset": {"suspension_type": "", "suspension_reason": ""}}
            )

            logger.info(f"Redsys payment OK: order={order_number} member={member_id}")
        else:
            update_data["status"] = "failed"
            update_data["payment_status"] = "failed"
            logger.warning(f"Redsys payment FAILED: order={order_number} code={response_code}")

        await db.payment_transactions.update_one(
            {"order_number": order_number},
            {"$set": update_data}
        )

        return JSONResponse(content={"status": "ok"}, status_code=200)

    except Exception as e:
        logger.error(f"Redsys notification error: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)


# ── Check payment status by order number ──

@router.get("/redsys/status/{order_number}")
async def get_redsys_payment_status(order_number: str):
    """Check payment status by order number (used after redirect from Redsys)"""
    payment = await db.payment_transactions.find_one(
        {"order_number": order_number},
        {"_id": 0, "redsys_secret_key": 0}
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    return {
        "order_number": payment.get("order_number"),
        "status": payment.get("status"),
        "payment_status": payment.get("payment_status"),
        "amount": payment.get("amount"),
        "plan_name": payment.get("plan_name"),
        "redsys_response_message": payment.get("redsys_response_message"),
    }
