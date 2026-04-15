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
        try:
            end_str = m.get("end_date", "")
            if not end_str:
                continue
            if "T" in end_str or "+" in end_str:
                end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            else:
                end_date = datetime.strptime(end_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if now <= end_date <= future:
                member = await db.members.find_one({"id": m["member_id"]}, {"_id": 0})
                m["member"] = member
                expiring.append(m)
        except Exception:
            continue
    return expiring


@router.post("/plans/import")
async def import_plans(data: dict, admin: dict = Depends(get_current_admin)):
    """Import plans from scraped IsMyGym data"""
    from auth import check_role
    check_role(admin, ["super_admin"])

    gym_id = data.get("gym_id")
    plans_data = data.get("plans", [])

    if not gym_id:
        raise HTTPException(status_code=400, detail="gym_id requerido")
    if not plans_data:
        raise HTTPException(status_code=400, detail="No hay planes para importar")

    gym = await db.gyms.find_one({"id": gym_id})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")

    imported = 0
    skipped = 0

    for p in plans_data:
        name = p.get("name", "").strip()
        if not name:
            continue

        existing = await db.plans.find_one({"gym_id": gym_id, "name": name, "active": True})
        if existing:
            skipped += 1
            continue

        # Determine duration from tipo_cuota
        tipo = p.get("tipo_cuota", "mensual").lower()
        if "trimestral" in tipo or "trimestre" in name.lower():
            duration_days = 90
        elif "bimensual" in tipo:
            duration_days = 60
        elif "cuatrimestral" in tipo:
            duration_days = 120
        elif "anual" in tipo:
            duration_days = 365
        elif "10 sesiones" in name.lower() or "bono" in name.lower():
            duration_days = 90
        else:
            duration_days = 30

        price = 0.0
        cuota_str = str(p.get("price", "0")).replace("€", "").replace(",", ".").strip()
        try:
            price = float(cuota_str)
        except ValueError:
            pass

        plan_dict = {
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "name": name,
            "description": p.get("description", ""),
            "price": price,
            "duration_days": duration_days,
            "access_type": "unlimited",
            "active": True,
            "imported": True,
            "import_source": "ismygym",
            "ismygym_id": p.get("ismygym_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await db.plans.insert_one(plan_dict)
        plan_dict.pop("_id", None)
        imported += 1

    return {
        "success": True,
        "imported": imported,
        "skipped": skipped,
        "message": f"Importacion completada: {imported} planes importados, {skipped} omitidos (duplicados)"
    }
