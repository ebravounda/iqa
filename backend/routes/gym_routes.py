from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import secrets
import logging

from database import db
from auth import get_current_admin, hash_password, check_role
from models import GymCreate, GymUpdate, EmailTemplateUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.post("/gyms")
async def create_gym(gym: GymCreate, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can create gyms")
    gym_dict = gym.model_dump()
    gym_dict["id"] = str(uuid.uuid4())
    gym_dict["api_token"] = secrets.token_urlsafe(32)
    gym_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    default_templates = [
        {"type": "welcome", "subject": "Bienvenido a {gym_name}", "body": "Hola {member_name},\n\nBienvenido a {gym_name}. Tu codigo de socio es: {member_code}\n\nSaludos!"},
        {"type": "expiring_10", "subject": "Tu membresia vence en 10 dias", "body": "Hola {member_name},\n\nTu membresia en {gym_name} vence el {expiry_date}.\n\nRenuevala ahora!"},
        {"type": "expiring_5", "subject": "Tu membresia vence en 5 dias", "body": "Hola {member_name},\n\nTu membresia en {gym_name} vence el {expiry_date}.\n\nRenuevala ahora!"},
        {"type": "expiring_3", "subject": "Tu membresia vence en 3 dias", "body": "Hola {member_name},\n\nTu membresia en {gym_name} vence el {expiry_date}.\n\nRenuevala ahora!"},
        {"type": "expired", "subject": "Tu membresia ha vencido", "body": "Hola {member_name},\n\nTu membresia en {gym_name} ha vencido.\n\nRenuevala para seguir disfrutando!"},
        {"type": "payment_success", "subject": "Pago exitoso", "body": "Hola {member_name},\n\nTu pago de {amount} ha sido procesado exitosamente.\n\nGracias!"},
    ]
    gym_dict["email_templates"] = default_templates
    await db.gyms.insert_one(gym_dict)
    gym_dict.pop("_id", None)
    admin_email = gym.admin_email
    admin_password = gym.admin_password
    admin_name = gym.admin_name or f"Admin {gym.name}"
    if admin_email and admin_password:
        existing_admin = await db.admins.find_one({"email": admin_email})
        if existing_admin:
            raise HTTPException(status_code=400, detail=f"Ya existe un administrador con el email {admin_email}")
        gym_admin = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password": hash_password(admin_password),
            "name": admin_name,
            "role": "gym_admin",
            "gym_id": gym_dict["id"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(gym_admin)
        gym_dict["admin_created"] = True
        gym_dict["admin_email"] = admin_email
        logger.info(f"Gym admin created for {gym.name}: {admin_email}")
    for key in ["admin_email", "admin_password", "admin_name"]:
        gym_dict.pop(key, None)
    return gym_dict

@router.get("/gyms")
async def get_gyms(admin: dict = Depends(get_current_admin)):
    if admin["role"] == "super_admin":
        gyms = await db.gyms.find({}, {"_id": 0}).to_list(100)
        for gym in gyms:
            gym.setdefault("business_type", "gym")
            gym_admin = await db.admins.find_one(
                {"gym_id": gym["id"], "role": "gym_admin"}, 
                {"_id": 0, "email": 1, "name": 1, "id": 1}
            )
            gym["gym_admin_email"] = gym_admin["email"] if gym_admin else None
            gym["gym_admin_name"] = gym_admin["name"] if gym_admin else None
            gym["admin_id"] = gym_admin["id"] if gym_admin else None
    else:
        gyms = await db.gyms.find({"id": admin.get("gym_id")}, {"_id": 0}).to_list(1)
        for gym in gyms:
            gym.setdefault("business_type", "gym")
    return gyms

@router.get("/gyms/{gym_id}")
async def get_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    gym.setdefault("business_type", "gym")
    return gym

@router.put("/gyms/{gym_id}")
async def update_gym(gym_id: str, gym_update: GymUpdate, admin: dict = Depends(get_current_admin)):
    update_data = {}
    for k, v in gym_update.model_dump().items():
        if v is not None:
            update_data[k] = v
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.gyms.update_one({"id": gym_id}, {"$set": update_data})
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    return gym

@router.put("/gyms/{gym_id}/templates/{template_type}")
async def update_email_template(gym_id: str, template_type: str, template: EmailTemplateUpdate, admin: dict = Depends(get_current_admin)):
    await db.gyms.update_one(
        {"id": gym_id, "email_templates.type": template_type},
        {"$set": {"email_templates.$.subject": template.subject, "email_templates.$.body": template.body}}
    )
    return {"message": "Template updated"}

@router.post("/gyms/{gym_id}/regenerate-token")
async def regenerate_gym_token(gym_id: str, admin: dict = Depends(get_current_admin)):
    new_token = secrets.token_urlsafe(32)
    await db.gyms.update_one({"id": gym_id}, {"$set": {"api_token": new_token}})
    return {"api_token": new_token}

@router.put("/gyms/{gym_id}/suspend")
async def suspend_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can suspend gyms")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    new_status = "active" if gym.get("status") in ("suspended", "payment_suspended") else "suspended"
    await db.gyms.update_one({"id": gym_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": f"Gym {'reactivated' if new_status == 'active' else 'suspended'}", "status": new_status}

@router.put("/gyms/{gym_id}/payment-suspend")
async def payment_suspend_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can suspend gyms")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    new_status = "active" if gym.get("status") == "payment_suspended" else "payment_suspended"
    await db.gyms.update_one({"id": gym_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    label = "reactivado" if new_status == "active" else "suspendido por falta de pago"
    return {"message": f"Gimnasio {label}", "status": new_status}

@router.delete("/gyms/{gym_id}")
async def delete_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can delete gyms")
    gym = await db.gyms.find_one({"id": gym_id})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    await db.gyms.delete_one({"id": gym_id})
    for col in ["members", "memberships", "classes", "class_schedules", "bookings", "notifications", "guests", "access_logs", "devices"]:
        await db[col].delete_many({"gym_id": gym_id})
    await db.admins.delete_many({"gym_id": gym_id})
    return {"message": "Gym and all related data deleted"}

@router.get("/gyms/{gym_id}/capacity")
async def get_gym_capacity(gym_id: str, admin: dict = Depends(get_current_admin)):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    active_count = await db.members.count_documents({"gym_id": gym_id, "status": "active"})
    total_count = await db.members.count_documents({"gym_id": gym_id})
    max_members = gym.get("max_members", 0)
    return {
        "gym_id": gym_id,
        "active_members": active_count,
        "total_members": total_count,
        "max_members": max_members,
        "usage_percent": round((active_count / max_members * 100), 1) if max_members > 0 else 0
    }

@router.get("/gyms/{gym_id}/public-info")
async def get_gym_public_info(gym_id: str):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if gym.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Este gimnasio esta suspendido")
    has_stripe = bool(gym.get("stripe_secret_key"))
    has_mercadopago = bool(gym.get("mercadopago_access_token"))
    return {
        "id": gym["id"],
        "name": gym.get("name", ""),
        "logo_url": gym.get("logo_url"),
        "primary_color": gym.get("primary_color", "#E1FF01"),
        "address": gym.get("address"),
        "phone": gym.get("phone"),
        "email": gym.get("email"),
        "business_type": gym.get("business_type", "gym"),
        "has_payments": has_stripe or has_mercadopago,
        "has_stripe": has_stripe,
        "has_mercadopago": has_mercadopago,
        "currency": gym.get("currency", gym.get("stripe_currency", "eur"))
    }



@router.get("/gyms/resolve-domain/{domain}")
async def resolve_gym_domain(domain: str):
    """Public endpoint - resolve a custom domain to a gym's public info"""
    domain = domain.lower().strip()
    gym = await db.gyms.find_one({"custom_domain": domain, "status": {"$ne": "suspended"}}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Dominio no configurado")
    return {
        "id": gym["id"],
        "name": gym.get("name", ""),
        "logo_url": gym.get("logo_url"),
        "primary_color": gym.get("primary_color", "#E1FF01"),
        "secondary_color": gym.get("secondary_color"),
        "bg_color": gym.get("bg_color"),
        "menu_color": gym.get("menu_color"),
        "text_color": gym.get("text_color"),
        "business_type": gym.get("business_type", "gym"),
        "custom_domain": gym.get("custom_domain"),
    }
