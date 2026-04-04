from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
import uuid

from database import db
from auth import (
    security, hash_password, verify_password, create_jwt_token, 
    decode_jwt_token, get_current_admin, check_role
)
from models import AdminCreate, AdminLogin
from routes.security_routes import is_ip_blocked, record_failed_attempt, record_successful_login, get_client_ip

router = APIRouter(prefix="/api")

@router.post("/auth/admin/register")
async def register_admin(admin: AdminCreate):
    existing = await db.admins.find_one({"email": admin.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    admin_dict = admin.model_dump()
    admin_dict["id"] = str(uuid.uuid4())
    admin_dict["password"] = hash_password(admin.password)
    admin_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.admins.insert_one(admin_dict)
    admin_dict.pop("password", None)
    admin_dict.pop("_id", None)
    token = create_jwt_token({"sub": admin_dict["id"], "role": admin_dict["role"], "gym_id": admin_dict.get("gym_id")})
    return {"admin": admin_dict, "token": token}

@router.post("/auth/admin/login")
async def login_admin(login: AdminLogin, request: Request):
    ip = await get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    if await is_ip_blocked(ip):
        raise HTTPException(status_code=429, detail="IP bloqueada temporalmente por multiples intentos fallidos. Intenta en 15 minutos.")
    admin = await db.admins.find_one({"email": login.email})
    if not admin or not verify_password(login.password, admin["password"]):
        blocked = await record_failed_attempt(ip, login.email, "admin", user_agent)
        detail = "Credenciales invalidas"
        if blocked:
            detail = "IP bloqueada por multiples intentos fallidos. Intenta en 15 minutos."
        raise HTTPException(status_code=401, detail=detail)
    if admin.get("active") is False:
        raise HTTPException(status_code=403, detail="Cuenta desactivada. Contacta al administrador.")
    # Check gym payment suspension
    gym_status = None
    if admin.get("gym_id"):
        gym = await db.gyms.find_one({"id": admin["gym_id"]}, {"_id": 0})
        if gym:
            gym_status = gym.get("status")
    await record_successful_login(ip, login.email, "admin")
    token = create_jwt_token({"sub": admin["id"], "role": admin["role"], "gym_id": admin.get("gym_id")})
    admin_data = {k: v for k, v in admin.items() if k not in ["_id", "password"]}
    admin_data["gym_status"] = gym_status
    return {"admin": admin_data, "token": token}

@router.post("/auth/admin/impersonate/{gym_id}")
async def impersonate_gym(gym_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if payload.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Solo el super admin puede usar esta funcion")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    original_admin = await db.admins.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not original_admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    impersonation_token = create_jwt_token({
        "sub": payload.get("sub"),
        "role": "gym_admin",
        "gym_id": gym_id,
        "impersonating": True,
        "original_role": "super_admin"
    })
    admin_data = {k: v for k, v in original_admin.items() if k not in ["_id", "password"]}
    admin_data["role"] = "gym_admin"
    admin_data["gym_id"] = gym_id
    admin_data["impersonating"] = True
    admin_data["original_role"] = "super_admin"
    admin_data["gym_name"] = gym.get("name", "")
    return {"admin": admin_data, "token": impersonation_token, "gym": gym}

@router.post("/auth/member/login")
async def login_member(code: str, request: Request, device_fingerprint: str = None):
    ip = await get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    if await is_ip_blocked(ip):
        raise HTTPException(status_code=429, detail="IP bloqueada temporalmente. Intenta en 15 minutos.")
    member = await db.members.find_one({"code": code.upper()}, {"_id": 0})
    if not member:
        await record_failed_attempt(ip, code.upper(), "member", user_agent)
        raise HTTPException(status_code=404, detail="Codigo no encontrado")
    if member.get("status") == "blocked":
        raise HTTPException(status_code=403, detail="Cuenta bloqueada")
    if member.get("status") == "suspended":
        # Determine suspension type: explicit field > fallback to reason text for legacy records
        s_type = member.get("suspension_type")
        if s_type == "manual":
            raise HTTPException(status_code=403, detail="Cuenta suspendida. Contacta al administrador.")
        elif s_type == "payment":
            pass  # Allow login, frontend will show payment banner
        else:
            # Legacy records without suspension_type: check reason
            if "vencida" in (member.get("suspension_reason") or "").lower():
                pass  # Treat as payment suspension
            else:
                raise HTTPException(status_code=403, detail="Cuenta suspendida. Contacta al administrador.")
    
    # Check gym payment suspension BEFORE device check
    gym = await db.gyms.find_one({"id": member["gym_id"]}, {"_id": 0})
    if gym and gym.get("status") in ("payment_suspended", "suspended"):
        raise HTTPException(status_code=403, detail="Cuenta Bloqueada")
    
    # Device registration
    if device_fingerprint:
        from routes.device_member_routes import register_member_device
        user_agent = request.headers.get("user-agent", "")
        success, error_msg = await register_member_device(member["id"], member["gym_id"], device_fingerprint, user_agent)
        if not success:
            raise HTTPException(status_code=403, detail=error_msg)
    
    membership = await db.memberships.find_one(
        {"member_id": member["id"], "status": "active"}, {"_id": 0}
    )
    await record_successful_login(ip, code.upper(), "member")
    # Convert avatar_path to avatar_url if needed
    if member.get("avatar_path") and not member.get("avatar_url"):
        member["avatar_url"] = f"/api/files/{member['avatar_path']}"
    token = create_jwt_token({"sub": member["id"], "role": "member", "gym_id": member["gym_id"]})
    if gym:
        gym.setdefault("business_type", "gym")
    return {"member": member, "gym": gym, "membership": membership, "token": token}

@router.get("/auth/member/me")
async def get_member_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if payload.get("role") != "member":
        raise HTTPException(status_code=403, detail="Not a member")
    member = await db.members.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.get("status") == "suspended":
        s_type = member.get("suspension_type")
        if s_type == "manual":
            raise HTTPException(status_code=403, detail="Cuenta suspendida")
        elif s_type == "payment":
            pass
        else:
            if "vencida" not in (member.get("suspension_reason") or "").lower():
                raise HTTPException(status_code=403, detail="Cuenta suspendida")
    if member.get("status") == "blocked":
        raise HTTPException(status_code=403, detail="Cuenta bloqueada")
    # Convert avatar_path to avatar_url if needed
    if member.get("avatar_path") and not member.get("avatar_url"):
        member["avatar_url"] = f"/api/files/{member['avatar_path']}"
    gym = await db.gyms.find_one({"id": member["gym_id"]}, {"_id": 0})
    if gym and gym.get("status") in ("payment_suspended", "suspended"):
        raise HTTPException(status_code=403, detail="Cuenta Bloqueada")
    membership = await db.memberships.find_one(
        {"member_id": member["id"], "status": "active"}, {"_id": 0}
    )
    plan = None
    if membership:
        plan = await db.plans.find_one({"id": membership["plan_id"]}, {"_id": 0})
    if gym:
        gym.setdefault("business_type", "gym")
    return {"member": member, "gym": gym, "membership": membership, "plan": plan}


@router.put("/auth/admin/update-profile")
async def update_admin_profile(request: Request, admin: dict = Depends(get_current_admin)):
    body = await request.json()
    new_email = body.get("email", "").strip()
    new_password = body.get("password", "").strip()
    current_password = body.get("current_password", "").strip()
    if not current_password:
        raise HTTPException(status_code=400, detail="Debes ingresar tu contraseña actual")
    stored = await db.admins.find_one({"id": admin["id"]})
    if not stored or not verify_password(current_password, stored["password"]):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    updates = {}
    if new_email and new_email != stored.get("email"):
        existing = await db.admins.find_one({"email": new_email, "id": {"$ne": admin["id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="Ese email ya esta en uso por otro administrador")
        updates["email"] = new_email
    if new_password:
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
        updates["password"] = hash_password(new_password)
    if not updates:
        raise HTTPException(status_code=400, detail="No hay cambios para guardar")
    await db.admins.update_one({"id": admin["id"]}, {"$set": updates})
    updated = await db.admins.find_one({"id": admin["id"]}, {"_id": 0, "password": 0})
    new_token = create_jwt_token({"sub": updated["id"], "role": updated["role"], "gym_id": updated.get("gym_id")})
    return {"message": "Perfil actualizado correctamente", "admin": updated, "token": new_token}


@router.put("/auth/admin/{admin_id}/credentials")
async def update_admin_credentials(admin_id: str, request: Request, admin: dict = Depends(get_current_admin)):
    """Super admin can change email/password of any gym admin"""
    check_role(admin, ["super_admin"])
    body = await request.json()
    new_email = body.get("email", "").strip()
    new_password = body.get("password", "").strip()
    target = await db.admins.find_one({"id": admin_id})
    if not target:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    updates = {}
    if new_email and new_email != target.get("email"):
        existing = await db.admins.find_one({"email": new_email, "id": {"$ne": admin_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Ese email ya esta en uso")
        updates["email"] = new_email
    if new_password:
        if len(new_password) < 6:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
        updates["password"] = hash_password(new_password)
    if not updates:
        raise HTTPException(status_code=400, detail="No hay cambios")
    await db.admins.update_one({"id": admin_id}, {"$set": updates})
    updated = await db.admins.find_one({"id": admin_id}, {"_id": 0, "password": 0})
    # Also update gym record if email changed
    if "email" in updates and target.get("gym_id"):
        await db.gyms.update_one({"id": target["gym_id"]}, {"$set": {"gym_admin_email": updates["email"]}})
    return {"message": "Credenciales actualizadas", "admin": updated}
