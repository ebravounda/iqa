from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

from database import db
from auth import get_current_admin

router = APIRouter(prefix="/api")

# ==================== DEVICE HEARTBEAT (called by Raspberry Pi) ====================

@router.post("/devices/{device_id}/heartbeat")
async def device_heartbeat(device_id: str, request: Request):
    body = await request.json()
    gym_token = body.get("gym_token")
    if not gym_token:
        raise HTTPException(status_code=401, detail="Token requerido")
    gym = await db.gyms.find_one({"api_token": gym_token}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=401, detail="Token invalido")
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    now = datetime.now(timezone.utc).isoformat()
    update = {
        "status": "online",
        "last_ping": now,
        "ip_address": body.get("ip_address", ""),
        "local_ip": body.get("local_ip", ""),
        "cpu_temp": body.get("cpu_temp"),
        "cpu_usage": body.get("cpu_usage"),
        "memory_usage": body.get("memory_usage"),
        "uptime": body.get("uptime"),
        "software_version": body.get("software_version", "1.0"),
        "wifi_signal": body.get("wifi_signal"),
    }
    await db.devices.update_one({"id": device_id}, {"$set": update})
    pending_cmd = await db.device_commands.find_one(
        {"device_id": device_id, "status": "pending"}, {"_id": 0}
    )
    if pending_cmd:
        await db.device_commands.update_one(
            {"id": pending_cmd["id"]}, {"$set": {"status": "delivered", "delivered_at": now}}
        )
        return {"status": "ok", "command": pending_cmd.get("command")}
    return {"status": "ok", "command": None}

# ==================== REMOTE COMMANDS (Admin) ====================

@router.post("/devices/{device_id}/command")
async def send_device_command(device_id: str, request: Request, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    body = await request.json()
    command = body.get("command")
    if command not in ["reboot", "update", "restart_service"]:
        raise HTTPException(status_code=400, detail="Comando no valido. Usa: reboot, update, restart_service")
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    cmd = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "command": command,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin.get("email", admin["id"]),
    }
    await db.device_commands.insert_one(cmd)
    cmd.pop("_id", None)
    return {"message": f"Comando '{command}' enviado", "command": cmd}

@router.get("/devices/{device_id}/commands")
async def get_device_commands(device_id: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    commands = await db.device_commands.find(
        {"device_id": device_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return commands

@router.get("/devices/status")
async def get_devices_status(admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    devices = await db.devices.find({}, {"_id": 0}).to_list(100)
    now = datetime.now(timezone.utc)
    for d in devices:
        if d.get("last_ping"):
            try:
                last = datetime.fromisoformat(d["last_ping"].replace("Z", "+00:00"))
                diff = (now - last).total_seconds()
                d["computed_status"] = "online" if diff < 120 else "offline"
                d["seconds_since_ping"] = int(diff)
            except:
                d["computed_status"] = "offline"
                d["seconds_since_ping"] = None
        else:
            d["computed_status"] = "offline"
            d["seconds_since_ping"] = None
        gym = await db.gyms.find_one({"id": d.get("gym_id")}, {"_id": 0, "name": 1})
        d["gym_name"] = gym.get("name", "Desconocido") if gym else "Desconocido"
    return devices
