from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

from database import db
from auth import get_current_admin, check_role, security, decode_jwt_token, check_permission
from models import NotificationCreate, GuestCreate
from qr_utils import generate_member_code, generate_qr_data

router = APIRouter(prefix="/api")

# ==================== NOTIFICATIONS ====================

@router.post("/notifications")
async def create_notification(notification: NotificationCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"], notification.gym_id)
    check_permission(admin, "notifications_send")
    notification_dict = {
        "id": str(uuid.uuid4()), "gym_id": notification.gym_id,
        "title": notification.title, "message": notification.message,
        "notification_type": notification.notification_type, "target": notification.target,
        "created_by": admin["id"], "created_at": datetime.now(timezone.utc).isoformat(),
        "read_by": []
    }
    await db.notifications.insert_one(notification_dict)
    notification_dict.pop("_id", None)
    return notification_dict

@router.get("/notifications")
async def get_notifications(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notifications

@router.get("/notifications/member")
async def get_member_notifications(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    gym_id = payload.get("gym_id")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        return []
    query = {"gym_id": gym_id}
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    for n in notifications:
        n["is_read"] = member_id in n.get("read_by", [])
    return notifications

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    await db.notifications.update_one({"id": notification_id}, {"$addToSet": {"read_by": member_id}})
    return {"message": "Marked as read"}

@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    await db.notifications.delete_one({"id": notification_id})
    return {"message": "Notification deleted"}

# ==================== GUESTS ====================

@router.post("/guests")
async def create_guest_pass(guest: GuestCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if not member.get("can_bring_guests", False):
        raise HTTPException(status_code=403, detail="No tienes permiso para traer invitados. Consulta con administracion.")
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    guests_this_month = await db.guests.count_documents({"invited_by": member_id, "created_at": {"$gte": month_start.isoformat()}})
    max_guests = member.get("max_guests_per_month", 2)
    if guests_this_month >= max_guests:
        raise HTTPException(status_code=400, detail=f"Has alcanzado el limite de {max_guests} invitados este mes")
    guest_code = "G" + generate_member_code()
    max_valid_days = member.get("guest_valid_days", 1)
    requested_days = min(guest.valid_days, max_valid_days) if guest.valid_days else max_valid_days
    valid_until = datetime.now(timezone.utc) + timedelta(days=requested_days)
    guest_dict = {
        "id": str(uuid.uuid4()), "code": guest_code, "name": guest.name,
        "phone": guest.phone, "invited_by": member_id, "invited_by_name": member["name"],
        "gym_id": member["gym_id"], "valid_until": valid_until.isoformat(),
        "valid_days": requested_days, "status": "active", "accesses": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.guests.insert_one(guest_dict)
    guest_dict.pop("_id", None)
    return guest_dict

@router.get("/guests/member")
async def get_member_guests(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    guests = await db.guests.find({"invited_by": member_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    now = datetime.now(timezone.utc)
    for g in guests:
        valid_until = datetime.fromisoformat(g["valid_until"].replace('Z', '+00:00'))
        if valid_until < now and g["status"] == "active":
            g["status"] = "expired"
            await db.guests.update_one({"id": g["id"]}, {"$set": {"status": "expired"}})
    return guests

@router.get("/guests")
async def get_all_guests(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    guests = await db.guests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return guests

@router.get("/guests/{guest_code}/qr")
async def get_guest_qr(guest_code: str):
    guest = await db.guests.find_one({"code": guest_code.upper()}, {"_id": 0})
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    valid_until = datetime.fromisoformat(guest["valid_until"].replace('Z', '+00:00'))
    if valid_until < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Guest pass expired")
    if guest["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Guest pass is {guest['status']}")
    timestamp = int(datetime.now(timezone.utc).timestamp())
    qr_data = generate_qr_data(f"GUEST:{guest['id']}", guest["gym_id"], timestamp)
    gym = await db.gyms.find_one({"id": guest["gym_id"]}, {"_id": 0})
    refresh_seconds = gym.get("qr_refresh_seconds", 10) if gym else 10
    return {"qr_code": qr_data, "guest": guest, "expires_at": timestamp + refresh_seconds, "refresh_seconds": refresh_seconds}

@router.post("/access/validate/guest")
async def validate_guest_access(from_models: None = None):
    # Guest access is handled in the main /access/validate endpoint
    return {"message": "Use /access/validate for all access validation"}
