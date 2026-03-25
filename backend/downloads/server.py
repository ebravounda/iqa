from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import base64
import json
import secrets
import bcrypt
from jose import jwt, JWTError

import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret_change_me')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# QR Config
QR_SECRET = os.environ.get('QR_SECRET', 'qr_secret_change_me')

app = FastAPI(title="Gym Access Control System")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class GymCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: str = "#E1FF01"
    qr_refresh_seconds: int = 10
    max_members: Optional[int] = None
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = None
    admin_name: Optional[str] = None

class GymUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    qr_refresh_seconds: Optional[int] = None
    qr_mode: Optional[str] = None  # "dynamic" or "static"
    max_members: Optional[int] = None
    stripe_secret_key: Optional[str] = None
    stripe_currency: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "gym_admin"  # super_admin, gym_admin, gym_manager, trainer
    gym_id: Optional[str] = None

# Roles:
# - super_admin: Administra todo el sistema SaaS (todos los gyms)
# - gym_admin: Administrador de un gym específico (todo el control)
# - gym_manager: Gestor de gym (gestiona socios, clases, pero no configuración)
# - trainer: Entrenador (solo ve sus clases y asistentes)

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    gym_id: str

class MemberPublicRegister(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    gym_id: str
    plan_id: Optional[str] = None

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = None  # active, blocked, pending, suspended
    can_bring_guests: Optional[bool] = None
    max_guests_per_month: Optional[int] = None
    suspension_reason: Optional[str] = None

class PlanCreate(BaseModel):
    gym_id: str
    name: str
    description: Optional[str] = None
    price: float
    duration_days: int
    access_type: str = "unlimited"  # unlimited, limited

class MembershipCreate(BaseModel):
    member_id: str
    plan_id: str

class AccessValidation(BaseModel):
    qr_code: str
    gym_token: str
    direction: str  # entrada, salida

class DeviceCreate(BaseModel):
    gym_id: str
    name: str
    location: Optional[str] = None

class EmailTemplateUpdate(BaseModel):
    subject: str
    body: str

class ManualPayment(BaseModel):
    member_id: str
    plan_id: str
    payment_method: str  # "cash", "card_reception"
    amount: float
    notes: Optional[str] = None

# ==================== CLASS/BOOKING MODELS ====================

class ClassCreate(BaseModel):
    gym_id: str
    name: str
    description: Optional[str] = None
    trainer_id: Optional[str] = None
    max_capacity: int = 20
    duration_minutes: int = 60
    class_type: str = "group"  # group, personal
    recurring: bool = False
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    start_time: Optional[str] = None  # HH:MM format for recurring
    single_date: Optional[str] = None  # ISO date for single class
    single_start_time: Optional[str] = None  # HH:MM for single class

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trainer_id: Optional[str] = None
    max_capacity: Optional[int] = None
    duration_minutes: Optional[int] = None
    active: Optional[bool] = None

class ClassScheduleCreate(BaseModel):
    class_id: str
    date: str  # ISO date
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    trainer_id: Optional[str] = None
    max_capacity: Optional[int] = None

class BookingCreate(BaseModel):
    schedule_id: str

class TrainerCreate(BaseModel):
    gym_id: str
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    specialties: Optional[List[str]] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

# ==================== NOTIFICATION MODELS ====================

class NotificationCreate(BaseModel):
    gym_id: str
    title: str
    message: str
    notification_type: str = "general"  # general, class, membership, promotion
    target: str = "all"  # all, active_members, expiring_members

# ==================== GUEST MODELS ====================

class GuestCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    valid_days: int = 1  # Number of days the guest pass is valid

# ==================== UTILITIES ====================

def generate_member_code():
    """Generate unique member code like SD345FG"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(chars) for _ in range(6))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_jwt_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    admin = await db.admins.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    
    # If impersonating, override role and gym_id from token
    if payload.get("impersonating"):
        admin = dict(admin)  # Make a copy to avoid modifying cached data
        admin["role"] = payload.get("role", admin.get("role"))
        admin["gym_id"] = payload.get("gym_id")
        admin["impersonating"] = True
        admin["original_role"] = payload.get("original_role")
    
    return admin

def generate_qr_data(member_id: str, gym_id: str, timestamp: int) -> str:
    """Generate encrypted QR data"""
    data = f"{member_id}|{gym_id}|{timestamp}"
    signature = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{data}|{signature}".encode()).decode()

def sanitize_qr_input(qr_code: str) -> str:
    """Clean QR code string from scanner artifacts"""
    # Strip whitespace, newlines, carriage returns
    cleaned = qr_code.strip().replace('\n', '').replace('\r', '').replace(' ', '')
    # Fix base64 padding (QR scanners often strip trailing '=')
    padding_needed = len(cleaned) % 4
    if padding_needed:
        cleaned += '=' * (4 - padding_needed)
    return cleaned

def validate_qr_data(qr_code: str, max_age_seconds: int = 15) -> dict:
    """Validate QR code and return member info (supports dynamic and static)"""
    try:
        # Sanitize the QR input first
        qr_code = sanitize_qr_input(qr_code)
        logger.info(f"QR validation - sanitized input length: {len(qr_code)}, first 30 chars: {qr_code[:30]}")
        
        decoded = base64.urlsafe_b64decode(qr_code.encode()).decode()
        parts = decoded.split('|')
        logger.info(f"QR validation - decoded parts count: {len(parts)}")
        
        # Static QR: STATIC|member_id|gym_id|signature
        if len(parts) == 4 and parts[0] == "STATIC":
            _, member_id, gym_id, signature = parts
            data = f"STATIC|{member_id}|{gym_id}"
            expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
            if signature != expected_sig:
                logger.warning(f"QR STATIC sig mismatch: got={signature}, expected={expected_sig}")
                return {"valid": False, "reason": "Invalid signature"}
            return {"valid": True, "member_id": member_id, "gym_id": gym_id}
        
        # Dynamic QR: member_id|gym_id|timestamp|signature
        if len(parts) != 4:
            logger.warning(f"QR format error: expected 4 parts, got {len(parts)}: {parts}")
            return {"valid": False, "reason": "Invalid QR format"}
        
        member_id, gym_id, timestamp_str, signature = parts
        timestamp = int(timestamp_str)
        
        # Verify signature
        data = f"{member_id}|{gym_id}|{timestamp}"
        expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
        if signature != expected_sig:
            logger.warning(f"QR DYNAMIC sig mismatch: got={signature}, expected={expected_sig}, data={data}")
            return {"valid": False, "reason": "Invalid signature"}
        
        # Check expiration
        now = int(datetime.now(timezone.utc).timestamp())
        age = now - timestamp
        if age > max_age_seconds:
            logger.info(f"QR expired: age={age}s, max={max_age_seconds}s")
            return {"valid": False, "reason": "QR expired"}
        
        return {"valid": True, "member_id": member_id, "gym_id": gym_id}
    except Exception as e:
        logger.error(f"QR validation error: {e}, raw input (first 50): {qr_code[:50]}")
        return {"valid": False, "reason": "Invalid QR code"}

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/admin/register")
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

@api_router.post("/auth/admin/login")
async def login_admin(login: AdminLogin):
    admin = await db.admins.find_one({"email": login.email})
    if not admin or not verify_password(login.password, admin["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token({"sub": admin["id"], "role": admin["role"], "gym_id": admin.get("gym_id")})
    
    admin_data = {k: v for k, v in admin.items() if k not in ["_id", "password"]}
    return {"admin": admin_data, "token": token}

@api_router.post("/auth/admin/impersonate/{gym_id}")
async def impersonate_gym(gym_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Super admin impersonates a gym admin to manage a specific gym"""
    payload = decode_jwt_token(credentials.credentials)
    if payload.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Solo el super admin puede usar esta función")
    
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    
    original_admin = await db.admins.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not original_admin:
        raise HTTPException(status_code=404, detail="Admin no encontrado")
    
    # Create impersonation token with the gym_id
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

@api_router.post("/auth/member/login")
async def login_member(code: str):
    """Login member with their unique code"""
    member = await db.members.find_one({"code": code.upper()}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.get("status") == "blocked":
        raise HTTPException(status_code=403, detail="Account blocked")
    
    # Get gym info
    gym = await db.gyms.find_one({"id": member["gym_id"]}, {"_id": 0})
    
    # Get active membership
    membership = await db.memberships.find_one(
        {"member_id": member["id"], "status": "active"},
        {"_id": 0}
    )
    
    token = create_jwt_token({"sub": member["id"], "role": "member", "gym_id": member["gym_id"]})
    
    return {
        "member": member,
        "gym": gym,
        "membership": membership,
        "token": token
    }

@api_router.get("/auth/member/me")
async def get_member_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    if payload.get("role") != "member":
        raise HTTPException(status_code=403, detail="Not a member")
    
    member = await db.members.find_one({"id": payload.get("sub")}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    gym = await db.gyms.find_one({"id": member["gym_id"]}, {"_id": 0})
    membership = await db.memberships.find_one(
        {"member_id": member["id"], "status": "active"},
        {"_id": 0}
    )
    
    plan = None
    if membership:
        plan = await db.plans.find_one({"id": membership["plan_id"]}, {"_id": 0})
    
    return {"member": member, "gym": gym, "membership": membership, "plan": plan}

# ==================== GYM ROUTES ====================

@api_router.post("/gyms")
async def create_gym(gym: GymCreate, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can create gyms")
    
    gym_dict = gym.model_dump()
    gym_dict["id"] = str(uuid.uuid4())
    gym_dict["api_token"] = secrets.token_urlsafe(32)
    gym_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Create default email templates
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
    
    # Auto-create gym admin if credentials provided
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
    
    # Remove internal fields
    for key in ["admin_email", "admin_password", "admin_name"]:
        gym_dict.pop(key, None)
    
    return gym_dict

@api_router.get("/gyms")
async def get_gyms(admin: dict = Depends(get_current_admin)):
    if admin["role"] == "super_admin":
        gyms = await db.gyms.find({}, {"_id": 0}).to_list(100)
        # Enrich with admin info for each gym
        for gym in gyms:
            gym_admin = await db.admins.find_one(
                {"gym_id": gym["id"], "role": "gym_admin"}, 
                {"_id": 0, "email": 1, "name": 1}
            )
            gym["gym_admin_email"] = gym_admin["email"] if gym_admin else None
            gym["gym_admin_name"] = gym_admin["name"] if gym_admin else None
    else:
        gyms = await db.gyms.find({"id": admin.get("gym_id")}, {"_id": 0}).to_list(1)
    return gyms

@api_router.get("/gyms/{gym_id}")
async def get_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    return gym

@api_router.put("/gyms/{gym_id}")
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

@api_router.put("/gyms/{gym_id}/templates/{template_type}")
async def update_email_template(gym_id: str, template_type: str, template: EmailTemplateUpdate, admin: dict = Depends(get_current_admin)):
    await db.gyms.update_one(
        {"id": gym_id, "email_templates.type": template_type},
        {"$set": {"email_templates.$.subject": template.subject, "email_templates.$.body": template.body}}
    )
    return {"message": "Template updated"}

@api_router.post("/gyms/{gym_id}/regenerate-token")
async def regenerate_gym_token(gym_id: str, admin: dict = Depends(get_current_admin)):
    new_token = secrets.token_urlsafe(32)
    await db.gyms.update_one({"id": gym_id}, {"$set": {"api_token": new_token}})
    return {"api_token": new_token}

@api_router.put("/gyms/{gym_id}/suspend")
async def suspend_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    """Suspend or reactivate a gym"""
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can suspend gyms")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    new_status = "active" if gym.get("status") == "suspended" else "suspended"
    await db.gyms.update_one({"id": gym_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": f"Gym {'reactivated' if new_status == 'active' else 'suspended'}", "status": new_status}

@api_router.delete("/gyms/{gym_id}")
async def delete_gym(gym_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a gym and all its data"""
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can delete gyms")
    gym = await db.gyms.find_one({"id": gym_id})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    await db.gyms.delete_one({"id": gym_id})
    await db.members.delete_many({"gym_id": gym_id})
    await db.memberships.delete_many({"gym_id": gym_id})
    await db.classes.delete_many({"gym_id": gym_id})
    await db.class_schedules.delete_many({"gym_id": gym_id})
    await db.bookings.delete_many({"gym_id": gym_id})
    await db.notifications.delete_many({"gym_id": gym_id})
    await db.guests.delete_many({"gym_id": gym_id})
    await db.access_logs.delete_many({"gym_id": gym_id})
    await db.devices.delete_many({"gym_id": gym_id})
    await db.admins.delete_many({"gym_id": gym_id})
    return {"message": "Gym and all related data deleted"}

# ==================== MEMBER ROUTES ====================

@api_router.post("/members")
async def create_member(member: MemberCreate, admin: dict = Depends(get_current_admin)):
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered in this gym")
    
    member_dict = member.model_dump()
    member_dict["id"] = str(uuid.uuid4())
    member_dict["code"] = generate_member_code()
    member_dict["status"] = "active"
    member_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Ensure unique code
    while await db.members.find_one({"code": member_dict["code"]}):
        member_dict["code"] = generate_member_code()
    
    await db.members.insert_one(member_dict)
    member_dict.pop("_id", None)
    return member_dict

@api_router.post("/members/register")
async def register_member_public(member: MemberPublicRegister):
    """Public registration for members - optionally with a plan"""
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya está registrado en este gimnasio")
    
    gym = await db.gyms.find_one({"id": member.gym_id})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if gym.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Este gimnasio está suspendido")
    
    member_dict = {
        "id": str(uuid.uuid4()),
        "email": member.email,
        "name": member.name,
        "phone": member.phone,
        "gym_id": member.gym_id,
        "code": generate_member_code(),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    while await db.members.find_one({"code": member_dict["code"]}):
        member_dict["code"] = generate_member_code()
    
    await db.members.insert_one(member_dict)
    member_dict.pop("_id", None)
    
    # If a plan is selected and no Stripe, create a pending membership
    membership_data = None
    if member.plan_id:
        plan = await db.plans.find_one({"id": member.plan_id}, {"_id": 0})
        if plan:
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=plan["duration_days"])
            membership = {
                "id": str(uuid.uuid4()),
                "member_id": member_dict["id"],
                "plan_id": plan["id"],
                "gym_id": member.gym_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.memberships.insert_one(membership)
            membership.pop("_id", None)
            membership_data = membership
    
    # Create JWT token so they can login immediately
    token = create_jwt_token({
        "sub": member_dict["id"],
        "type": "member",
        "gym_id": member.gym_id
    })
    
    return {
        "member": member_dict,
        "membership": membership_data,
        "token": token,
        "message": f"Registro exitoso. Tu código de acceso es: {member_dict['code']}"
    }

@api_router.get("/members")
async def get_members(gym_id: Optional[str] = None, status: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if status:
        query["status"] = status
    
    members = await db.members.find(query, {"_id": 0}).to_list(1000)
    return members

@api_router.get("/members/{member_id}")
async def get_member(member_id: str, admin: dict = Depends(get_current_admin)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@api_router.put("/members/{member_id}")
async def update_member(member_id: str, member_update: MemberUpdate, admin: dict = Depends(get_current_admin)):
    update_data = {k: v for k, v in member_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    return member

@api_router.post("/members/{member_id}/approve")
async def approve_member(member_id: str, admin: dict = Depends(get_current_admin)):
    await db.members.update_one({"id": member_id}, {"$set": {"status": "active"}})
    return {"message": "Member approved"}

@api_router.post("/members/{member_id}/block")
async def block_member(member_id: str, admin: dict = Depends(get_current_admin)):
    await db.members.update_one({"id": member_id}, {"$set": {"status": "blocked"}})
    return {"message": "Member blocked"}

@api_router.post("/members/{member_id}/suspend")
async def suspend_member(member_id: str, body: dict = {}, admin: dict = Depends(get_current_admin)):
    """Suspend a member with a reason"""
    reason = body.get("reason", "Sin motivo especificado") if isinstance(body, dict) else "Sin motivo especificado"
    await db.members.update_one({"id": member_id}, {"$set": {
        "status": "suspended",
        "suspension_reason": reason,
        "suspended_at": datetime.now(timezone.utc).isoformat(),
        "suspended_by": admin.get("name", admin.get("email", ""))
    }})
    return {"message": "Member suspended", "reason": reason}

@api_router.delete("/members/{member_id}")
async def delete_member(member_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a member and all related data"""
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.members.delete_one({"id": member_id})
    await db.memberships.delete_many({"member_id": member_id})
    await db.bookings.delete_many({"member_id": member_id})
    await db.guests.delete_many({"member_id": member_id})
    await db.access_logs.delete_many({"member_id": member_id})
    return {"message": "Member deleted"}

@api_router.post("/members/check-expired-memberships")
async def check_expired_memberships(admin: dict = Depends(get_current_admin)):
    """Check and suspend members with expired memberships"""
    now = datetime.now(timezone.utc).isoformat()
    active_memberships = await db.memberships.find({"status": "active"}, {"_id": 0}).to_list(10000)
    suspended_count = 0
    for m in active_memberships:
        if m.get("end_date") and m["end_date"] < now:
            await db.memberships.update_one({"id": m["id"]}, {"$set": {"status": "expired"}})
            other_active = await db.memberships.find_one({"member_id": m["member_id"], "status": "active"})
            if not other_active:
                await db.members.update_one({"id": m["member_id"]}, {"$set": {
                    "status": "suspended",
                    "suspension_reason": "Membresía vencida",
                    "suspended_at": now
                }})
                suspended_count += 1
    return {"message": f"{suspended_count} members suspended due to expired memberships"}

@api_router.get("/gyms/{gym_id}/capacity")
async def get_gym_capacity(gym_id: str, admin: dict = Depends(get_current_admin)):
    """Get gym member capacity usage"""
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

# ==================== PLAN ROUTES ====================

@api_router.post("/plans")
async def create_plan(plan: PlanCreate, admin: dict = Depends(get_current_admin)):
    plan_dict = plan.model_dump()
    plan_dict["id"] = str(uuid.uuid4())
    plan_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    plan_dict["active"] = True
    
    await db.plans.insert_one(plan_dict)
    plan_dict.pop("_id", None)
    return plan_dict

@api_router.get("/plans")
async def get_plans(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"active": True}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    plans = await db.plans.find(query, {"_id": 0}).to_list(100)
    return plans

@api_router.get("/plans/public/{gym_id}")
async def get_plans_public(gym_id: str):
    """Public endpoint to get plans for a gym"""
    plans = await db.plans.find({"gym_id": gym_id, "active": True}, {"_id": 0}).to_list(100)
    if not plans:
        plans = await db.plans.find({"gym_id": gym_id}, {"_id": 0}).to_list(100)
    return plans

@api_router.get("/gyms/{gym_id}/public-info")
async def get_gym_public_info(gym_id: str):
    """Public endpoint to get gym info for registration page"""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if gym.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Este gimnasio está suspendido")
    
    has_stripe = bool(gym.get("stripe_secret_key"))
    return {
        "id": gym["id"],
        "name": gym.get("name", ""),
        "logo_url": gym.get("logo_url"),
        "primary_color": gym.get("primary_color", "#E1FF01"),
        "address": gym.get("address"),
        "phone": gym.get("phone"),
        "email": gym.get("email"),
        "has_payments": has_stripe,
        "currency": gym.get("stripe_currency", "usd")
    }

@api_router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, admin: dict = Depends(get_current_admin)):
    await db.plans.update_one({"id": plan_id}, {"$set": {"active": False}})
    return {"message": "Plan deleted"}

# ==================== MEMBERSHIP ROUTES ====================

@api_router.post("/memberships")
async def create_membership(membership: MembershipCreate, admin: dict = Depends(get_current_admin)):
    plan = await db.plans.find_one({"id": membership.plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Deactivate current membership
    await db.memberships.update_many(
        {"member_id": membership.member_id, "status": "active"},
        {"$set": {"status": "expired"}}
    )
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=plan["duration_days"])
    
    membership_dict = {
        "id": str(uuid.uuid4()),
        "member_id": membership.member_id,
        "plan_id": membership.plan_id,
        "gym_id": plan["gym_id"],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.memberships.insert_one(membership_dict)
    membership_dict.pop("_id", None)
    return membership_dict

@api_router.get("/memberships")
async def get_memberships(gym_id: Optional[str] = None, member_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if member_id:
        query["member_id"] = member_id
    
    memberships = await db.memberships.find(query, {"_id": 0}).to_list(1000)
    return memberships

@api_router.get("/memberships/expiring")
async def get_expiring_memberships(days: int = 10, admin: dict = Depends(get_current_admin)):
    """Get memberships expiring in X days"""
    query = {"status": "active"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=days)
    
    memberships = await db.memberships.find(query, {"_id": 0}).to_list(1000)
    expiring = []
    for m in memberships:
        end_date = datetime.fromisoformat(m["end_date"].replace('Z', '+00:00'))
        if now <= end_date <= future:
            member = await db.members.find_one({"id": m["member_id"]}, {"_id": 0})
            m["member"] = member
            expiring.append(m)
    
    return expiring

def generate_static_qr_data(member_id: str, gym_id: str) -> str:
    """Generate a static QR code that doesn't expire"""
    data = f"STATIC|{member_id}|{gym_id}"
    signature = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{data}|{signature}".encode()).decode()

# ==================== QR ROUTES ====================

@api_router.get("/qr/generate")
async def generate_qr(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    gym_id = payload.get("gym_id")
    
    # Get gym config for refresh time and QR mode
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    qr_mode = gym.get("qr_mode", "dynamic") if gym else "dynamic"
    refresh_seconds = gym.get("qr_refresh_seconds", 10) if gym else 10
    
    if qr_mode == "static":
        qr_data = generate_static_qr_data(member_id, gym_id)
        return {
            "qr_code": qr_data,
            "expires_at": 0,
            "refresh_seconds": 0,
            "qr_mode": "static"
        }
    
    timestamp = int(datetime.now(timezone.utc).timestamp())
    qr_data = generate_qr_data(member_id, gym_id, timestamp)
    
    return {
        "qr_code": qr_data,
        "expires_at": timestamp + refresh_seconds,
        "refresh_seconds": refresh_seconds,
        "qr_mode": "dynamic"
    }

# ==================== ACCESS ROUTES ====================

@api_router.post("/access/debug-qr")
async def debug_qr_validation(validation: AccessValidation):
    """Debug endpoint - shows step-by-step QR validation without granting access"""
    debug_info = {
        "step_1_raw_input": {
            "qr_code_length": len(validation.qr_code),
            "qr_code_first_40": validation.qr_code[:40],
            "qr_code_last_20": validation.qr_code[-20:],
            "has_whitespace": validation.qr_code != validation.qr_code.strip(),
            "has_newline": '\n' in validation.qr_code or '\r' in validation.qr_code,
        }
    }
    
    # Step 2: Sanitize
    sanitized = sanitize_qr_input(validation.qr_code)
    debug_info["step_2_sanitized"] = {
        "length": len(sanitized),
        "first_40": sanitized[:40],
        "changed_from_original": sanitized != validation.qr_code,
    }
    
    # Step 3: Decode
    try:
        decoded = base64.urlsafe_b64decode(sanitized.encode()).decode()
        parts = decoded.split('|')
        debug_info["step_3_decode"] = {
            "success": True,
            "decoded_content": decoded,
            "parts_count": len(parts),
            "parts": parts,
        }
    except Exception as e:
        debug_info["step_3_decode"] = {"success": False, "error": str(e)}
        return debug_info
    
    # Step 4: Signature check
    if len(parts) == 4:
        if parts[0] == "STATIC":
            data = f"STATIC|{parts[1]}|{parts[2]}"
        else:
            data = f"{parts[0]}|{parts[1]}|{parts[2]}"
        expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
        debug_info["step_4_signature"] = {
            "data_for_hmac": data,
            "received_signature": parts[3],
            "expected_signature": expected_sig,
            "match": parts[3] == expected_sig,
            "qr_secret_first_4": QR_SECRET[:4] + "...",
        }
    
    # Step 5: Gym token check
    gym = await db.gyms.find_one({"api_token": validation.gym_token}, {"_id": 0})
    debug_info["step_5_gym"] = {
        "gym_found": gym is not None,
        "gym_name": gym.get("name") if gym else None,
    }
    
    return debug_info

@api_router.get("/access/self-test")
async def access_self_test():
    """Self-test: generates a QR and immediately validates it. Use to verify QR_SECRET is consistent."""
    test_member_id = "self-test-member"
    test_gym_id = "self-test-gym"
    timestamp = int(datetime.now(timezone.utc).timestamp())
    
    # Generate
    qr_code = generate_qr_data(test_member_id, test_gym_id, timestamp)
    
    # Validate
    result = validate_qr_data(qr_code, max_age_seconds=60)
    
    # Also test static
    static_qr = generate_static_qr_data(test_member_id, test_gym_id)
    static_result = validate_qr_data(static_qr, max_age_seconds=9999999)
    
    # Test with simulated scanner corruptions
    corrupted_tests = {
        "trailing_newline": validate_qr_data(qr_code + "\n", max_age_seconds=60),
        "trailing_spaces": validate_qr_data(qr_code + "  ", max_age_seconds=60),
        "stripped_padding": validate_qr_data(qr_code.rstrip("="), max_age_seconds=60),
    }
    
    return {
        "qr_secret_loaded": QR_SECRET[:4] + "..." + QR_SECRET[-4:],
        "qr_secret_length": len(QR_SECRET),
        "dynamic_qr_test": {"qr_code_preview": qr_code[:40], "valid": result.get("valid"), "details": result},
        "static_qr_test": {"valid": static_result.get("valid"), "details": static_result},
        "corruption_tests": corrupted_tests,
        "all_passed": result.get("valid") and static_result.get("valid") and all(t.get("valid") for t in corrupted_tests.values())
    }

@api_router.post("/access/validate")
async def validate_access(validation: AccessValidation):
    """Validate QR code from Raspberry Pi (supports members and guests)"""
    logger.info(f"Access validate - raw qr_code length: {len(validation.qr_code)}, direction: {validation.direction}")
    
    # Verify gym token
    gym = await db.gyms.find_one({"api_token": validation.gym_token}, {"_id": 0})
    if not gym:
        return {"valid": False, "reason": "Invalid gym token"}
    
    # Validate QR - generous expiration for both directions
    # USB scanners can swap between reboots, so use same timeout for both
    max_age = max(gym.get("qr_refresh_seconds", 10) + 5, 300)
    result = validate_qr_data(validation.qr_code, max_age)
    
    if not result["valid"]:
        return result
    
    if result["gym_id"] != gym["id"]:
        return {"valid": False, "reason": "QR code not for this gym"}
    
    member_id = result["member_id"]
    
    # Check if it's a guest QR
    if member_id.startswith("GUEST:"):
        guest_id = member_id.replace("GUEST:", "")
        guest = await db.guests.find_one({"id": guest_id}, {"_id": 0})
        
        if not guest:
            return {"valid": False, "reason": "Guest not found"}
        
        # Check expiry
        valid_until = datetime.fromisoformat(guest["valid_until"].replace('Z', '+00:00'))
        if valid_until < datetime.now(timezone.utc):
            await db.guests.update_one({"id": guest_id}, {"$set": {"status": "expired"}})
            return {"valid": False, "reason": "Guest pass expired"}
        
        if guest["status"] != "active":
            return {"valid": False, "reason": f"Guest pass is {guest['status']}"}
        
        # Log access
        access_log = {
            "id": str(uuid.uuid4()),
            "guest_id": guest_id,
            "guest_name": guest["name"],
            "guest_code": guest["code"],
            "invited_by": guest["invited_by"],
            "invited_by_name": guest["invited_by_name"],
            "gym_id": gym["id"],
            "direction": validation.direction,
            "is_guest": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.access_logs.insert_one(access_log)
        
        # Update guest accesses count
        await db.guests.update_one({"id": guest_id}, {"$inc": {"accesses": 1}})
        
        return {
            "valid": True,
            "is_guest": True,
            "guest_name": guest["name"],
            "guest_code": guest["code"],
            "invited_by": guest["invited_by_name"],
            "direction": validation.direction
        }
    
    # Regular member validation
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        return {"valid": False, "reason": "Member not found"}
    
    if member["status"] != "active":
        return {"valid": False, "reason": f"Member status: {member['status']}"}
    
    # Check membership
    membership = await db.memberships.find_one({
        "member_id": member["id"],
        "status": "active"
    }, {"_id": 0})
    
    if not membership:
        return {"valid": False, "reason": "No active membership"}
    
    end_date = datetime.fromisoformat(membership["end_date"].replace('Z', '+00:00'))
    if end_date < datetime.now(timezone.utc):
        await db.memberships.update_one({"id": membership["id"]}, {"$set": {"status": "expired"}})
        return {"valid": False, "reason": "Membership expired"}
    
    # Anti-passback: prevent re-entry without exit (and vice versa)
    # Auto-detect direction based on last access log
    last_log = await db.access_logs.find_one(
        {"member_id": member["id"], "gym_id": gym["id"], "is_guest": {"$ne": True}},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    if last_log:
        last_direction = last_log.get("direction")
        if last_direction == "entrada":
            # Last was entry, this must be exit
            actual_direction = "salida"
        else:
            actual_direction = "entrada"
    else:
        # First time, must be entry
        actual_direction = "entrada"
    
    # Log access with auto-detected direction
    access_log = {
        "id": str(uuid.uuid4()),
        "member_id": member["id"],
        "member_name": member["name"],
        "member_code": member["code"],
        "gym_id": gym["id"],
        "direction": actual_direction,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.access_logs.insert_one(access_log)
    
    return {
        "valid": True,
        "member_name": member["name"],
        "member_code": member["code"],
        "direction": actual_direction
    }

@api_router.get("/access/logs")
async def get_access_logs(
    gym_id: Optional[str] = None,
    member_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    admin: dict = Depends(get_current_admin)
):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if member_id:
        query["member_id"] = member_id
    
    if date_from:
        query["timestamp"] = {"$gte": date_from}
    if date_to:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = date_to
        else:
            query["timestamp"] = {"$lte": date_to}
    
    logs = await db.access_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

@api_router.get("/access/logs/member")
async def get_member_access_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get access logs for current member"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    logs = await db.access_logs.find({"member_id": member_id}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    return logs

@api_router.get("/access/stats")
async def get_access_stats(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get access statistics for dashboard"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    # Today's accesses
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_query = {**query, "timestamp": {"$gte": today_start.isoformat()}}
    today_count = await db.access_logs.count_documents(today_query)
    
    # This week
    week_start = today_start - timedelta(days=today_start.weekday())
    week_query = {**query, "timestamp": {"$gte": week_start.isoformat()}}
    week_count = await db.access_logs.count_documents(week_query)
    
    # This month
    month_start = today_start.replace(day=1)
    month_query = {**query, "timestamp": {"$gte": month_start.isoformat()}}
    month_count = await db.access_logs.count_documents(month_query)
    
    # Active members
    member_query = {"status": "active"}
    if admin["role"] != "super_admin":
        member_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        member_query["gym_id"] = gym_id
    active_members = await db.members.count_documents(member_query)
    
    # Active memberships
    membership_query = {"status": "active"}
    if admin["role"] != "super_admin":
        membership_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        membership_query["gym_id"] = gym_id
    active_memberships = await db.memberships.count_documents(membership_query)
    
    return {
        "today_accesses": today_count,
        "week_accesses": week_count,
        "month_accesses": month_count,
        "active_members": active_members,
        "active_memberships": active_memberships
    }

@api_router.get("/access/stats/daily")
async def get_daily_access_stats(gym_id: Optional[str] = None, days: int = 7, admin: dict = Depends(get_current_admin)):
    """Get daily access count for the last N days for charts"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    today = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
    start_date = (today - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    day_names_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    
    daily_data = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_end = day.replace(hour=23, minute=59, second=59)
        day_query = {**query, "timestamp": {"$gte": day.isoformat(), "$lte": day_end.isoformat()}}
        count = await db.access_logs.count_documents(day_query)
        
        # Count unique entries (entrada only)
        entry_query = {**day_query, "direction": "entrada"}
        entries = await db.access_logs.count_documents(entry_query)
        
        daily_data.append({
            "date": day.strftime("%Y-%m-%d"),
            "day_name": day_names_es[day.weekday()],
            "accesos": count,
            "entradas": entries
        })
    
    return daily_data

@api_router.get("/access/stats/member/{member_id}")
async def get_member_access_stats(member_id: str, days: int = 30, admin: dict = Depends(get_current_admin)):
    """Get access statistics for a specific member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    today = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
    start_date = (today - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get all logs for period
    logs = await db.access_logs.find(
        {"member_id": member_id, "timestamp": {"$gte": start_date.isoformat()}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(1000)
    
    # Daily breakdown
    daily = {}
    for log in logs:
        day = log["timestamp"][:10]
        if day not in daily:
            daily[day] = {"entradas": 0, "salidas": 0}
        if log.get("direction") == "entrada":
            daily[day]["entradas"] += 1
        else:
            daily[day]["salidas"] += 1
    
    # Total stats
    total_entries = sum(d["entradas"] for d in daily.values())
    days_attended = len(daily)
    
    return {
        "member": {"id": member["id"], "name": member["name"], "code": member["code"]},
        "total_entries": total_entries,
        "days_attended": days_attended,
        "period_days": days,
        "attendance_rate": round((days_attended / days * 100), 1) if days > 0 else 0,
        "daily_breakdown": [{"date": k, **v} for k, v in sorted(daily.items())],
        "recent_logs": logs[:20]
    }

@api_router.get("/access/stats/hourly")
async def get_hourly_access_stats(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get hourly access distribution for today"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    query["timestamp"] = {"$gte": today_start.isoformat()}
    
    logs = await db.access_logs.find(query, {"_id": 0, "timestamp": 1}).to_list(10000)
    
    hourly = {f"{h:02d}:00": 0 for h in range(24)}
    for log in logs:
        try:
            hour = log["timestamp"][11:13]
            hourly[f"{hour}:00"] = hourly.get(f"{hour}:00", 0) + 1
        except (IndexError, KeyError):
            pass
    
    return [{"hour": k, "accesos": v} for k, v in hourly.items()]

# ==================== DEVICE ROUTES ====================

@api_router.post("/devices")
async def create_device(device: DeviceCreate, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede gestionar dispositivos")
    device_dict = device.model_dump()
    device_dict["id"] = str(uuid.uuid4())
    device_dict["status"] = "offline"
    device_dict["last_ping"] = None
    device_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.devices.insert_one(device_dict)
    device_dict.pop("_id", None)
    return device_dict

@api_router.get("/devices")
async def get_devices(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede ver dispositivos")
    query = {}
    if gym_id:
        query["gym_id"] = gym_id
    
    devices = await db.devices.find(query, {"_id": 0}).to_list(100)
    return devices

@api_router.delete("/devices/{device_id}")
async def delete_device(device_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a device"""
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede eliminar dispositivos")
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.devices.delete_one({"id": device_id})
    return {"message": "Device deleted"}

@api_router.post("/devices/{device_id}/ping")
async def ping_device(device_id: str, gym_token: str):
    """Heartbeat from Raspberry Pi"""
    gym = await db.gyms.find_one({"api_token": gym_token})
    if not gym:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    await db.devices.update_one(
        {"id": device_id},
        {"$set": {"status": "online", "last_ping": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok"}

# ==================== PAYMENT ROUTES ====================

@api_router.post("/payments/checkout")
async def create_checkout(
    request: Request,
    plan_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create Stripe checkout session for membership payment"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Use gym-specific Stripe key if available, otherwise fallback to global
    gym = await db.gyms.find_one({"id": plan["gym_id"]}, {"_id": 0})
    api_key = (gym or {}).get("stripe_secret_key") or os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="No se ha configurado la pasarela de pagos para este gimnasio")
    
    currency = (gym or {}).get("stripe_currency") or "usd"
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    origin_url = request.headers.get("origin", host_url)
    success_url = f"{origin_url}/app/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/app/membership"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(plan["price"]),
        currency=currency,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "member_id": member_id,
            "plan_id": plan_id,
            "gym_id": plan["gym_id"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "member_id": member_id,
        "plan_id": plan_id,
        "gym_id": plan["gym_id"],
        "amount": plan["price"],
        "currency": currency,
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check payment status and activate membership if paid"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    # Get transaction to find gym_id and use gym-specific Stripe key
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    api_key = os.environ.get("STRIPE_API_KEY")
    if transaction:
        gym = await db.gyms.find_one({"id": transaction.get("gym_id")}, {"_id": 0})
        if gym and gym.get("stripe_secret_key"):
            api_key = gym["stripe_secret_key"]
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if transaction and status.payment_status == "paid" and transaction["payment_status"] != "paid":
        # Activate membership
        plan = await db.plans.find_one({"id": transaction["plan_id"]})
        if plan:
            # Deactivate old memberships
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
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.memberships.insert_one(membership)
        
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": status.status, "payment_status": status.payment_status}}
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
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

# ==================== STRIPE CONFIG ROUTES ====================

@api_router.get("/gyms/{gym_id}/stripe-config")
async def get_stripe_config(gym_id: str, admin: dict = Depends(get_current_admin)):
    """Get Stripe configuration status for a gym (does not return the full key)"""
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
    
    return {
        "has_stripe_key": has_key,
        "masked_key": masked_key,
        "currency": gym.get("stripe_currency", "usd")
    }

@api_router.put("/gyms/{gym_id}/stripe-config")
async def update_stripe_config(gym_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    """Update Stripe configuration for a gym"""
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

@api_router.get("/gyms/{gym_id}/has-payments")
async def gym_has_payments(gym_id: str):
    """Public check if gym has payments configured (for member PWA)"""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        return {"has_payments": False}
    has_key = bool(gym.get("stripe_secret_key")) or bool(os.environ.get("STRIPE_API_KEY"))
    return {"has_payments": has_key, "currency": gym.get("stripe_currency", "usd")}

@api_router.get("/payments/history")
async def get_payment_history(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get payment transaction history for admin"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Enrich with member info
    for t in transactions:
        member = await db.members.find_one({"id": t.get("member_id")}, {"_id": 0, "name": 1, "code": 1, "email": 1})
        t["member"] = member
        plan = await db.plans.find_one({"id": t.get("plan_id")}, {"_id": 0, "name": 1})
        t["plan"] = plan
    
    return transactions

# ==================== DASHBOARD ROUTES ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin)):
    """Get comprehensive dashboard statistics"""
    gym_id = admin.get("gym_id") if admin["role"] != "super_admin" else None
    
    query = {}
    if gym_id:
        query["gym_id"] = gym_id
    
    # Members stats
    total_members = await db.members.count_documents(query if query else {})
    active_members = await db.members.count_documents({**query, "status": "active"})
    pending_members = await db.members.count_documents({**query, "status": "pending"})
    
    # Access stats
    access_stats = await get_access_stats(gym_id, admin)
    
    # Revenue (this month)
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    revenue_query = {"payment_status": "paid", "created_at": {"$gte": month_start.isoformat()}}
    if gym_id:
        revenue_query["gym_id"] = gym_id
    
    transactions = await db.payment_transactions.find(revenue_query, {"_id": 0}).to_list(1000)
    month_revenue = sum(t.get("amount", 0) for t in transactions)
    
    # Gyms count (for super admin)
    gyms_count = await db.gyms.count_documents({}) if admin["role"] == "super_admin" else 1
    
    # Classes stats
    classes_count = await db.classes.count_documents({**query, "active": True})
    today = datetime.now(timezone.utc).date().isoformat()
    today_schedules = await db.class_schedules.count_documents({**query, "date": today})
    
    # Today's bookings
    today_bookings = await db.bookings.count_documents({"date": today, "status": "confirmed", **({} if not gym_id else {"gym_id": gym_id})})
    
    # Capacity info
    capacity_info = None
    if gym_id:
        gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0, "max_members": 1})
        max_members = gym.get("max_members") if gym else None
        if max_members and max_members > 0:
            capacity_info = {
                "max_members": max_members,
                "active_members": active_members,
                "usage_percent": round((active_members / max_members * 100), 1)
            }

    # Suspended members count
    suspended_members = await db.members.count_documents({**query, "status": "suspended"})

    # For super admin: enrich recent accesses with gym name
    recent_accesses_enriched = []
    if admin["role"] == "super_admin":
        recent_logs = await db.access_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(15)
        gym_cache = {}
        for log in recent_logs:
            gid = log.get("gym_id")
            if gid and gid not in gym_cache:
                g = await db.gyms.find_one({"id": gid}, {"_id": 0, "name": 1})
                gym_cache[gid] = g.get("name", "?") if g else "?"
            log["gym_name"] = gym_cache.get(gid, "?")
            recent_accesses_enriched.append(log)

    return {
        "total_members": total_members,
        "active_members": active_members,
        "pending_members": pending_members,
        "suspended_members": suspended_members,
        "gyms_count": gyms_count,
        "month_revenue": month_revenue,
        "classes_count": classes_count,
        "today_schedules": today_schedules,
        "today_bookings": today_bookings,
        "capacity": capacity_info,
        "recent_accesses_by_gym": recent_accesses_enriched if admin["role"] == "super_admin" else [],
        **access_stats
    }

# ==================== ROLE HELPERS ====================

def check_role(admin: dict, allowed_roles: List[str], gym_id: str = None):
    """Check if admin has required role"""
    if admin["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Access denied. Required roles: {allowed_roles}")
    if gym_id and admin["role"] != "super_admin" and admin.get("gym_id") != gym_id:
        raise HTTPException(status_code=403, detail="Access denied to this gym")

# ==================== TRAINER ROUTES ====================

@api_router.post("/trainers")
async def create_trainer(trainer: TrainerCreate, admin: dict = Depends(get_current_admin)):
    """Create a new trainer (gym_admin, gym_manager only)"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"], trainer.gym_id)
    
    existing = await db.admins.find_one({"email": trainer.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    trainer_dict = {
        "id": str(uuid.uuid4()),
        "email": trainer.email,
        "password": hash_password(trainer.password),
        "name": trainer.name,
        "phone": trainer.phone,
        "role": "trainer",
        "gym_id": trainer.gym_id,
        "specialties": trainer.specialties or [],
        "bio": trainer.bio,
        "avatar_url": trainer.avatar_url,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.admins.insert_one(trainer_dict)
    trainer_dict.pop("password", None)
    trainer_dict.pop("_id", None)
    return trainer_dict

@api_router.get("/trainers")
async def get_trainers(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get trainers list"""
    query = {"role": "trainer"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    trainers = await db.admins.find(query, {"_id": 0, "password": 0}).to_list(100)
    return trainers

@api_router.get("/trainers/{trainer_id}")
async def get_trainer(trainer_id: str, admin: dict = Depends(get_current_admin)):
    trainer = await db.admins.find_one({"id": trainer_id, "role": "trainer"}, {"_id": 0, "password": 0})
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return trainer

@api_router.put("/trainers/{trainer_id}")
async def update_trainer(trainer_id: str, update_data: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    allowed_fields = ["name", "phone", "specialties", "bio", "avatar_url", "active"]
    update_dict = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    await db.admins.update_one({"id": trainer_id, "role": "trainer"}, {"$set": update_dict})
    return {"message": "Trainer updated"}

# ==================== STAFF/MANAGER ROUTES ====================

@api_router.post("/staff")
async def create_staff(staff_data: AdminCreate, admin: dict = Depends(get_current_admin)):
    """Create gym_manager or gym_admin staff"""
    check_role(admin, ["super_admin", "gym_admin"])
    
    if staff_data.role not in ["gym_admin", "gym_manager"]:
        raise HTTPException(status_code=400, detail="Invalid role. Use 'gym_admin' or 'gym_manager'")
    
    existing = await db.admins.find_one({"email": staff_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    gym_id = staff_data.gym_id or admin.get("gym_id")
    if not gym_id and admin["role"] != "super_admin":
        raise HTTPException(status_code=400, detail="gym_id required")
    
    staff_dict = {
        "id": str(uuid.uuid4()),
        "email": staff_data.email,
        "password": hash_password(staff_data.password),
        "name": staff_data.name,
        "role": staff_data.role,
        "gym_id": gym_id,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.admins.insert_one(staff_dict)
    staff_dict.pop("password", None)
    staff_dict.pop("_id", None)
    return staff_dict

@api_router.get("/staff")
async def get_staff(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get staff list (admins, managers, trainers)"""
    check_role(admin, ["super_admin", "gym_admin"])
    
    query = {"role": {"$in": ["gym_admin", "gym_manager", "trainer"]}}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    staff = await db.admins.find(query, {"_id": 0, "password": 0}).to_list(100)
    return staff

# ==================== CLASS ROUTES ====================

@api_router.post("/classes")
async def create_class(class_data: ClassCreate, admin: dict = Depends(get_current_admin)):
    """Create a new class"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"], class_data.gym_id)
    
    class_dict = class_data.model_dump()
    class_dict["id"] = str(uuid.uuid4())
    class_dict["active"] = True
    class_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.classes.insert_one(class_dict)
    class_dict.pop("_id", None)
    
    # If recurring, create schedules for next 4 weeks
    if class_data.recurring and class_data.days_of_week and class_data.start_time:
        await generate_recurring_schedules(class_dict, weeks=4)
    
    # If single class, create one schedule
    if not class_data.recurring and class_data.single_date and class_data.single_start_time:
        schedule = {
            "id": str(uuid.uuid4()),
            "class_id": class_dict["id"],
            "gym_id": class_data.gym_id,
            "date": class_data.single_date,
            "start_time": class_data.single_start_time,
            "end_time": calculate_end_time(class_data.single_start_time, class_data.duration_minutes),
            "trainer_id": class_data.trainer_id,
            "max_capacity": class_data.max_capacity,
            "current_bookings": 0,
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.class_schedules.insert_one(schedule)
    
    return class_dict

async def generate_recurring_schedules(class_data: dict, weeks: int = 4):
    """Generate schedules for recurring classes"""
    from datetime import date, timedelta
    
    today = date.today()
    schedules = []
    
    for week in range(weeks):
        for day_offset in range(7):
            current_date = today + timedelta(days=week*7 + day_offset)
            weekday = current_date.weekday()
            
            if weekday in class_data.get("days_of_week", []):
                schedule = {
                    "id": str(uuid.uuid4()),
                    "class_id": class_data["id"],
                    "gym_id": class_data["gym_id"],
                    "date": current_date.isoformat(),
                    "start_time": class_data["start_time"],
                    "end_time": calculate_end_time(class_data["start_time"], class_data["duration_minutes"]),
                    "trainer_id": class_data.get("trainer_id"),
                    "max_capacity": class_data["max_capacity"],
                    "current_bookings": 0,
                    "status": "scheduled",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                schedules.append(schedule)
    
    if schedules:
        await db.class_schedules.insert_many(schedules)

def calculate_end_time(start_time: str, duration_minutes: int) -> str:
    """Calculate end time from start time and duration"""
    hours, minutes = map(int, start_time.split(":"))
    total_minutes = hours * 60 + minutes + duration_minutes
    end_hours = (total_minutes // 60) % 24
    end_minutes = total_minutes % 60
    return f"{end_hours:02d}:{end_minutes:02d}"

@api_router.get("/classes")
async def get_classes(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get classes list"""
    query = {"active": True}
    
    if admin["role"] == "trainer":
        # Trainers only see their classes
        query["trainer_id"] = admin["id"]
        query["gym_id"] = admin.get("gym_id")
    elif admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    classes = await db.classes.find(query, {"_id": 0}).to_list(100)
    
    # Add trainer info
    for c in classes:
        if c.get("trainer_id"):
            trainer = await db.admins.find_one({"id": c["trainer_id"]}, {"_id": 0, "password": 0})
            c["trainer"] = trainer
    
    return classes

@api_router.get("/classes/{class_id}")
async def get_class(class_id: str, admin: dict = Depends(get_current_admin)):
    class_data = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_data:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_data

@api_router.put("/classes/{class_id}")
async def update_class(class_id: str, class_update: ClassUpdate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    update_data = {k: v for k, v in class_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.classes.update_one({"id": class_id}, {"$set": update_data})
    return {"message": "Class updated"}

@api_router.delete("/classes/{class_id}")
async def delete_class(class_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    # Soft delete
    await db.classes.update_one({"id": class_id}, {"$set": {"active": False}})
    return {"message": "Class deleted"}

# ==================== CLASS SCHEDULE ROUTES ====================

@api_router.post("/schedules")
async def create_schedule(schedule: ClassScheduleCreate, admin: dict = Depends(get_current_admin)):
    """Create a single class schedule"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    # Get class info
    class_data = await db.classes.find_one({"id": schedule.class_id}, {"_id": 0})
    if not class_data:
        raise HTTPException(status_code=404, detail="Class not found")
    
    schedule_dict = {
        "id": str(uuid.uuid4()),
        "class_id": schedule.class_id,
        "gym_id": class_data["gym_id"],
        "class_name": class_data["name"],
        "date": schedule.date,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "trainer_id": schedule.trainer_id or class_data.get("trainer_id"),
        "max_capacity": schedule.max_capacity or class_data["max_capacity"],
        "current_bookings": 0,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.class_schedules.insert_one(schedule_dict)
    schedule_dict.pop("_id", None)
    return schedule_dict

@api_router.get("/schedules")
async def get_schedules(
    gym_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    trainer_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get class schedules"""
    query = {"status": {"$ne": "cancelled"}}
    
    if admin["role"] == "trainer":
        query["trainer_id"] = admin["id"]
        query["gym_id"] = admin.get("gym_id")
    elif admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    if trainer_id:
        query["trainer_id"] = trainer_id
    
    schedules = await db.class_schedules.find(query, {"_id": 0}).sort("date", 1).to_list(500)
    
    # Add class and trainer info
    for s in schedules:
        class_data = await db.classes.find_one({"id": s["class_id"]}, {"_id": 0})
        s["class"] = class_data
        if s.get("trainer_id"):
            trainer = await db.admins.find_one({"id": s["trainer_id"]}, {"_id": 0, "password": 0})
            s["trainer"] = trainer
    
    return schedules

@api_router.get("/schedules/public/{gym_id}")
async def get_public_schedules(gym_id: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Get public schedules for a gym (for members)"""
    query = {"gym_id": gym_id, "status": "scheduled"}
    
    if not date_from:
        date_from = datetime.now(timezone.utc).date().isoformat()
    query["date"] = {"$gte": date_from}
    
    if date_to:
        query["date"]["$lte"] = date_to
    
    schedules = await db.class_schedules.find(query, {"_id": 0}).sort([("date", 1), ("start_time", 1)]).to_list(100)
    
    for s in schedules:
        class_data = await db.classes.find_one({"id": s["class_id"]}, {"_id": 0})
        s["class"] = class_data
        if s.get("trainer_id"):
            trainer = await db.admins.find_one({"id": s["trainer_id"]}, {"_id": 0, "password": 0})
            s["trainer"] = trainer
        s["spots_available"] = s["max_capacity"] - s["current_bookings"]
    
    return schedules

@api_router.put("/schedules/{schedule_id}/cancel")
async def cancel_schedule(schedule_id: str, admin: dict = Depends(get_current_admin)):
    """Cancel a scheduled class"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    await db.class_schedules.update_one({"id": schedule_id}, {"$set": {"status": "cancelled"}})
    # Cancel all bookings for this schedule
    await db.bookings.update_many({"schedule_id": schedule_id}, {"$set": {"status": "cancelled"}})
    return {"message": "Schedule cancelled"}

# ==================== BOOKING ROUTES ====================

@api_router.post("/bookings")
async def create_booking(booking: BookingCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a booking for a member"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    if payload.get("role") != "member":
        raise HTTPException(status_code=403, detail="Only members can book classes")
    
    # Get schedule
    schedule = await db.class_schedules.find_one({"id": booking.schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if schedule["status"] != "scheduled":
        raise HTTPException(status_code=400, detail="Class is not available for booking")
    
    if schedule["current_bookings"] >= schedule["max_capacity"]:
        raise HTTPException(status_code=400, detail="Class is full")
    
    # Check if already booked
    existing = await db.bookings.find_one({
        "member_id": member_id,
        "schedule_id": booking.schedule_id,
        "status": {"$ne": "cancelled"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already booked for this class")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    
    booking_dict = {
        "id": str(uuid.uuid4()),
        "member_id": member_id,
        "member_name": member["name"],
        "member_code": member["code"],
        "schedule_id": booking.schedule_id,
        "class_id": schedule["class_id"],
        "gym_id": schedule["gym_id"],
        "date": schedule["date"],
        "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bookings.insert_one(booking_dict)
    
    # Update schedule bookings count
    await db.class_schedules.update_one(
        {"id": booking.schedule_id},
        {"$inc": {"current_bookings": 1}}
    )
    
    booking_dict.pop("_id", None)
    return booking_dict

@api_router.get("/bookings")
async def get_bookings(
    gym_id: Optional[str] = None,
    schedule_id: Optional[str] = None,
    date: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get bookings (admin view)"""
    query = {}
    
    if admin["role"] == "trainer":
        # Get trainer's schedules first
        trainer_schedules = await db.class_schedules.find(
            {"trainer_id": admin["id"]},
            {"id": 1}
        ).to_list(1000)
        schedule_ids = [s["id"] for s in trainer_schedules]
        query["schedule_id"] = {"$in": schedule_ids}
    elif admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if schedule_id:
        query["schedule_id"] = schedule_id
    if date:
        query["date"] = date
    
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return bookings

@api_router.get("/bookings/member")
async def get_member_bookings(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get bookings for current member"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    bookings = await db.bookings.find(
        {"member_id": member_id, "status": {"$ne": "cancelled"}},
        {"_id": 0}
    ).sort("date", -1).to_list(50)
    
    # Add schedule/class info
    for b in bookings:
        schedule = await db.class_schedules.find_one({"id": b["schedule_id"]}, {"_id": 0})
        if schedule:
            class_data = await db.classes.find_one({"id": schedule["class_id"]}, {"_id": 0})
            b["schedule"] = schedule
            b["class"] = class_data
    
    return bookings

@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cancel a booking"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check ownership (unless admin)
    if payload.get("role") == "member" and booking["member_id"] != member_id:
        raise HTTPException(status_code=403, detail="Cannot cancel others' bookings")
    
    await db.bookings.update_one({"id": booking_id}, {"$set": {"status": "cancelled"}})
    
    # Decrease schedule bookings count
    await db.class_schedules.update_one(
        {"id": booking["schedule_id"]},
        {"$inc": {"current_bookings": -1}}
    )
    
    return {"message": "Booking cancelled"}

@api_router.get("/bookings/schedule/{schedule_id}/attendees")
async def get_schedule_attendees(schedule_id: str, admin: dict = Depends(get_current_admin)):
    """Get list of attendees for a class (trainer can see this)"""
    bookings = await db.bookings.find(
        {"schedule_id": schedule_id, "status": "confirmed"},
        {"_id": 0}
    ).to_list(100)
    
    return bookings

# ==================== NOTIFICATION ROUTES ====================

@api_router.post("/notifications")
async def create_notification(notification: NotificationCreate, admin: dict = Depends(get_current_admin)):
    """Create a notification for gym members"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"], notification.gym_id)
    
    notification_dict = {
        "id": str(uuid.uuid4()),
        "gym_id": notification.gym_id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "target": notification.target,
        "created_by": admin["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_by": []
    }
    
    await db.notifications.insert_one(notification_dict)
    notification_dict.pop("_id", None)
    return notification_dict

@api_router.get("/notifications")
async def get_notifications(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get notifications for admin view"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notifications

@api_router.get("/notifications/member")
async def get_member_notifications(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get notifications for current member"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    gym_id = payload.get("gym_id")
    
    # Get member to check status
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        return []
    
    # Get notifications for this gym
    query = {"gym_id": gym_id}
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Add read status
    for n in notifications:
        n["is_read"] = member_id in n.get("read_by", [])
    
    return notifications

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Mark notification as read"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    await db.notifications.update_one(
        {"id": notification_id},
        {"$addToSet": {"read_by": member_id}}
    )
    return {"message": "Marked as read"}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a notification"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    await db.notifications.delete_one({"id": notification_id})
    return {"message": "Notification deleted"}

# ==================== GUEST PASS ROUTES ====================

@api_router.post("/guests")
async def create_guest_pass(guest: GuestCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a guest pass (member creates for their guest)"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if member can bring guests
    if not member.get("can_bring_guests", False):
        raise HTTPException(status_code=403, detail="No tienes permiso para traer invitados. Consulta con administración.")
    
    # Check monthly guest limit
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    guests_this_month = await db.guests.count_documents({
        "invited_by": member_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    max_guests = member.get("max_guests_per_month", 2)
    if guests_this_month >= max_guests:
        raise HTTPException(status_code=400, detail=f"Has alcanzado el límite de {max_guests} invitados este mes")
    
    # Generate guest code
    guest_code = "G" + generate_member_code()
    
    # Calculate expiry
    valid_until = datetime.now(timezone.utc) + timedelta(days=guest.valid_days)
    
    guest_dict = {
        "id": str(uuid.uuid4()),
        "code": guest_code,
        "name": guest.name,
        "phone": guest.phone,
        "invited_by": member_id,
        "invited_by_name": member["name"],
        "gym_id": member["gym_id"],
        "valid_until": valid_until.isoformat(),
        "valid_days": guest.valid_days,
        "status": "active",  # active, used, expired
        "accesses": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.guests.insert_one(guest_dict)
    guest_dict.pop("_id", None)
    return guest_dict

@api_router.get("/guests/member")
async def get_member_guests(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get guests invited by current member"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    
    guests = await db.guests.find(
        {"invited_by": member_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Update status for expired guests
    now = datetime.now(timezone.utc)
    for g in guests:
        valid_until = datetime.fromisoformat(g["valid_until"].replace('Z', '+00:00'))
        if valid_until < now and g["status"] == "active":
            g["status"] = "expired"
            await db.guests.update_one({"id": g["id"]}, {"$set": {"status": "expired"}})
    
    return guests

@api_router.get("/guests")
async def get_all_guests(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """Get all guests for admin view"""
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    guests = await db.guests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return guests

@api_router.get("/guests/{guest_code}/qr")
async def get_guest_qr(guest_code: str):
    """Generate QR code for guest (public endpoint for guest to access)"""
    guest = await db.guests.find_one({"code": guest_code.upper()}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Check if expired
    valid_until = datetime.fromisoformat(guest["valid_until"].replace('Z', '+00:00'))
    if valid_until < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Guest pass expired")
    
    if guest["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Guest pass is {guest['status']}")
    
    # Generate QR
    timestamp = int(datetime.now(timezone.utc).timestamp())
    qr_data = generate_qr_data(f"GUEST:{guest['id']}", guest["gym_id"], timestamp)
    
    # Get gym for refresh time
    gym = await db.gyms.find_one({"id": guest["gym_id"]}, {"_id": 0})
    refresh_seconds = gym.get("qr_refresh_seconds", 10) if gym else 10
    
    return {
        "qr_code": qr_data,
        "guest": guest,
        "expires_at": timestamp + refresh_seconds,
        "refresh_seconds": refresh_seconds
    }

@api_router.post("/access/validate/guest")
async def validate_guest_access(validation: AccessValidation):
    """Validate guest QR code from Raspberry Pi"""
    # Verify gym token
    gym = await db.gyms.find_one({"api_token": validation.gym_token}, {"_id": 0})
    if not gym:
        return {"valid": False, "reason": "Invalid gym token"}
    
    # Validate QR - generous expiration for both directions
    max_age = max(gym.get("qr_refresh_seconds", 10) + 5, 300)
    result = validate_qr_data(validation.qr_code, max_age)
    
    if not result["valid"]:
        return result
    
    member_id = result["member_id"]
    
    # Check if it's a guest QR
    if member_id.startswith("GUEST:"):
        guest_id = member_id.replace("GUEST:", "")
        guest = await db.guests.find_one({"id": guest_id}, {"_id": 0})
        
        if not guest:
            return {"valid": False, "reason": "Guest not found"}
        
        if guest["gym_id"] != gym["id"]:
            return {"valid": False, "reason": "Guest not valid for this gym"}
        
        # Check expiry
        valid_until = datetime.fromisoformat(guest["valid_until"].replace('Z', '+00:00'))
        if valid_until < datetime.now(timezone.utc):
            await db.guests.update_one({"id": guest_id}, {"$set": {"status": "expired"}})
            return {"valid": False, "reason": "Guest pass expired"}
        
        if guest["status"] != "active":
            return {"valid": False, "reason": f"Guest pass is {guest['status']}"}
        
        # Log access
        access_log = {
            "id": str(uuid.uuid4()),
            "guest_id": guest_id,
            "guest_name": guest["name"],
            "guest_code": guest["code"],
            "invited_by": guest["invited_by"],
            "gym_id": gym["id"],
            "direction": validation.direction,
            "is_guest": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.access_logs.insert_one(access_log)
        
        # Update guest accesses count
        await db.guests.update_one({"id": guest_id}, {"$inc": {"accesses": 1}})
        
        return {
            "valid": True,
            "is_guest": True,
            "guest_name": guest["name"],
            "guest_code": guest["code"],
            "invited_by": guest["invited_by_name"],
            "direction": validation.direction
        }
    
    # Regular member validation continues in original endpoint
    return {"valid": False, "reason": "Use /access/validate for members"}

@api_router.put("/members/{member_id}/guest-permission")
async def update_guest_permission(
    member_id: str, 
    can_bring_guests: bool,
    max_guests_per_month: int = 2,
    admin: dict = Depends(get_current_admin)
):
    """Update member's permission to bring guests"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "can_bring_guests": can_bring_guests,
            "max_guests_per_month": max_guests_per_month
        }}
    )
    return {"message": "Guest permission updated"}

# ==================== EMAIL UTILITY ====================

async def send_gym_email(gym_id: str, to_email: str, subject: str, html_body: str):
    """Send email using gym-specific SMTP config"""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    smtp_host = gym.get("smtp_host")
    smtp_port = gym.get("smtp_port", 587)
    smtp_user = gym.get("smtp_user")
    smtp_password = gym.get("smtp_password")
    smtp_from = gym.get("smtp_from_email", smtp_user)
    
    if not smtp_host or not smtp_user or not smtp_password:
        raise HTTPException(status_code=400, detail="SMTP no configurado para este gimnasio")
    
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{gym.get('name', 'GymAccess')} <{smtp_from}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    
    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            use_tls=smtp_port == 465,
            start_tls=smtp_port != 465
        )
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al enviar email: {str(e)}")

@api_router.post("/email/test")
async def test_email(admin: dict = Depends(get_current_admin)):
    """Test SMTP configuration by sending a test email"""
    gym_id = admin.get("gym_id")
    if not gym_id:
        raise HTTPException(status_code=400, detail="Selecciona un gimnasio")
    
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    to_email = gym.get("smtp_from_email") or gym.get("smtp_user")
    if not to_email:
        raise HTTPException(status_code=400, detail="SMTP no configurado")
    
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
        <h2 style="color:{gym.get('primary_color','#E1FF01')};">Prueba de Email</h2>
        <p>Este es un correo de prueba desde <strong>{gym.get('name','GymAccess')}</strong>.</p>
        <p>Si recibes este correo, tu configuración SMTP es correcta.</p>
    </div>
    """
    await send_gym_email(gym_id, to_email, f"[{gym.get('name')}] Prueba de configuración SMTP", html)
    return {"message": f"Email de prueba enviado a {to_email}"}

@api_router.post("/email/welcome/{member_id}")
async def send_welcome_email(member_id: str, admin: dict = Depends(get_current_admin)):
    """Send welcome email to a member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    
    gym_id = member.get("gym_id")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    
    color = gym.get("primary_color", "#E1FF01")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:30px;background:#09090B;color:#fff;border-radius:16px;">
        <div style="text-align:center;margin-bottom:20px;">
            <h1 style="color:{color};margin:0;">{gym.get('name','GymAccess')}</h1>
        </div>
        <h2>Bienvenido/a, {member.get('name','Socio')}</h2>
        <p>Tu registro en <strong>{gym.get('name')}</strong> ha sido completado con éxito.</p>
        <div style="background:#18181B;padding:20px;border-radius:12px;text-align:center;margin:20px 0;">
            <p style="color:#a1a1aa;margin:0 0 8px;">Tu código de acceso</p>
            <p style="font-size:32px;font-weight:900;color:{color};font-family:monospace;letter-spacing:4px;margin:0;">
                {member.get('code','------')}
            </p>
        </div>
        <p style="color:#a1a1aa;font-size:14px;">Usa este código para acceder al gimnasio con tu QR.</p>
    </div>
    """
    await send_gym_email(gym_id, member["email"], f"Bienvenido/a a {gym.get('name')}", html)
    return {"message": f"Email de bienvenida enviado a {member['email']}"}

# ==================== CHECK-IN / ATTENDANCE ====================

@api_router.post("/bookings/{booking_id}/checkin")
async def checkin_booking(booking_id: str, admin: dict = Depends(get_current_admin)):
    """Mark a member as checked in for a class"""
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    if booking["status"] != "confirmed":
        raise HTTPException(status_code=400, detail="La reserva no está confirmada")
    
    await db.bookings.update_one({"id": booking_id}, {"$set": {
        "checked_in": True,
        "checked_in_at": datetime.now(timezone.utc).isoformat(),
        "checked_in_by": admin["id"]
    }})
    return {"message": "Check-in registrado"}

@api_router.post("/bookings/{booking_id}/checkout")
async def checkout_booking(booking_id: str, admin: dict = Depends(get_current_admin)):
    """Undo a check-in"""
    await db.bookings.update_one({"id": booking_id}, {"$set": {
        "checked_in": False,
        "checked_in_at": None,
        "checked_in_by": None
    }})
    return {"message": "Check-in anulado"}

@api_router.get("/attendance/schedule/{schedule_id}")
async def get_schedule_attendance(schedule_id: str, admin: dict = Depends(get_current_admin)):
    """Get attendance list for a specific class schedule"""
    schedule = await db.class_schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    
    bookings = await db.bookings.find(
        {"schedule_id": schedule_id, "status": "confirmed"},
        {"_id": 0}
    ).to_list(200)
    
    class_data = await db.classes.find_one({"id": schedule.get("class_id")}, {"_id": 0})
    
    total = len(bookings)
    checked_in = sum(1 for b in bookings if b.get("checked_in"))
    
    return {
        "schedule": schedule,
        "class": class_data,
        "bookings": bookings,
        "total_booked": total,
        "checked_in": checked_in,
        "pending": total - checked_in
    }

@api_router.get("/attendance/stats")
async def get_attendance_stats(
    gym_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get attendance statistics"""
    query = {"status": "confirmed"}
    
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    
    all_bookings = await db.bookings.find(query, {"_id": 0}).to_list(5000)
    
    total_bookings = len(all_bookings)
    total_checkins = sum(1 for b in all_bookings if b.get("checked_in"))
    
    return {
        "total_bookings": total_bookings,
        "total_checkins": total_checkins,
        "attendance_rate": round((total_checkins / total_bookings * 100), 1) if total_bookings > 0 else 0
    }

# ==================== MANUAL PAYMENTS ====================

@api_router.post("/payments/manual")
async def create_manual_payment(payment: ManualPayment, admin: dict = Depends(get_current_admin)):
    """Register a cash or card-at-reception payment"""
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    
    member = await db.members.find_one({"id": payment.member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    
    plan = await db.plans.find_one({"id": payment.plan_id}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    gym_id = member.get("gym_id")
    
    # Create transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "member_id": payment.member_id,
        "member_name": member.get("name"),
        "plan_id": payment.plan_id,
        "plan_name": plan.get("name"),
        "gym_id": gym_id,
        "amount": payment.amount,
        "currency": "eur",
        "payment_method": payment.payment_method,
        "status": "completed",
        "payment_status": "paid",
        "notes": payment.notes,
        "registered_by": admin["id"],
        "registered_by_name": admin.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    transaction.pop("_id", None)
    
    # Activate membership
    await db.memberships.update_many(
        {"member_id": payment.member_id, "status": "active"},
        {"$set": {"status": "expired"}}
    )
    
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=plan["duration_days"])
    membership = {
        "id": str(uuid.uuid4()),
        "member_id": payment.member_id,
        "plan_id": payment.plan_id,
        "gym_id": gym_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active",
        "payment_id": transaction["id"],
        "payment_method": payment.payment_method,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.memberships.insert_one(membership)
    membership.pop("_id", None)
    
    # Reactivate member if suspended
    await db.members.update_one(
        {"id": payment.member_id, "status": "suspended"},
        {"$set": {"status": "active", "suspension_reason": None, "suspended_at": None}}
    )
    
    return {"transaction": transaction, "membership": membership, "message": "Pago registrado y membresía activada"}

# ==================== ACCOUNTING ====================

@api_router.get("/accounting/report")
async def get_accounting_report(
    gym_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get accounting report with payment data"""
    query = {"payment_status": "paid"}
    
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)
    
    total_revenue = sum(t.get("amount", 0) for t in transactions)
    cash_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") == "cash")
    card_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") == "card_reception")
    stripe_total = sum(t.get("amount", 0) for t in transactions if t.get("payment_method") in (None, "stripe"))
    
    # Group by date for chart
    daily_revenue = {}
    for t in transactions:
        date_key = t.get("created_at", "")[:10]
        if date_key:
            daily_revenue[date_key] = daily_revenue.get(date_key, 0) + t.get("amount", 0)
    
    daily_chart = [{"date": k, "amount": v} for k, v in sorted(daily_revenue.items())]
    
    return {
        "transactions": transactions,
        "summary": {
            "total_revenue": total_revenue,
            "total_transactions": len(transactions),
            "cash_total": cash_total,
            "card_total": card_total,
            "stripe_total": stripe_total
        },
        "daily_chart": daily_chart
    }

@api_router.get("/accounting/pdf")
async def generate_accounting_pdf(
    gym_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Generate accounting PDF report"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # Get data
    query = {"payment_status": "paid"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    
    transactions = await db.payment_transactions.find(query, {"_id": 0}).sort("created_at", 1).to_list(5000)
    
    # Get gym name
    gym_name = "Todos los Gimnasios"
    target_gym_id = admin.get("gym_id") or gym_id
    if target_gym_id:
        gym_doc = await db.gyms.find_one({"id": target_gym_id}, {"_id": 0, "name": 1})
        gym_name = gym_doc.get("name", gym_name) if gym_doc else gym_name
    
    total = sum(t.get("amount", 0) for t in transactions)
    
    # Build PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=18, spaceAfter=6)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    
    elements = []
    elements.append(Paragraph(f"Informe de Contabilidad - {gym_name}", title_style))
    
    period = ""
    if date_from:
        period += f"Desde: {date_from} "
    if date_to:
        period += f"Hasta: {date_to}"
    if not period:
        period = "Todos los períodos"
    
    elements.append(Paragraph(period, subtitle_style))
    elements.append(Spacer(1, 10*mm))
    
    # Summary
    elements.append(Paragraph(f"<b>Total Recaudado: ${total:,.2f}</b>  |  Transacciones: {len(transactions)}", styles['Normal']))
    elements.append(Spacer(1, 8*mm))
    
    # Table
    if transactions:
        table_data = [['Fecha', 'Socio', 'Plan', 'Método', 'Monto']]
        for t in transactions:
            method_map = {"cash": "Efectivo", "card_reception": "Tarjeta", "stripe": "Stripe Online"}
            method = method_map.get(t.get("payment_method", "stripe"), "Stripe Online")
            date_str = t.get("created_at", "")[:10]
            table_data.append([
                date_str,
                t.get("member_name", "-"),
                t.get("plan_name", "-"),
                method,
                f"${t.get('amount', 0):,.2f}"
            ])
        
        col_widths = [70, 130, 100, 80, 70]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay transacciones en este período.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"contabilidad_{gym_name.replace(' ', '_')}_{date_from or 'all'}_{date_to or 'all'}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== EMAIL WITH TEMPLATES ====================

async def send_templated_email(gym_id: str, template_type: str, to_email: str, variables: dict):
    """Send an email using a gym's stored template"""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        return False
    
    # Find template
    template = None
    for t in gym.get("email_templates", []):
        if t["type"] == template_type:
            template = t
            break
    
    if not template:
        return False
    
    subject = template["subject"]
    body = template["body"]
    
    # Replace variables
    for key, value in variables.items():
        subject = subject.replace(key, str(value))
        body = body.replace(key, str(value))
    
    # Convert body to HTML (preserve line breaks)
    color = gym.get("primary_color", "#E1FF01")
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:30px;background:#09090B;color:#fff;border-radius:16px;">
        <div style="text-align:center;margin-bottom:20px;">
            <h1 style="color:{color};margin:0;font-size:24px;">{gym.get('name','GymAccess')}</h1>
        </div>
        <div style="line-height:1.6;">
            {body.replace(chr(10), '<br/>')}
        </div>
    </div>
    """
    
    try:
        await send_gym_email(gym_id, to_email, subject, html_body)
        return True
    except Exception as e:
        logger.error(f"Template email error: {e}")
        return False

# ==================== KIOSK REGISTRATION ====================

@api_router.post("/kiosk/register")
async def kiosk_register(member: MemberPublicRegister):
    """Kiosk registration - registers member and sends payment email"""
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya está registrado en este gimnasio")
    
    gym = await db.gyms.find_one({"id": member.gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    
    member_dict = {
        "id": str(uuid.uuid4()),
        "email": member.email,
        "name": member.name,
        "phone": member.phone,
        "gym_id": member.gym_id,
        "code": generate_member_code(),
        "status": "pending",
        "registered_via": "kiosk",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    while await db.members.find_one({"code": member_dict["code"]}):
        member_dict["code"] = generate_member_code()
    
    await db.members.insert_one(member_dict)
    member_dict.pop("_id", None)
    
    # Create token for payment
    token = create_jwt_token({
        "sub": member_dict["id"],
        "type": "member",
        "gym_id": member.gym_id
    })
    
    # Try sending welcome email with payment link
    email_sent = False
    if gym.get("smtp_host") and gym.get("smtp_user"):
        try:
            plan = None
            if member.plan_id:
                plan = await db.plans.find_one({"id": member.plan_id}, {"_id": 0})
            
            variables = {
                "{gym_name}": gym.get("name", ""),
                "{member_name}": member.name,
                "{member_code}": member_dict["code"],
                "{member_email}": member.email,
                "{plan_name}": plan.get("name", "") if plan else ""
            }
            email_sent = await send_templated_email(member.gym_id, "welcome", member.email, variables)
        except Exception as e:
            logger.error(f"Kiosk email error: {e}")
    
    return {
        "member": member_dict,
        "token": token,
        "email_sent": email_sent,
        "message": f"Registro exitoso. Código: {member_dict['code']}"
    }

# ==================== INIT & HEALTH ====================

@api_router.get("/")
async def root():
    return {"message": "Gym Access Control API", "version": "1.0.0"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Initialize super admin if not exists
@app.on_event("startup")
async def init_super_admin():
    existing = await db.admins.find_one({"role": "super_admin"})
    if not existing:
        admin = {
            "id": str(uuid.uuid4()),
            "email": "admin@gymaccess.com",
            "password": hash_password("admin123"),
            "name": "Super Admin",
            "role": "super_admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(admin)
        logger.info("Super admin created: admin@gymaccess.com / admin123")

# Background task: auto-suspend expired memberships every 60 minutes
async def auto_suspend_expired_memberships():
    while True:
        try:
            await asyncio.sleep(3600)  # Run every 60 minutes
            now = datetime.now(timezone.utc).isoformat()
            active_memberships = await db.memberships.find({"status": "active"}, {"_id": 0}).to_list(10000)
            suspended_count = 0
            for m in active_memberships:
                if m.get("end_date") and m["end_date"] < now:
                    await db.memberships.update_one({"id": m["id"]}, {"$set": {"status": "expired"}})
                    other_active = await db.memberships.find_one({"member_id": m["member_id"], "status": "active"})
                    if not other_active:
                        await db.members.update_one({"id": m["member_id"]}, {"$set": {
                            "status": "suspended",
                            "suspension_reason": "Membresía vencida (automático)",
                            "suspended_at": now
                        }})
                        suspended_count += 1
            if suspended_count > 0:
                logger.info(f"Auto-suspended {suspended_count} members with expired memberships")
        except Exception as e:
            logger.error(f"Error in auto-suspend task: {e}")

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(auto_suspend_expired_memberships())
