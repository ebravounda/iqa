from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from database import db
from auth import get_current_admin, security, decode_jwt_token

router = APIRouter(prefix="/api")

# ==================== Trainer: Create/Manage Routines ====================

@router.post("/routines")
async def create_routine(request: Request, admin: dict = Depends(get_current_admin)):
    body = await request.json()
    gym_id = body.get("gym_id") or admin.get("gym_id")
    if not gym_id:
        raise HTTPException(status_code=400, detail="gym_id requerido")
    routine = {
        "id": str(uuid.uuid4()),
        "gym_id": gym_id,
        "name": body.get("name", "Sin nombre"),
        "description": body.get("description", ""),
        "trainer_id": admin["id"],
        "trainer_name": admin.get("name", "Trainer"),
        "member_id": body.get("member_id"),
        "days": body.get("days", []),
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.routines.insert_one(routine)
    routine.pop("_id", None)
    return routine

@router.get("/routines")
async def get_routines(
    gym_id: Optional[str] = None, member_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    target_gym = gym_id if admin["role"] == "super_admin" and gym_id else admin.get("gym_id")
    query = {}
    if target_gym:
        query["gym_id"] = target_gym
    if member_id:
        query["member_id"] = member_id
    if admin["role"] == "trainer":
        query["trainer_id"] = admin["id"]
    routines = await db.routines.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return routines

@router.put("/routines/{routine_id}")
async def update_routine(routine_id: str, request: Request, admin: dict = Depends(get_current_admin)):
    body = await request.json()
    routine = await db.routines.find_one({"id": routine_id}, {"_id": 0})
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    updates = {k: v for k, v in body.items() if k in ["name", "description", "days", "active", "member_id"]}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.routines.update_one({"id": routine_id}, {"$set": updates})
    updated = await db.routines.find_one({"id": routine_id}, {"_id": 0})
    return updated

@router.delete("/routines/{routine_id}")
async def delete_routine(routine_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.routines.delete_one({"id": routine_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")
    return {"message": "Rutina eliminada"}

# ==================== Member: View My Routines ====================

@router.get("/routines/me")
async def get_my_routines(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    routines = await db.routines.find(
        {"member_id": member_id, "active": True}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return routines

# ==================== Routine Progress Tracking ====================

@router.post("/routines/{routine_id}/log")
async def log_routine_progress(routine_id: str, request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    body = await request.json()
    log = {
        "id": str(uuid.uuid4()),
        "routine_id": routine_id,
        "member_id": member_id,
        "day_index": body.get("day_index", 0),
        "exercises_completed": body.get("exercises_completed", []),
        "notes": body.get("notes", ""),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.routine_logs.insert_one(log)
    log.pop("_id", None)
    return log

@router.get("/routines/{routine_id}/logs")
async def get_routine_logs(routine_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    logs = await db.routine_logs.find(
        {"routine_id": routine_id, "member_id": member_id}, {"_id": 0}
    ).sort("completed_at", -1).to_list(100)
    return logs
