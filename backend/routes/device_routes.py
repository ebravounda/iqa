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
async def get_devices(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede ver dispositivos")
    query = {}
    if gym_id:
        query["gym_id"] = gym_id
    devices = await db.devices.find(query, {"_id": 0}).to_list(100)
    return devices

@router.delete("/devices/{device_id}")
async def delete_device(device_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super_admin puede eliminar dispositivos")
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.devices.delete_one({"id": device_id})
    return {"message": "Device deleted"}

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
