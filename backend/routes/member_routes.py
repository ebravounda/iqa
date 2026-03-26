from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging

from database import db
from auth import get_current_admin, create_jwt_token, check_role
from models import MemberCreate, MemberPublicRegister, MemberUpdate
from qr_utils import generate_member_code

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.post("/members")
async def create_member(member: MemberCreate, admin: dict = Depends(get_current_admin)):
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered in this gym")
    member_dict = member.model_dump()
    member_dict["id"] = str(uuid.uuid4())
    member_dict["code"] = generate_member_code()
    member_dict["status"] = "active"
    member_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    while await db.members.find_one({"code": member_dict["code"]}):
        member_dict["code"] = generate_member_code()
    await db.members.insert_one(member_dict)
    member_dict.pop("_id", None)
    return member_dict

@router.post("/members/register")
async def register_member_public(member: MemberPublicRegister):
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya esta registrado en este gimnasio")
    gym = await db.gyms.find_one({"id": member.gym_id})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if gym.get("status") == "suspended":
        raise HTTPException(status_code=403, detail="Este gimnasio esta suspendido")
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
    token = create_jwt_token({"sub": member_dict["id"], "type": "member", "gym_id": member.gym_id})
    return {
        "member": member_dict,
        "membership": membership_data,
        "token": token,
        "message": f"Registro exitoso. Tu codigo de acceso es: {member_dict['code']}"
    }

@router.get("/members")
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

@router.get("/members/{member_id}")
async def get_member(member_id: str, admin: dict = Depends(get_current_admin)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@router.put("/members/{member_id}")
async def update_member(member_id: str, member_update: MemberUpdate, admin: dict = Depends(get_current_admin)):
    update_data = {k: v for k, v in member_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    return member

@router.post("/members/{member_id}/approve")
async def approve_member(member_id: str, admin: dict = Depends(get_current_admin)):
    await db.members.update_one({"id": member_id}, {"$set": {"status": "active"}})
    return {"message": "Member approved"}

@router.post("/members/{member_id}/block")
async def block_member(member_id: str, admin: dict = Depends(get_current_admin)):
    await db.members.update_one({"id": member_id}, {"$set": {"status": "blocked"}})
    return {"message": "Member blocked"}

@router.post("/members/{member_id}/suspend")
async def suspend_member(member_id: str, body: dict = {}, admin: dict = Depends(get_current_admin)):
    reason = body.get("reason", "Sin motivo especificado") if isinstance(body, dict) else "Sin motivo especificado"
    await db.members.update_one({"id": member_id}, {"$set": {
        "status": "suspended",
        "suspension_reason": reason,
        "suspended_at": datetime.now(timezone.utc).isoformat(),
        "suspended_by": admin.get("name", admin.get("email", ""))
    }})
    return {"message": "Member suspended", "reason": reason}

@router.delete("/members/{member_id}")
async def delete_member(member_id: str, admin: dict = Depends(get_current_admin)):
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.members.delete_one({"id": member_id})
    await db.memberships.delete_many({"member_id": member_id})
    await db.bookings.delete_many({"member_id": member_id})
    await db.guests.delete_many({"member_id": member_id})
    await db.access_logs.delete_many({"member_id": member_id})
    return {"message": "Member deleted"}

@router.post("/members/check-expired-memberships")
async def check_expired_memberships(admin: dict = Depends(get_current_admin)):
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
                    "suspension_reason": "Membresia vencida",
                    "suspended_at": now
                }})
                suspended_count += 1
    return {"message": f"{suspended_count} members suspended due to expired memberships"}

@router.put("/members/{member_id}/guest-permission")
async def update_guest_permission(
    member_id: str, 
    can_bring_guests: bool,
    max_guests_per_month: int = 2,
    admin: dict = Depends(get_current_admin)
):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"can_bring_guests": can_bring_guests, "max_guests_per_month": max_guests_per_month}}
    )
    return {"message": "Guest permission updated"}
