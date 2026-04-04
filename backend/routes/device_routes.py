from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid

from database import db
from auth import get_current_admin
from models import DeviceCreate

router = APIRouter(prefix="/api")

@router.post("/devices")
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

@router.get("/devices")
async def get_devices(gym_id: Optional[str] = None, include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede ver dispositivos")
    query = {}
    if gym_id:
        query["gym_id"] = gym_id
    if not include_inactive:
        query["active"] = {"$ne": False}
    devices = await db.devices.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    # Also return last 8 inactive devices
    inactive_query = {**({} if not gym_id else {"gym_id": gym_id}), "active": False}
    inactive = await db.devices.find(inactive_query, {"_id": 0}).sort("deactivated_at", -1).to_list(8)
    return {"active": [d for d in devices if d.get("active") is not False], "inactive": inactive}

@router.delete("/devices/{device_id}")
async def delete_device(device_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede eliminar dispositivos")
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.get("active") is False:
        # Already inactive, delete permanently
        await db.devices.delete_one({"id": device_id})
        return {"message": "Dispositivo eliminado permanentemente"}
    # Soft-delete: mark as inactive
    await db.devices.update_one({"id": device_id}, {"$set": {"active": False, "deactivated_at": datetime.now(timezone.utc).isoformat()}})
    # Keep only last 8 inactive per gym
    gym_id = device.get("gym_id")
    if gym_id:
        inactive = await db.devices.find({"gym_id": gym_id, "active": False}, {"_id": 0, "id": 1}).sort("deactivated_at", -1).to_list(100)
        if len(inactive) > 8:
            old_ids = [d["id"] for d in inactive[8:]]
            await db.devices.delete_many({"id": {"$in": old_ids}})
    return {"message": "Dispositivo desactivado"}

@router.post("/devices/{device_id}/ping")
async def ping_device(device_id: str, gym_token: str):
    gym = await db.gyms.find_one({"api_token": gym_token})
    if not gym:
        raise HTTPException(status_code=401, detail="Invalid token")
    await db.devices.update_one(
        {"id": device_id},
        {"$set": {"status": "online", "last_ping": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok"}
