from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
import uuid

from database import db
from auth import (
    security, hash_password, verify_password, create_jwt_token, 
    decode_jwt_token, get_current_admin
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
    await record_successful_login(ip, login.email, "admin")
    token = create_jwt_token({"sub": admin["id"], "role": admin["role"], "gym_id": admin.get("gym_id")})
    admin_data = {k: v for k, v in admin.items() if k not in ["_id", "password"]}
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
    
    # Device registration
    if device_fingerprint:
        from routes.device_member_routes import register_member_device
        user_agent = request.headers.get("user-agent", "")
        success, error_msg = await register_member_device(member["id"], member["gym_id"], device_fingerprint, user_agent)
        if not success:
            raise HTTPException(status_code=403, detail=error_msg)
    
    gym = await db.gyms.find_one({"id": member["gym_id"]}, {"_id": 0})
    membership = await db.memberships.find_one(
        {"member_id": member["id"], "status": "active"}, {"_id": 0}
    )
    await record_successful_login(ip, code.upper(), "member")
    token = create_jwt_token({"sub": member["id"], "role": "member", "gym_id": member["gym_id"]})
    return {"member": member, "gym": gym, "membership": membership, "token": token}

@router.get("/auth/member/me")
async def get_member_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if payload.get("role") != "member":
        raise HTTPException(status_code=403, detail="Not a member")
    member = await db.members.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    gym = await db.gyms.find_one({"id": member["gym_id"]}, {"_id": 0})
    membership = await db.memberships.find_one(
        {"member_id": member["id"], "status": "active"}, {"_id": 0}
    )
    plan = None
    if membership:
        plan = await db.plans.find_one({"id": membership["plan_id"]}, {"_id": 0})
    return {"member": member, "gym": gym, "membership": membership, "plan": plan}
