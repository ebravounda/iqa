from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from database import db
from auth import get_current_admin, check_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# --- Member Device Registration (called from member login) ---
async def register_member_device(member_id: str, gym_id: str, device_fingerprint: str, user_agent: str):
    """Register a device for a member. Returns (success, error_message)."""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    max_devices = gym.get("max_devices_per_member", 2) if gym else 2

    existing = await db.member_devices.find_one({
        "member_id": member_id, "device_fingerprint": device_fingerprint, "active": True
    })
    if existing:
        await db.member_devices.update_one(
            {"id": existing["id"]},
            {"$set": {"last_active": datetime.now(timezone.utc).isoformat(), "user_agent": user_agent}}
        )
        return True, None

    active_count = await db.member_devices.count_documents({"member_id": member_id, "active": True})
    if active_count >= max_devices:
        return False, f"Limite de dispositivos alcanzado ({max_devices}). Contacta a recepcion para desactivar uno."

    device = {
        "id": str(uuid.uuid4()),
        "member_id": member_id,
        "gym_id": gym_id,
        "device_fingerprint": device_fingerprint,
        "user_agent": user_agent,
        "device_name": _parse_device_name(user_agent),
        "active": True,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "last_active": datetime.now(timezone.utc).isoformat()
    }
    await db.member_devices.insert_one(device)
    return True, None

def _parse_device_name(ua: str) -> str:
    ua_lower = ua.lower()
    if "iphone" in ua_lower:
        return "iPhone"
    if "ipad" in ua_lower:
        return "iPad"
    if "android" in ua_lower:
        if "samsung" in ua_lower:
            return "Samsung"
        if "huawei" in ua_lower:
            return "Huawei"
        if "xiaomi" in ua_lower or "redmi" in ua_lower:
            return "Xiaomi"
        return "Android"
    if "windows" in ua_lower:
        return "Windows PC"
    if "macintosh" in ua_lower:
        return "Mac"
    if "linux" in ua_lower:
        return "Linux PC"
    return "Desconocido"

# --- Admin Endpoints ---

@router.get("/member-devices/{member_id}")
async def get_member_devices(member_id: str, admin: dict = Depends(get_current_admin)):
    devices = await db.member_devices.find(
        {"member_id": member_id}, {"_id": 0}
    ).sort("last_active", -1).to_list(50)
    return devices

@router.put("/member-devices/{device_id}/deactivate")
async def deactivate_device(device_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.member_devices.update_one(
        {"id": device_id},
        {"$set": {"active": False, "deactivated_at": datetime.now(timezone.utc).isoformat(), "deactivated_by": admin["id"]}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return {"message": "Dispositivo desactivado"}

@router.put("/member-devices/member/{member_id}/deactivate-all")
async def deactivate_all_devices(member_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.member_devices.update_many(
        {"member_id": member_id, "active": True},
        {"$set": {"active": False, "deactivated_at": datetime.now(timezone.utc).isoformat(), "deactivated_by": admin["id"]}}
    )
    return {"message": f"{result.modified_count} dispositivos desactivados"}

@router.put("/gyms/{gym_id}/max-devices")
async def update_max_devices(gym_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    max_devices = body.get("max_devices_per_member", 2)
    if max_devices < 1 or max_devices > 10:
        raise HTTPException(status_code=400, detail="El limite debe estar entre 1 y 10")
    await db.gyms.update_one({"id": gym_id}, {"$set": {"max_devices_per_member": max_devices}})
    return {"message": f"Limite actualizado a {max_devices} dispositivos", "max_devices_per_member": max_devices}

# --- Member Visit Statistics ---

@router.get("/member-stats/visits")
async def get_member_visit_stats(credentials=Depends(get_current_admin)):
    """This is used from member context - we override with a separate member endpoint below."""
    pass

@router.get("/stats/member-visits/{member_id}")
async def get_member_visit_stats_admin(member_id: str, admin: dict = Depends(get_current_admin)):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    total = await db.access_logs.count_documents({"member_id": member_id, "direction": "entrada"})
    this_month = await db.access_logs.count_documents({"member_id": member_id, "direction": "entrada", "timestamp": {"$gte": month_start}})
    this_week = await db.access_logs.count_documents({"member_id": member_id, "direction": "entrada", "timestamp": {"$gte": week_start}})

    # Monthly breakdown for last 6 months
    monthly = []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        m_start = datetime(y, m, 1, tzinfo=timezone.utc).isoformat()
        next_m = m + 1
        next_y = y
        if next_m > 12:
            next_m = 1
            next_y += 1
        m_end = datetime(next_y, next_m, 1, tzinfo=timezone.utc).isoformat()
        count = await db.access_logs.count_documents({
            "member_id": member_id, "direction": "entrada",
            "timestamp": {"$gte": m_start, "$lt": m_end}
        })
        month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        monthly.append({"month": month_names[m - 1], "visits": count})

    return {
        "total_visits": total,
        "this_month": this_month,
        "this_week": this_week,
        "monthly": monthly
    }
