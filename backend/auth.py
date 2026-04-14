from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from typing import List
import bcrypt
import os

from database import db

JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret_change_me')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

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
    if payload.get("impersonating"):
        admin = dict(admin)
        admin["role"] = payload.get("role", admin.get("role"))
        admin["gym_id"] = payload.get("gym_id")
        admin["impersonating"] = True
        admin["original_role"] = payload.get("original_role")
    return admin

def check_role(admin: dict, allowed_roles: List[str], gym_id: str = None):
    if admin["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Access denied. Required roles: {allowed_roles}")
    if gym_id and admin["role"] != "super_admin" and admin.get("gym_id") != gym_id:
        raise HTTPException(status_code=403, detail="Access denied to this gym")

# Permission constants for gym_manager
DEFAULT_MANAGER_PERMISSIONS = [
    "members_view",
    "members_create",
    "members_edit",
    "payments_register",
    "pos_sell",
    "access_view",
    "classes_manage",
]

ALL_MANAGER_PERMISSIONS = [
    "members_view",
    "members_create",
    "members_edit",
    "members_delete",
    "members_suspend",
    "membership_edit",
    "payments_register",
    "pos_sell",
    "pos_products",
    "access_view",
    "classes_manage",
    "data_export",
    "notifications_send",
]

def check_permission(admin: dict, permission: str):
    """Check if a gym_manager has a specific permission. Admins and super_admins bypass."""
    if admin["role"] in ("super_admin", "gym_admin"):
        return
    perms = admin.get("permissions", DEFAULT_MANAGER_PERMISSIONS)
    if permission not in perms:
        raise HTTPException(status_code=403, detail=f"No tienes permiso para: {permission}")
