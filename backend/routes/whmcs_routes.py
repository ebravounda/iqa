from fastapi import APIRouter, HTTPException, Header
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid
import secrets
import logging
import os

from database import db
from auth import hash_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

WHMCS_API_KEY = os.environ.get("WHMCS_API_KEY", "")

def verify_whmcs_key(x_whmcs_key: str = Header(...)):
    if not WHMCS_API_KEY or x_whmcs_key != WHMCS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid WHMCS API key")
    return True


class WhmcsProvision(BaseModel):
    gym_name: str
    admin_email: EmailStr
    admin_password: str
    admin_name: Optional[str] = None
    business_type: str = "gym"
    max_members: Optional[int] = None
    plan_name: Optional[str] = None
    whmcs_service_id: Optional[str] = None


class WhmcsAction(BaseModel):
    gym_id: Optional[str] = None
    admin_email: Optional[str] = None
    whmcs_service_id: Optional[str] = None


async def find_gym(data: WhmcsAction):
    """Find gym by gym_id, admin_email, or whmcs_service_id"""
    if data.gym_id:
        gym = await db.gyms.find_one({"id": data.gym_id}, {"_id": 0})
        if gym:
            return gym
    if data.whmcs_service_id:
        gym = await db.gyms.find_one({"whmcs_service_id": data.whmcs_service_id}, {"_id": 0})
        if gym:
            return gym
    if data.admin_email:
        admin = await db.admins.find_one({"email": data.admin_email}, {"_id": 0})
        if admin and admin.get("gym_id"):
            gym = await db.gyms.find_one({"id": admin["gym_id"]}, {"_id": 0})
            if gym:
                return gym
    return None


@router.post("/whmcs/diagnostico")
async def whmcs_diagnostico(x_whmcs_key: str = Header(None)):
    """Endpoint de diagnostico para verificar conexion y API key desde WHMCS"""
    key_valid = False
    if WHMCS_API_KEY and x_whmcs_key == WHMCS_API_KEY:
        key_valid = True
    elif not WHMCS_API_KEY:
        logger.warning("WHMCS_API_KEY no configurada en .env")

    if not key_valid:
        raise HTTPException(status_code=403, detail="API Key invalida")

    total_gyms = await db.gyms.count_documents({})
    total_admins = await db.admins.count_documents({})

    return {
        "success": True,
        "message": "Conexion OK - API Key valida",
        "api_key_valid": True,
        "stats": {
            "total_gyms": total_gyms,
            "total_admins": total_admins,
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/whmcs/provision")
async def whmcs_provision(data: WhmcsProvision, x_whmcs_key: str = Header(None)):
    logger.info(f"WHMCS Provision request: gym_name={data.gym_name}, email={data.admin_email}, service_id={data.whmcs_service_id}")

    # Verificar API key
    if not WHMCS_API_KEY or x_whmcs_key != WHMCS_API_KEY:
        logger.error(f"WHMCS Provision: API key invalida. Recibida: {(x_whmcs_key or '')[:8]}... Esperada: {WHMCS_API_KEY[:8]}...")
        raise HTTPException(status_code=403, detail="Invalid WHMCS API key")

    try:
        existing_admin = await db.admins.find_one({"email": data.admin_email})
        if existing_admin:
            logger.warning(f"WHMCS Provision: Email ya existe: {data.admin_email}")
            raise HTTPException(status_code=400, detail=f"Admin email {data.admin_email} already exists")

        gym_id = str(uuid.uuid4())
        gym_dict = {
            "id": gym_id,
            "name": data.gym_name,
            "business_type": data.business_type,
            "max_members": data.max_members,
            "primary_color": "#E1FF01",
            "qr_refresh_seconds": 10,
            "status": "active",
            "api_token": secrets.token_urlsafe(32),
            "whmcs_service_id": data.whmcs_service_id,
            "whmcs_plan": data.plan_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "email_templates": [
                {"type": "welcome", "subject": "Bienvenido a {gym_name}", "body": "Hola {member_name},\n\nBienvenido a {gym_name}. Tu codigo de socio es: {member_code}\n\nSaludos!"},
                {"type": "expiring_10", "subject": "Tu membresia vence en 10 dias", "body": "Hola {member_name},\n\nTu membresia en {gym_name} vence el {expiry_date}.\n\nRenuevala ahora!"},
                {"type": "expiring_5", "subject": "Tu membresia vence en 5 dias", "body": "Hola {member_name},\n\nTu membresia en {gym_name} vence el {expiry_date}.\n\nRenuevala ahora!"},
                {"type": "expiring_3", "subject": "Tu membresia vence en 3 dias", "body": "Hola {member_name},\n\nTu membresia en {gym_name} vence el {expiry_date}.\n\nRenuevala ahora!"},
                {"type": "expired", "subject": "Tu membresia ha vencido", "body": "Hola {member_name},\n\nTu membresia en {gym_name} ha vencido.\n\nRenuevala para seguir disfrutando!"},
                {"type": "payment_success", "subject": "Pago exitoso", "body": "Hola {member_name},\n\nTu pago de {amount} ha sido procesado exitosamente.\n\nGracias!"},
            ]
        }

        admin_dict = {
            "id": str(uuid.uuid4()),
            "email": data.admin_email,
            "password": hash_password(data.admin_password),
            "name": data.admin_name or f"Admin {data.gym_name}",
            "role": "gym_admin",
            "gym_id": gym_id,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.gyms.insert_one(gym_dict)
        gym_dict.pop("_id", None)
        await db.admins.insert_one(admin_dict)

        logger.info(f"WHMCS Provision OK: Gym '{data.gym_name}' (ID: {gym_id}), Admin: {data.admin_email}")

        return {
            "success": True,
            "gym_id": gym_id,
            "admin_email": data.admin_email,
            "message": f"Gym '{data.gym_name}' created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WHMCS Provision ERROR: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/whmcs/suspend")
async def whmcs_suspend(data: WhmcsAction, x_whmcs_key: str = Header(None)):
    if not WHMCS_API_KEY or x_whmcs_key != WHMCS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid WHMCS API key")

    gym = await find_gym(data)
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")

    await db.gyms.update_one(
        {"id": gym["id"]},
        {"$set": {"status": "suspended", "suspended_at": datetime.now(timezone.utc).isoformat(), "suspended_by": "whmcs"}}
    )

    logger.info(f"WHMCS Suspend: Gym '{gym['name']}' (ID: {gym['id']})")

    return {"success": True, "gym_id": gym["id"], "message": f"Gym '{gym['name']}' suspended"}


@router.post("/whmcs/unsuspend")
async def whmcs_unsuspend(data: WhmcsAction, x_whmcs_key: str = Header(None)):
    if not WHMCS_API_KEY or x_whmcs_key != WHMCS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid WHMCS API key")

    gym = await find_gym(data)
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")

    await db.gyms.update_one(
        {"id": gym["id"]},
        {"$set": {"status": "active"}, "$unset": {"suspended_at": "", "suspended_by": ""}}
    )

    logger.info(f"WHMCS Unsuspend: Gym '{gym['name']}' (ID: {gym['id']})")

    return {"success": True, "gym_id": gym["id"], "message": f"Gym '{gym['name']}' reactivated"}


@router.post("/whmcs/terminate")
async def whmcs_terminate(data: WhmcsAction, x_whmcs_key: str = Header(None)):
    if not WHMCS_API_KEY or x_whmcs_key != WHMCS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid WHMCS API key")

    gym = await find_gym(data)
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")

    await db.gyms.update_one(
        {"id": gym["id"]},
        {"$set": {"status": "terminated", "terminated_at": datetime.now(timezone.utc).isoformat()}}
    )

    logger.info(f"WHMCS Terminate: Gym '{gym['name']}' (ID: {gym['id']})")

    return {"success": True, "gym_id": gym["id"], "message": f"Gym '{gym['name']}' terminated"}


@router.post("/whmcs/info")
async def whmcs_info(data: WhmcsAction, x_whmcs_key: str = Header(None)):
    if not WHMCS_API_KEY or x_whmcs_key != WHMCS_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid WHMCS API key")

    gym = await find_gym(data)
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")

    active_members = await db.members.count_documents({"gym_id": gym["id"], "status": "active"})
    total_members = await db.members.count_documents({"gym_id": gym["id"]})

    return {
        "success": True,
        "gym_id": gym["id"],
        "name": gym.get("name"),
        "status": gym.get("status", "active"),
        "business_type": gym.get("business_type", "gym"),
        "max_members": gym.get("max_members"),
        "active_members": active_members,
        "total_members": total_members,
        "created_at": gym.get("created_at")
    }
