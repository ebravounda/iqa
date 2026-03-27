from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

from database import db
from auth import get_current_admin
from models import PlanCreate, MembershipCreate

router = APIRouter(prefix="/api")

@router.post("/plans")
async def create_plan(plan: PlanCreate, admin: dict = Depends(get_current_admin)):
    plan_dict = plan.model_dump()
    plan_dict["id"] = str(uuid.uuid4())
    plan_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    plan_dict["active"] = True
    await db.plans.insert_one(plan_dict)
    plan_dict.pop("_id", None)
    return plan_dict

@router.get("/plans")
async def get_plans(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"active": True}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    plans = await db.plans.find(query, {"_id": 0}).to_list(100)
    return plans

@router.get("/plans/public/{gym_id}")
async def get_plans_public(gym_id: str):
    plans = await db.plans.find({"gym_id": gym_id, "active": True}, {"_id": 0}).to_list(100)
    if not plans:
        plans = await db.plans.find({"gym_id": gym_id}, {"_id": 0}).to_list(100)
    return plans

@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, admin: dict = Depends(get_current_admin)):
    await db.plans.update_one({"id": plan_id}, {"$set": {"active": False}})
    return {"message": "Plan deleted"}

@router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, plan_update: dict, admin: dict = Depends(get_current_admin)):
    allowed_fields = {"name", "description", "price", "duration_days", "access_type"}
    update_data = {k: v for k, v in plan_update.items() if k in allowed_fields and v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.plans.update_one({"id": plan_id}, {"$set": update_data})
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    return plan

@router.post("/memberships")
async def create_membership(membership: MembershipCreate, admin: dict = Depends(get_current_admin)):
    plan = await db.plans.find_one({"id": membership.plan_id})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
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

@router.get("/memberships")
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

@router.get("/memberships/expiring")
async def get_expiring_memberships(days: int = 10, admin: dict = Depends(get_current_admin)):
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
