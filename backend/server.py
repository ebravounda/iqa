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

class GymUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    qr_refresh_seconds: Optional[int] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "gym_admin"  # super_admin, gym_admin
    gym_id: Optional[str] = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class MemberCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    gym_id: str

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[str] = None  # active, blocked, pending

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
    return admin

def generate_qr_data(member_id: str, gym_id: str, timestamp: int) -> str:
    """Generate encrypted QR data"""
    data = f"{member_id}|{gym_id}|{timestamp}"
    signature = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{data}|{signature}".encode()).decode()

def validate_qr_data(qr_code: str, max_age_seconds: int = 15) -> dict:
    """Validate QR code and return member info"""
    try:
        decoded = base64.urlsafe_b64decode(qr_code.encode()).decode()
        parts = decoded.split('|')
        if len(parts) != 4:
            return {"valid": False, "reason": "Invalid QR format"}
        
        member_id, gym_id, timestamp_str, signature = parts
        timestamp = int(timestamp_str)
        
        # Verify signature
        data = f"{member_id}|{gym_id}|{timestamp}"
        expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
        if signature != expected_sig:
            return {"valid": False, "reason": "Invalid signature"}
        
        # Check expiration
        now = int(datetime.now(timezone.utc).timestamp())
        if now - timestamp > max_age_seconds:
            return {"valid": False, "reason": "QR expired"}
        
        return {"valid": True, "member_id": member_id, "gym_id": gym_id}
    except Exception as e:
        logger.error(f"QR validation error: {e}")
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
    return gym_dict

@api_router.get("/gyms")
async def get_gyms(admin: dict = Depends(get_current_admin)):
    if admin["role"] == "super_admin":
        gyms = await db.gyms.find({}, {"_id": 0}).to_list(100)
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
    update_data = {k: v for k, v in gym_update.model_dump().items() if v is not None}
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
async def register_member_public(member: MemberCreate):
    """Public registration for members"""
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    gym = await db.gyms.find_one({"id": member.gym_id})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    
    member_dict = member.model_dump()
    member_dict["id"] = str(uuid.uuid4())
    member_dict["code"] = generate_member_code()
    member_dict["status"] = "pending"  # Needs admin approval
    member_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    
    while await db.members.find_one({"code": member_dict["code"]}):
        member_dict["code"] = generate_member_code()
    
    await db.members.insert_one(member_dict)
    member_dict.pop("_id", None)
    return member_dict

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
    return plans

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

# ==================== QR ROUTES ====================

@api_router.get("/qr/generate")
async def generate_qr(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    gym_id = payload.get("gym_id")
    
    # Get gym config for refresh time
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    refresh_seconds = gym.get("qr_refresh_seconds", 10) if gym else 10
    
    timestamp = int(datetime.now(timezone.utc).timestamp())
    qr_data = generate_qr_data(member_id, gym_id, timestamp)
    
    return {
        "qr_code": qr_data,
        "expires_at": timestamp + refresh_seconds,
        "refresh_seconds": refresh_seconds
    }

# ==================== ACCESS ROUTES ====================

@api_router.post("/access/validate")
async def validate_access(validation: AccessValidation):
    """Validate QR code from Raspberry Pi"""
    # Verify gym token
    gym = await db.gyms.find_one({"api_token": validation.gym_token}, {"_id": 0})
    if not gym:
        return {"valid": False, "reason": "Invalid gym token"}
    
    # Validate QR
    max_age = gym.get("qr_refresh_seconds", 10) + 5  # Small grace period
    result = validate_qr_data(validation.qr_code, max_age)
    
    if not result["valid"]:
        return result
    
    if result["gym_id"] != gym["id"]:
        return {"valid": False, "reason": "QR code not for this gym"}
    
    # Check member
    member = await db.members.find_one({"id": result["member_id"]}, {"_id": 0})
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
    
    # Log access
    access_log = {
        "id": str(uuid.uuid4()),
        "member_id": member["id"],
        "member_name": member["name"],
        "member_code": member["code"],
        "gym_id": gym["id"],
        "direction": validation.direction,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.access_logs.insert_one(access_log)
    
    return {
        "valid": True,
        "member_name": member["name"],
        "member_code": member["code"],
        "direction": validation.direction
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

# ==================== DEVICE ROUTES ====================

@api_router.post("/devices")
async def create_device(device: DeviceCreate, admin: dict = Depends(get_current_admin)):
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
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    
    devices = await db.devices.find(query, {"_id": 0}).to_list(100)
    return devices

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
    
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    origin_url = request.headers.get("origin", host_url)
    success_url = f"{origin_url}/app/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/app/membership"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(plan["price"]),
        currency="usd",
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
        "currency": "usd",
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
    
    api_key = os.environ.get("STRIPE_API_KEY")
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
    
    return {
        "total_members": total_members,
        "active_members": active_members,
        "pending_members": pending_members,
        "gyms_count": gyms_count,
        "month_revenue": month_revenue,
        **access_stats
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

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
