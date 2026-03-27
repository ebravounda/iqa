from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
import uuid

from database import db
from auth import hash_password

router = APIRouter(prefix="/api")

DEMO_GYM_ID = "demo-gym-001"
DEMO_EMAIL = "demo@ingresoqr.com"
DEMO_PASSWORD = "demo2024"

async def ensure_demo_data():
    gym = await db.gyms.find_one({"id": DEMO_GYM_ID})
    if gym:
        return
    now = datetime.now(timezone.utc).isoformat()
    gym = {
        "id": DEMO_GYM_ID, "name": "GymDemo IngresoQR", "address": "Av. Demo 123, Madrid",
        "phone": "+34 600 123 456", "email": "demo@gimnasio.com",
        "primary_color": "#E1FF01", "qr_refresh_seconds": 10, "max_members": 100,
        "api_token": "demo-token-001", "status": "active", "qr_mode": "dynamic",
        "created_at": now,
    }
    await db.gyms.insert_one(gym)
    admin = {
        "id": "demo-admin-001", "email": DEMO_EMAIL, "password": hash_password(DEMO_PASSWORD),
        "name": "Admin Demo", "role": "gym_admin", "gym_id": DEMO_GYM_ID,
        "created_at": now, "is_demo": True,
    }
    await db.admins.insert_one(admin)
    plans = [
        {"id": "demo-plan-1", "gym_id": DEMO_GYM_ID, "name": "Plan Mensual", "price": 29.99, "duration_days": 30, "access_type": "unlimited", "active": True, "created_at": now},
        {"id": "demo-plan-2", "gym_id": DEMO_GYM_ID, "name": "Plan Trimestral", "price": 74.99, "duration_days": 90, "access_type": "unlimited", "active": True, "created_at": now},
        {"id": "demo-plan-3", "gym_id": DEMO_GYM_ID, "name": "Plan Anual", "price": 249.99, "duration_days": 365, "access_type": "unlimited", "active": True, "created_at": now},
    ]
    for p in plans:
        await db.plans.insert_one(p)
    members_data = [
        {"name": "Carlos Garcia", "email": "carlos@demo.com", "code": "DEMO01", "phone": "+34 611 111 111", "gender": "male"},
        {"name": "Maria Lopez", "email": "maria@demo.com", "code": "DEMO02", "phone": "+34 622 222 222", "gender": "female"},
        {"name": "Juan Martinez", "email": "juan@demo.com", "code": "DEMO03", "phone": "+34 633 333 333", "gender": "male"},
        {"name": "Ana Rodriguez", "email": "ana@demo.com", "code": "DEMO04", "phone": "+34 644 444 444", "gender": "female"},
        {"name": "Pedro Sanchez", "email": "pedro@demo.com", "code": "DEMO05", "phone": "+34 655 555 555", "gender": "male"},
    ]
    from datetime import timedelta
    for i, m in enumerate(members_data):
        member = {
            **m, "id": f"demo-member-{i+1}", "gym_id": DEMO_GYM_ID, "status": "active",
            "created_at": now, "is_demo": True,
        }
        await db.members.insert_one(member)
        membership = {
            "id": f"demo-ms-{i+1}", "member_id": member["id"], "plan_id": plans[i % 3]["id"],
            "gym_id": DEMO_GYM_ID, "start_date": now,
            "end_date": (datetime.now(timezone.utc) + timedelta(days=30 * (i+1))).isoformat(),
            "status": "active", "payment_method": "demo", "amount_paid": plans[i % 3]["price"],
            "created_at": now,
        }
        await db.memberships.insert_one(membership)
    import random
    for day_offset in range(30):
        day = datetime.now(timezone.utc) - timedelta(days=day_offset)
        num_visits = random.randint(2, 5)
        for j in range(num_visits):
            member_idx = random.randint(0, 4)
            hour = random.randint(6, 22)
            ts = day.replace(hour=hour, minute=random.randint(0, 59))
            log = {
                "id": str(uuid.uuid4()), "member_id": f"demo-member-{member_idx+1}",
                "member_name": members_data[member_idx]["name"],
                "member_code": members_data[member_idx]["code"],
                "gym_id": DEMO_GYM_ID, "direction": "entrada",
                "timestamp": ts.isoformat(),
            }
            await db.access_logs.insert_one(log)

@router.post("/demo/login")
async def demo_login():
    await ensure_demo_data()
    from auth import create_jwt_token
    admin = await db.admins.find_one({"email": DEMO_EMAIL}, {"_id": 0, "password": 0})
    if not admin:
        raise HTTPException(status_code=500, detail="Error al crear demo")
    token = create_jwt_token({"sub": admin["id"], "role": admin["role"], "gym_id": admin.get("gym_id")})
    return {"admin": admin, "token": token, "is_demo": True}

@router.post("/demo/cleanup")
async def demo_cleanup():
    await db.gyms.delete_many({"id": DEMO_GYM_ID})
    await db.admins.delete_many({"is_demo": True})
    await db.members.delete_many({"is_demo": True})
    await db.memberships.delete_many({"gym_id": DEMO_GYM_ID})
    await db.access_logs.delete_many({"gym_id": DEMO_GYM_ID})
    await db.plans.delete_many({"gym_id": DEMO_GYM_ID})
    await db.routines.delete_many({"gym_id": DEMO_GYM_ID})
    await db.notifications.delete_many({"gym_id": DEMO_GYM_ID})
    await db.classes.delete_many({"gym_id": DEMO_GYM_ID})
    await db.devices.delete_many({"gym_id": DEMO_GYM_ID})
    return {"message": "Datos demo eliminados"}
