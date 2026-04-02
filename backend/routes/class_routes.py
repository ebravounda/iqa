from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List
import uuid

from database import db
from auth import get_current_admin, check_role, security, decode_jwt_token, check_permission, DEFAULT_MANAGER_PERMISSIONS, ALL_MANAGER_PERMISSIONS
from models import ClassCreate, ClassUpdate, ClassScheduleCreate, BookingCreate, TrainerCreate, AdminCreate
from auth import hash_password

router = APIRouter(prefix="/api")

def calculate_end_time(start_time: str, duration_minutes: int) -> str:
    hours, minutes = map(int, start_time.split(":"))
    total_minutes = hours * 60 + minutes + duration_minutes
    end_hours = (total_minutes // 60) % 24
    end_minutes = total_minutes % 60
    return f"{end_hours:02d}:{end_minutes:02d}"

async def generate_recurring_schedules(class_data: dict, weeks: int = 8):
    today = date.today()
    # Respect start_date and end_date from class config
    start_date_str = class_data.get("start_date")
    end_date_str = class_data.get("end_date")
    range_start = today
    if start_date_str and start_date_str.strip():
        try:
            parsed = date.fromisoformat(start_date_str)
            if parsed > today:
                range_start = parsed
        except ValueError:
            pass
    range_end = range_start + timedelta(days=weeks * 7)
    if end_date_str and end_date_str.strip():
        try:
            parsed = date.fromisoformat(end_date_str)
            range_end = parsed
        except ValueError:
            pass
    end_time = class_data.get("end_time") or calculate_end_time(class_data["start_time"], class_data["duration_minutes"])
    schedules = []
    current_date = range_start
    while current_date <= range_end:
        if current_date.weekday() in class_data.get("days_of_week", []):
            schedule = {
                "id": str(uuid.uuid4()), "class_id": class_data["id"],
                "gym_id": class_data["gym_id"], "date": current_date.isoformat(),
                "start_time": class_data["start_time"],
                "end_time": end_time,
                "trainer_id": class_data.get("trainer_id"),
                "max_capacity": class_data["max_capacity"], "current_bookings": 0,
                "status": "scheduled", "created_at": datetime.now(timezone.utc).isoformat()
            }
            schedules.append(schedule)
        current_date += timedelta(days=1)
    if schedules:
        await db.class_schedules.insert_many(schedules)

# ==================== TRAINER ROUTES ====================

@router.post("/trainers")
async def create_trainer(trainer: TrainerCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"], trainer.gym_id)
    existing = await db.admins.find_one({"email": trainer.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    trainer_dict = {
        "id": str(uuid.uuid4()), "email": trainer.email,
        "password": hash_password(trainer.password), "name": trainer.name,
        "phone": trainer.phone, "role": "trainer", "gym_id": trainer.gym_id,
        "specialties": trainer.specialties or [], "bio": trainer.bio,
        "avatar_url": trainer.avatar_url, "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admins.insert_one(trainer_dict)
    trainer_dict.pop("password", None)
    trainer_dict.pop("_id", None)
    return trainer_dict

@router.get("/trainers")
async def get_trainers(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"role": "trainer"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    trainers = await db.admins.find(query, {"_id": 0, "password": 0}).to_list(100)
    return trainers

@router.get("/trainers/{trainer_id}")
async def get_trainer(trainer_id: str, admin: dict = Depends(get_current_admin)):
    trainer = await db.admins.find_one({"id": trainer_id, "role": "trainer"}, {"_id": 0, "password": 0})
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return trainer

@router.put("/trainers/{trainer_id}")
async def update_trainer(trainer_id: str, update_data: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    allowed_fields = ["name", "phone", "specialties", "bio", "avatar_url", "active"]
    update_dict = {k: v for k, v in update_data.items() if k in allowed_fields and v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    await db.admins.update_one({"id": trainer_id, "role": "trainer"}, {"$set": update_dict})
    return {"message": "Trainer updated"}

# ==================== STAFF ROUTES ====================

@router.post("/staff")
async def create_staff(staff_data: AdminCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    if staff_data.role not in ["gym_admin", "gym_manager"]:
        raise HTTPException(status_code=400, detail="Invalid role. Use 'gym_admin' or 'gym_manager'")
    existing = await db.admins.find_one({"email": staff_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    gym_id = staff_data.gym_id or admin.get("gym_id")
    if not gym_id and admin["role"] != "super_admin":
        raise HTTPException(status_code=400, detail="gym_id required")
    staff_dict = {
        "id": str(uuid.uuid4()), "email": staff_data.email,
        "password": hash_password(staff_data.password), "name": staff_data.name,
        "role": staff_data.role, "gym_id": gym_id, "active": True,
        "permissions": DEFAULT_MANAGER_PERMISSIONS if staff_data.role == "gym_manager" else [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.admins.insert_one(staff_dict)
    staff_dict.pop("password", None)
    staff_dict.pop("_id", None)
    return staff_dict

@router.get("/staff")
async def get_staff(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    query = {"role": {"$in": ["gym_admin", "gym_manager", "trainer"]}}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    staff = await db.admins.find(query, {"_id": 0, "password": 0}).to_list(100)
    return staff

@router.get("/staff/permissions-catalog")
async def get_permissions_catalog(admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    labels = {
        "members_view": "Ver socios",
        "members_create": "Crear socios",
        "members_edit": "Editar socios",
        "members_delete": "Eliminar socios",
        "members_suspend": "Suspender/Reactivar socios",
        "payments_register": "Registrar pagos",
        "pos_sell": "Ventas TPV",
        "pos_products": "Gestionar productos TPV",
        "access_view": "Ver accesos",
        "classes_manage": "Gestionar clases y horarios",
        "data_export": "Exportar datos (Excel)",
        "notifications_send": "Enviar notificaciones",
    }
    return {
        "all_permissions": ALL_MANAGER_PERMISSIONS,
        "default_permissions": DEFAULT_MANAGER_PERMISSIONS,
        "labels": labels
    }

@router.put("/staff/{staff_id}/permissions")
async def update_staff_permissions(staff_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    staff_member = await db.admins.find_one({"id": staff_id, "role": "gym_manager"}, {"_id": 0})
    if not staff_member:
        raise HTTPException(status_code=404, detail="Gestor no encontrado")
    if admin["role"] != "super_admin" and admin.get("gym_id") != staff_member.get("gym_id"):
        raise HTTPException(status_code=403, detail="No tienes acceso a este gestor")
    permissions = body.get("permissions", [])
    valid = [p for p in permissions if p in ALL_MANAGER_PERMISSIONS]
    await db.admins.update_one({"id": staff_id}, {"$set": {"permissions": valid}})
    return {"message": "Permisos actualizados", "permissions": valid}

@router.put("/staff/{staff_id}/toggle-active")
async def toggle_staff_active(staff_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    if staff_id == admin["id"]:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")
    target = await db.admins.find_one({"id": staff_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if admin["role"] != "super_admin" and admin.get("gym_id") != target.get("gym_id"):
        raise HTTPException(status_code=403, detail="No tienes acceso a este usuario")
    new_active = body.get("active", not target.get("active", True))
    await db.admins.update_one({"id": staff_id}, {"$set": {"active": new_active}})
    return {"message": "Activado" if new_active else "Desactivado", "active": new_active}

# ==================== CLASS ROUTES ====================

@router.post("/classes")
async def create_class(class_data: ClassCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"], class_data.gym_id)
    class_dict = class_data.model_dump()
    class_dict["id"] = str(uuid.uuid4())
    class_dict["active"] = True
    class_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.classes.insert_one(class_dict)
    class_dict.pop("_id", None)
    if class_data.recurring and class_data.days_of_week and class_data.start_time:
        await generate_recurring_schedules(class_dict, weeks=4)
    if not class_data.recurring and class_data.single_date and class_data.single_start_time:
        schedule = {
            "id": str(uuid.uuid4()), "class_id": class_dict["id"],
            "gym_id": class_data.gym_id, "date": class_data.single_date,
            "start_time": class_data.single_start_time,
            "end_time": calculate_end_time(class_data.single_start_time, class_data.duration_minutes),
            "trainer_id": class_data.trainer_id, "max_capacity": class_data.max_capacity,
            "current_bookings": 0, "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.class_schedules.insert_one(schedule)
    return class_dict

@router.get("/classes")
async def get_classes(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"active": True}
    if admin["role"] == "trainer":
        query["trainer_id"] = admin["id"]
        query["gym_id"] = admin.get("gym_id")
    elif admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    classes = await db.classes.find(query, {"_id": 0}).to_list(100)
    for c in classes:
        if c.get("trainer_id"):
            trainer = await db.admins.find_one({"id": c["trainer_id"]}, {"_id": 0, "password": 0})
            c["trainer"] = trainer
    return classes

@router.get("/classes/{class_id}")
async def get_class(class_id: str, admin: dict = Depends(get_current_admin)):
    class_data = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_data:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_data

@router.put("/classes/{class_id}")
async def update_class(class_id: str, class_update: ClassUpdate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    raw = class_update.model_dump()
    update_data = {}
    for k, v in raw.items():
        if v is not None:
            # Convert empty strings to None for date fields
            if k in ("start_date", "end_date") and isinstance(v, str) and not v.strip():
                update_data[k] = None
            else:
                update_data[k] = v
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.classes.update_one({"id": class_id}, {"$set": update_data})
    # Regenerate schedules if recurring settings changed
    if any(k in update_data for k in ["days_of_week", "start_time", "end_time", "start_date", "end_date", "recurring", "duration_minutes"]):
        cls = await db.classes.find_one({"id": class_id}, {"_id": 0})
        if cls and cls.get("recurring") and cls.get("days_of_week") and cls.get("start_time"):
            # Delete future unbooked schedules and regenerate
            today_str = date.today().isoformat()
            await db.class_schedules.delete_many({"class_id": class_id, "current_bookings": 0, "date": {"$gte": today_str}})
            await generate_recurring_schedules(cls)
    updated = await db.classes.find_one({"id": class_id}, {"_id": 0})
    return updated

@router.delete("/classes/{class_id}")
async def delete_class(class_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    await db.classes.update_one({"id": class_id}, {"$set": {"active": False}})
    await db.class_schedules.delete_many({"class_id": class_id})
    return {"message": "Class deleted"}

# ==================== SCHEDULE ROUTES ====================

@router.post("/schedules")
async def create_schedule(schedule: ClassScheduleCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    class_data = await db.classes.find_one({"id": schedule.class_id}, {"_id": 0})
    if not class_data:
        raise HTTPException(status_code=404, detail="Class not found")
    schedule_dict = {
        "id": str(uuid.uuid4()), "class_id": schedule.class_id,
        "gym_id": class_data["gym_id"], "class_name": class_data["name"],
        "date": schedule.date, "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "trainer_id": schedule.trainer_id or class_data.get("trainer_id"),
        "max_capacity": schedule.max_capacity or class_data["max_capacity"],
        "current_bookings": 0, "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.class_schedules.insert_one(schedule_dict)
    schedule_dict.pop("_id", None)
    return schedule_dict

@router.get("/schedules")
async def get_schedules(
    gym_id: Optional[str] = None, date_from: Optional[str] = None,
    date_to: Optional[str] = None, trainer_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    query = {"status": {"$ne": "cancelled"}}
    if admin["role"] == "trainer":
        query["trainer_id"] = admin["id"]
        query["gym_id"] = admin.get("gym_id")
    elif admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    if trainer_id:
        query["trainer_id"] = trainer_id
    schedules = await db.class_schedules.find(query, {"_id": 0}).sort("date", 1).to_list(500)
    for s in schedules:
        class_data = await db.classes.find_one({"id": s["class_id"]}, {"_id": 0})
        s["class"] = class_data
        if s.get("trainer_id"):
            trainer = await db.admins.find_one({"id": s["trainer_id"]}, {"_id": 0, "password": 0})
            s["trainer"] = trainer
    return schedules

@router.get("/schedules/public/{gym_id}")
async def get_public_schedules(gym_id: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
    query = {"gym_id": gym_id, "status": "scheduled"}
    if not date_from:
        date_from = datetime.now(timezone.utc).date().isoformat()
    query["date"] = {"$gte": date_from}
    if date_to:
        query["date"]["$lte"] = date_to
    schedules = await db.class_schedules.find(query, {"_id": 0}).sort([("date", 1), ("start_time", 1)]).to_list(100)
    for s in schedules:
        class_data = await db.classes.find_one({"id": s["class_id"]}, {"_id": 0})
        s["class"] = class_data
        if s.get("trainer_id"):
            trainer = await db.admins.find_one({"id": s["trainer_id"]}, {"_id": 0, "password": 0})
            s["trainer"] = trainer
        s["spots_available"] = s["max_capacity"] - s["current_bookings"]
    return schedules

@router.put("/schedules/{schedule_id}/cancel")
async def cancel_schedule(schedule_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin", "gym_manager"])
    await db.class_schedules.update_one({"id": schedule_id}, {"$set": {"status": "cancelled"}})
    await db.bookings.update_many({"schedule_id": schedule_id}, {"$set": {"status": "cancelled"}})
    return {"message": "Schedule cancelled"}

# ==================== BOOKING ROUTES ====================

@router.post("/bookings")
async def create_booking(booking: BookingCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    if payload.get("role") != "member":
        raise HTTPException(status_code=403, detail="Only members can book classes")
    # Check active membership
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member or member.get("status") not in ("active",):
        raise HTTPException(status_code=403, detail="Necesitas una membresia activa para reservar clases")
    active_membership = await db.memberships.find_one({"member_id": member_id, "status": "active"}, {"_id": 0})
    if not active_membership:
        raise HTTPException(status_code=403, detail="Necesitas una membresia activa para reservar clases")
    schedule = await db.class_schedules.find_one({"id": booking.schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if schedule["status"] != "scheduled":
        raise HTTPException(status_code=400, detail="Class is not available for booking")
    if schedule["current_bookings"] >= schedule["max_capacity"]:
        raise HTTPException(status_code=400, detail="Class is full")
    existing = await db.bookings.find_one({"member_id": member_id, "schedule_id": booking.schedule_id, "status": {"$ne": "cancelled"}})
    if existing:
        raise HTTPException(status_code=400, detail="Already booked for this class")
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    booking_dict = {
        "id": str(uuid.uuid4()), "member_id": member_id, "member_name": member["name"],
        "member_code": member["code"], "schedule_id": booking.schedule_id,
        "class_id": schedule["class_id"], "gym_id": schedule["gym_id"],
        "date": schedule["date"], "status": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.bookings.insert_one(booking_dict)
    await db.class_schedules.update_one({"id": booking.schedule_id}, {"$inc": {"current_bookings": 1}})
    booking_dict.pop("_id", None)
    return booking_dict

@router.get("/bookings")
async def get_bookings(
    gym_id: Optional[str] = None, schedule_id: Optional[str] = None,
    date: Optional[str] = None, admin: dict = Depends(get_current_admin)
):
    query = {}
    if admin["role"] == "trainer":
        trainer_schedules = await db.class_schedules.find({"trainer_id": admin["id"]}, {"id": 1}).to_list(1000)
        schedule_ids = [s["id"] for s in trainer_schedules]
        query["schedule_id"] = {"$in": schedule_ids}
    elif admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if schedule_id:
        query["schedule_id"] = schedule_id
    if date:
        query["date"] = date
    bookings = await db.bookings.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return bookings

@router.get("/bookings/member")
async def get_member_bookings(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    bookings = await db.bookings.find(
        {"member_id": member_id, "status": {"$ne": "cancelled"}}, {"_id": 0}
    ).sort("date", -1).to_list(50)
    for b in bookings:
        schedule = await db.class_schedules.find_one({"id": b["schedule_id"]}, {"_id": 0})
        if schedule:
            class_data = await db.classes.find_one({"id": schedule["class_id"]}, {"_id": 0})
            b["schedule"] = schedule
            b["class"] = class_data
    return bookings

@router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if payload.get("role") == "member" and booking["member_id"] != member_id:
        raise HTTPException(status_code=403, detail="Cannot cancel others' bookings")
    await db.bookings.update_one({"id": booking_id}, {"$set": {"status": "cancelled"}})
    await db.class_schedules.update_one({"id": booking["schedule_id"]}, {"$inc": {"current_bookings": -1}})
    return {"message": "Booking cancelled"}

@router.get("/bookings/schedule/{schedule_id}/attendees")
async def get_schedule_attendees(schedule_id: str, admin: dict = Depends(get_current_admin)):
    bookings = await db.bookings.find({"schedule_id": schedule_id, "status": "confirmed"}, {"_id": 0}).to_list(100)
    return bookings

# ==================== ATTENDANCE ====================

@router.post("/bookings/{booking_id}/checkin")
async def checkin_booking(booking_id: str, admin: dict = Depends(get_current_admin)):
    booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if booking["status"] != "confirmed":
        raise HTTPException(status_code=400, detail="La reserva no esta confirmada")
    await db.bookings.update_one({"id": booking_id}, {"$set": {
        "checked_in": True, "checked_in_at": datetime.now(timezone.utc).isoformat(),
        "checked_in_by": admin["id"]
    }})
    return {"message": "Check-in registrado"}

@router.post("/bookings/{booking_id}/checkout")
async def checkout_booking(booking_id: str, admin: dict = Depends(get_current_admin)):
    await db.bookings.update_one({"id": booking_id}, {"$set": {
        "checked_in": False, "checked_in_at": None, "checked_in_by": None
    }})
    return {"message": "Check-in anulado"}

@router.get("/attendance/schedule/{schedule_id}")
async def get_schedule_attendance(schedule_id: str, admin: dict = Depends(get_current_admin)):
    schedule = await db.class_schedules.find_one({"id": schedule_id}, {"_id": 0})
    if not schedule:
        raise HTTPException(status_code=404, detail="Horario no encontrado")
    bookings = await db.bookings.find({"schedule_id": schedule_id, "status": "confirmed"}, {"_id": 0}).to_list(200)
    class_data = await db.classes.find_one({"id": schedule.get("class_id")}, {"_id": 0})
    total = len(bookings)
    checked_in = sum(1 for b in bookings if b.get("checked_in"))
    return {"schedule": schedule, "class": class_data, "bookings": bookings,
            "total_booked": total, "checked_in": checked_in, "pending": total - checked_in}

@router.get("/attendance/stats")
async def get_attendance_stats(
    gym_id: Optional[str] = None, date_from: Optional[str] = None,
    date_to: Optional[str] = None, admin: dict = Depends(get_current_admin)
):
    query = {"status": "confirmed"}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if date_from:
        query["date"] = {"$gte": date_from}
    if date_to:
        if "date" in query:
            query["date"]["$lte"] = date_to
        else:
            query["date"] = {"$lte": date_to}
    all_bookings = await db.bookings.find(query, {"_id": 0}).to_list(5000)
    total_bookings = len(all_bookings)
    total_checkins = sum(1 for b in all_bookings if b.get("checked_in"))
    return {"total_bookings": total_bookings, "total_checkins": total_checkins,
            "attendance_rate": round((total_checkins / total_bookings * 100), 1) if total_bookings > 0 else 0}


# ==================== TRAINER DASHBOARD ====================

@router.get("/trainer/dashboard")
async def get_trainer_dashboard(admin: dict = Depends(get_current_admin)):
    """Dashboard data for trainers: their classes today, week stats, upcoming schedules."""
    trainer_id = admin["id"]
    today = date.today().isoformat()
    gym_id = admin.get("gym_id")

    # Today's schedules for this trainer
    today_schedules = await db.class_schedules.find(
        {"trainer_id": trainer_id, "date": today, "status": {"$ne": "cancelled"}}, {"_id": 0}
    ).sort("start_time", 1).to_list(50)

    for s in today_schedules:
        class_data = await db.classes.find_one({"id": s["class_id"], "active": {"$ne": False}}, {"_id": 0})
        if not class_data:
            continue
        s["class"] = class_data
        bookings = await db.bookings.find(
            {"schedule_id": s["id"], "status": "confirmed"}, {"_id": 0}
        ).to_list(200)
        s["bookings"] = bookings
        s["checked_in_count"] = sum(1 for b in bookings if b.get("checked_in"))
    today_schedules = [s for s in today_schedules if s.get("class")]

    # This week stats
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    week_end = (date.today() + timedelta(days=6 - date.today().weekday())).isoformat()
    week_schedules = await db.class_schedules.find(
        {"trainer_id": trainer_id, "date": {"$gte": week_start, "$lte": week_end}, "status": {"$ne": "cancelled"}}, {"_id": 0}
    ).to_list(100)
    week_bookings = 0
    week_checkins = 0
    for ws in week_schedules:
        bks = await db.bookings.find({"schedule_id": ws["id"], "status": "confirmed"}, {"_id": 0}).to_list(200)
        week_bookings += len(bks)
        week_checkins += sum(1 for b in bks if b.get("checked_in"))

    # Upcoming schedules (next 7 days)
    upcoming = await db.class_schedules.find(
        {"trainer_id": trainer_id, "date": {"$gt": today, "$lte": (date.today() + timedelta(days=7)).isoformat()}, "status": {"$ne": "cancelled"}},
        {"_id": 0}
    ).sort([("date", 1), ("start_time", 1)]).to_list(20)
    for u in upcoming:
        class_data = await db.classes.find_one({"id": u["class_id"], "active": {"$ne": False}}, {"_id": 0})
        u["class"] = class_data
    upcoming = [u for u in upcoming if u.get("class")]

    # Trainer's total classes
    total_classes = await db.classes.count_documents({"trainer_id": trainer_id, "active": True})

    return {
        "today_schedules": today_schedules,
        "upcoming_schedules": upcoming,
        "week_stats": {
            "total_schedules": len(week_schedules),
            "total_bookings": week_bookings,
            "total_checkins": week_checkins,
            "attendance_rate": round((week_checkins / week_bookings * 100), 1) if week_bookings > 0 else 0
        },
        "total_classes": total_classes
    }


@router.post("/classes/cleanup-stale-schedules")
async def cleanup_stale_schedules(admin: dict = Depends(get_current_admin)):
    """Remove schedules for deleted/inactive classes and schedules past their class end_date."""
    check_role(admin, ["super_admin", "gym_admin"])
    # Remove schedules for inactive classes
    inactive_classes = await db.classes.find({"active": False}, {"id": 1, "_id": 0}).to_list(1000)
    inactive_ids = [c["id"] for c in inactive_classes]
    removed_inactive = 0
    if inactive_ids:
        result = await db.class_schedules.delete_many({"class_id": {"$in": inactive_ids}})
        removed_inactive = result.deleted_count
    # Remove schedules past their class end_date
    removed_expired = 0
    classes_with_end = await db.classes.find({"end_date": {"$ne": None, "$exists": True}, "active": True}, {"_id": 0}).to_list(1000)
    for cls in classes_with_end:
        end_date = cls.get("end_date")
        if end_date and isinstance(end_date, str) and end_date.strip():
            result = await db.class_schedules.delete_many({
                "class_id": cls["id"],
                "date": {"$gt": end_date},
                "current_bookings": 0
            })
            removed_expired += result.deleted_count
    # Remove orphan schedules (class_id doesn't exist)
    all_class_ids = [c["id"] async for c in db.classes.find({}, {"id": 1, "_id": 0})]
    if all_class_ids:
        orphan_result = await db.class_schedules.delete_many({"class_id": {"$nin": all_class_ids}})
        removed_orphans = orphan_result.deleted_count
    else:
        removed_orphans = 0
    return {
        "removed_inactive": removed_inactive,
        "removed_expired": removed_expired, 
        "removed_orphans": removed_orphans,
        "total_removed": removed_inactive + removed_expired + removed_orphans
    }
