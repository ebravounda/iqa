from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging

from database import db
from auth import security, decode_jwt_token, get_current_admin
from models import AccessValidation
from qr_utils import (
    generate_qr_data, generate_static_qr_data, validate_qr_data, 
    sanitize_qr_input, QR_SECRET
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.get("/qr/generate")
async def generate_qr(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    gym_id = payload.get("gym_id")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    
    # Check if this specific member has static QR override
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member or member.get("status") in ("pending", "suspended"):
        raise HTTPException(status_code=403, detail="Necesitas una membresia activa para generar tu QR")
    
    # Check active membership
    active_membership = await db.memberships.find_one({"member_id": member_id, "status": "active"}, {"_id": 0})
    if not active_membership:
        raise HTTPException(status_code=403, detail="Necesitas una membresia activa para generar tu QR")
    
    member_qr_mode = (member or {}).get("qr_mode")
    
    gym_qr_mode = gym.get("qr_mode", "dynamic") if gym else "dynamic"
    effective_qr_mode = member_qr_mode or gym_qr_mode
    
    refresh_seconds = gym.get("qr_refresh_seconds", 10) if gym else 10
    if effective_qr_mode == "static":
        qr_data = generate_static_qr_data(member_id, gym_id)
        return {"qr_code": qr_data, "expires_at": 0, "refresh_seconds": 0, "qr_mode": "static"}
    timestamp = int(datetime.now(timezone.utc).timestamp())
    qr_data = generate_qr_data(member_id, gym_id, timestamp)
    return {"qr_code": qr_data, "expires_at": timestamp + refresh_seconds, "refresh_seconds": refresh_seconds, "qr_mode": "dynamic"}

@router.post("/access/debug-qr")
async def debug_qr_validation(validation: AccessValidation):
    import base64
    import hmac
    import hashlib
    debug_info = {
        "step_1_raw_input": {
            "qr_code_length": len(validation.qr_code),
            "qr_code_first_40": validation.qr_code[:40],
            "qr_code_last_20": validation.qr_code[-20:],
            "has_whitespace": validation.qr_code != validation.qr_code.strip(),
            "has_newline": '\n' in validation.qr_code or '\r' in validation.qr_code,
        }
    }
    sanitized = sanitize_qr_input(validation.qr_code)
    debug_info["step_2_sanitized"] = {"length": len(sanitized), "first_40": sanitized[:40], "changed_from_original": sanitized != validation.qr_code}
    try:
        decoded = base64.urlsafe_b64decode(sanitized.encode()).decode()
        parts = decoded.split('|')
        debug_info["step_3_decode"] = {"success": True, "decoded_content": decoded, "parts_count": len(parts), "parts": parts}
    except Exception as e:
        debug_info["step_3_decode"] = {"success": False, "error": str(e)}
        return debug_info
    if len(parts) == 4:
        if parts[0] == "STATIC":
            data = f"STATIC|{parts[1]}|{parts[2]}"
        else:
            data = f"{parts[0]}|{parts[1]}|{parts[2]}"
        expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
        debug_info["step_4_signature"] = {
            "data_for_hmac": data, "received_signature": parts[3],
            "expected_signature": expected_sig, "match": parts[3] == expected_sig,
            "qr_secret_first_4": QR_SECRET[:4] + "...",
        }
    gym = await db.gyms.find_one({"api_token": validation.gym_token}, {"_id": 0})
    debug_info["step_5_gym"] = {"gym_found": gym is not None, "gym_name": gym.get("name") if gym else None}
    return debug_info

@router.get("/access/self-test")
async def access_self_test():
    test_member_id = "self-test-member"
    test_gym_id = "self-test-gym"
    timestamp = int(datetime.now(timezone.utc).timestamp())
    qr_code = generate_qr_data(test_member_id, test_gym_id, timestamp)
    result = validate_qr_data(qr_code, max_age_seconds=60)
    static_qr = generate_static_qr_data(test_member_id, test_gym_id)
    static_result = validate_qr_data(static_qr, max_age_seconds=9999999)
    corrupted_tests = {
        "trailing_newline": validate_qr_data(qr_code + "\n", max_age_seconds=60),
        "trailing_spaces": validate_qr_data(qr_code + "  ", max_age_seconds=60),
        "stripped_padding": validate_qr_data(qr_code.rstrip("="), max_age_seconds=60),
    }
    return {
        "qr_secret_loaded": QR_SECRET[:4] + "..." + QR_SECRET[-4:],
        "qr_secret_length": len(QR_SECRET),
        "dynamic_qr_test": {"qr_code_preview": qr_code[:40], "valid": result.get("valid"), "details": result},
        "static_qr_test": {"valid": static_result.get("valid"), "details": static_result},
        "corruption_tests": corrupted_tests,
        "all_passed": result.get("valid") and static_result.get("valid") and all(t.get("valid") for t in corrupted_tests.values())
    }

@router.post("/access/validate")
async def validate_access(validation: AccessValidation):
    logger.info(f"Access validate - raw qr_code length: {len(validation.qr_code)}, direction: {validation.direction}")
    gym = await db.gyms.find_one({"api_token": validation.gym_token}, {"_id": 0})
    if not gym:
        return {"valid": False, "reason": "Invalid gym token"}
    if gym.get("status") == "payment_suspended":
        return {"valid": False, "reason": "Gimnasio suspendido por falta de pago"}
    if gym.get("status") == "suspended":
        return {"valid": False, "reason": "Gimnasio suspendido"}
    
    raw_input = validation.qr_code.strip()
    
    # Detect if this is RFID (short hex/numeric string) vs QR code (base64 encoded)
    is_rfid = len(raw_input) <= 20 and all(c in '0123456789ABCDEFabcdef:' for c in raw_input) and '|' not in raw_input
    
    if is_rfid:
        # RFID lookup
        rfid_uid = raw_input.upper().replace(':', '')
        member = await db.members.find_one({"rfid_uid": rfid_uid, "gym_id": gym["id"]}, {"_id": 0})
        if not member:
            return {"valid": False, "reason": "Tarjeta/llavero RFID no registrado", "access_type": "rfid"}
        if member["status"] != "active":
            return {"valid": False, "reason": f"Socio {member.get('status','inactivo')}", "access_type": "rfid"}
        membership = await db.memberships.find_one({"member_id": member["id"], "status": "active"}, {"_id": 0})
        if not membership:
            return {"valid": False, "reason": "Sin membresia activa", "access_type": "rfid"}
        end_str = membership["end_date"]
        if "T" in end_str or "+" in end_str:
            end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        else:
            end_date = datetime.strptime(end_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        if end_date < datetime.now(timezone.utc):
            await db.memberships.update_one({"id": membership["id"]}, {"$set": {"status": "expired"}})
            return {"valid": False, "reason": "Membresia vencida", "access_type": "rfid"}
        # Anti-passback for RFID
        last_log = await db.access_logs.find_one(
            {"member_id": member["id"], "gym_id": gym["id"], "is_guest": {"$ne": True}},
            {"_id": 0}, sort=[("timestamp", -1)]
        )
        direction = validation.direction
        if not direction or direction == "auto":
            if last_log and last_log.get("direction") == "entrada":
                direction = "salida"
            else:
                direction = "entrada"
        access_log = {
            "id": str(uuid.uuid4()), "member_id": member["id"], "member_name": member["name"],
            "member_code": member.get("code"), "gym_id": gym["id"], "direction": direction,
            "access_type": "rfid", "is_guest": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.access_logs.insert_one(access_log)
        return {
            "valid": True, "member_name": member["name"], "member_code": member.get("code"),
            "direction": direction, "access_type": "rfid",
            "membership_end": membership.get("end_date")
        }
    
    # QR code validation (existing logic)
    qr_refresh = gym.get("qr_refresh_seconds", 10)
    max_age = qr_refresh + 5
    result = validate_qr_data(validation.qr_code, max_age)
    if not result["valid"]:
        return result
    if result["gym_id"] != gym["id"]:
        return {"valid": False, "reason": "QR code not for this gym"}
    member_id = result["member_id"]
    # Guest QR
    if member_id.startswith("GUEST:"):
        guest_id = member_id.replace("GUEST:", "")
        guest = await db.guests.find_one({"id": guest_id}, {"_id": 0})
        if not guest:
            return {"valid": False, "reason": "Guest not found"}
        valid_until = datetime.fromisoformat(guest["valid_until"].replace('Z', '+00:00'))
        if valid_until < datetime.now(timezone.utc):
            await db.guests.update_one({"id": guest_id}, {"$set": {"status": "expired"}})
            return {"valid": False, "reason": "Guest pass expired"}
        if guest["status"] != "active":
            return {"valid": False, "reason": f"Guest pass is {guest['status']}"}
        access_log = {
            "id": str(uuid.uuid4()), "guest_id": guest_id, "guest_name": guest["name"],
            "guest_code": guest["code"], "invited_by": guest["invited_by"],
            "invited_by_name": guest["invited_by_name"], "gym_id": gym["id"],
            "direction": validation.direction, "is_guest": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.access_logs.insert_one(access_log)
        await db.guests.update_one({"id": guest_id}, {"$inc": {"accesses": 1}})
        return {"valid": True, "is_guest": True, "guest_name": guest["name"],
                "guest_code": guest["code"], "invited_by": guest["invited_by_name"],
                "direction": validation.direction}
    # Regular member
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        return {"valid": False, "reason": "Member not found"}
    if member["status"] != "active":
        return {"valid": False, "reason": f"Member status: {member['status']}"}
    membership = await db.memberships.find_one({"member_id": member["id"], "status": "active"}, {"_id": 0})
    if not membership:
        return {"valid": False, "reason": "No active membership"}
    end_str = membership["end_date"]
    if "T" in end_str or "+" in end_str:
        end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    else:
        end_date = datetime.strptime(end_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if end_date < datetime.now(timezone.utc):
        await db.memberships.update_one({"id": membership["id"]}, {"$set": {"status": "expired"}})
        return {"valid": False, "reason": "Membership expired"}
    # Anti-passback
    last_log = await db.access_logs.find_one(
        {"member_id": member["id"], "gym_id": gym["id"], "is_guest": {"$ne": True}},
        {"_id": 0}, sort=[("timestamp", -1)]
    )
    if last_log:
        actual_direction = "salida" if last_log.get("direction") == "entrada" else "entrada"
    else:
        actual_direction = "entrada"
    access_log = {
        "id": str(uuid.uuid4()), "member_id": member["id"], "member_name": member["name"],
        "member_code": member["code"], "gym_id": gym["id"],
        "direction": actual_direction, "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.access_logs.insert_one(access_log)
    return {"valid": True, "member_name": member["name"], "member_code": member["code"], "direction": actual_direction}

@router.get("/access/logs")
async def get_access_logs(
    gym_id: Optional[str] = None, member_id: Optional[str] = None,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    limit: int = 100, admin: dict = Depends(get_current_admin)
):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    if member_id:
        query["member_id"] = member_id
    if date_from:
        query["timestamp"] = {"$gte": date_from}
    if date_to:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = date_to
        else:
            query["timestamp"] = {"$lte": date_to}
    logs = await db.access_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

@router.get("/access/logs/member")
async def get_member_access_logs(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    logs = await db.access_logs.find({"member_id": member_id}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    return logs

@router.get("/access/stats/member")
async def get_member_visit_stats_pwa(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Visit statistics for the logged-in member (PWA)"""
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    total = await db.access_logs.count_documents({"member_id": member_id, "direction": "entrada"})
    this_month = await db.access_logs.count_documents({"member_id": member_id, "direction": "entrada", "timestamp": {"$gte": month_start}})
    this_week = await db.access_logs.count_documents({"member_id": member_id, "direction": "entrada", "timestamp": {"$gte": week_start}})

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


@router.get("/access/stats")
async def get_access_stats(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db.access_logs.count_documents({**query, "timestamp": {"$gte": today_start.isoformat()}})
    week_start = today_start - timedelta(days=today_start.weekday())
    week_count = await db.access_logs.count_documents({**query, "timestamp": {"$gte": week_start.isoformat()}})
    month_start = today_start.replace(day=1)
    month_count = await db.access_logs.count_documents({**query, "timestamp": {"$gte": month_start.isoformat()}})
    member_query = {"status": "active"}
    if admin["role"] != "super_admin":
        member_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        member_query["gym_id"] = gym_id
    active_members = await db.members.count_documents(member_query)
    membership_query = {"status": "active"}
    if admin["role"] != "super_admin":
        membership_query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        membership_query["gym_id"] = gym_id
    active_memberships = await db.memberships.count_documents(membership_query)
    return {
        "today_accesses": today_count, "week_accesses": week_count,
        "month_accesses": month_count, "active_members": active_members,
        "active_memberships": active_memberships
    }

@router.get("/access/stats/daily")
async def get_daily_access_stats(gym_id: Optional[str] = None, days: int = 7, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    today = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
    start_date = (today - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_names_es = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
    daily_data = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        day_end = day.replace(hour=23, minute=59, second=59)
        day_query = {**query, "timestamp": {"$gte": day.isoformat(), "$lte": day_end.isoformat()}}
        count = await db.access_logs.count_documents(day_query)
        entry_query = {**day_query, "direction": "entrada"}
        entries = await db.access_logs.count_documents(entry_query)
        daily_data.append({"date": day.strftime("%Y-%m-%d"), "day_name": day_names_es[day.weekday()], "accesos": count, "entradas": entries})
    return daily_data

@router.get("/access/stats/member/{member_id}")
async def get_member_access_stats(member_id: str, days: int = 30, admin: dict = Depends(get_current_admin)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    today = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
    start_date = (today - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    logs = await db.access_logs.find(
        {"member_id": member_id, "timestamp": {"$gte": start_date.isoformat()}}, {"_id": 0}
    ).sort("timestamp", -1).to_list(1000)
    daily = {}
    for log in logs:
        day = log["timestamp"][:10]
        if day not in daily:
            daily[day] = {"entradas": 0, "salidas": 0}
        if log.get("direction") == "entrada":
            daily[day]["entradas"] += 1
        else:
            daily[day]["salidas"] += 1
    total_entries = sum(d["entradas"] for d in daily.values())
    days_attended = len(daily)
    return {
        "member": {"id": member["id"], "name": member["name"], "code": member["code"]},
        "total_entries": total_entries, "days_attended": days_attended, "period_days": days,
        "attendance_rate": round((days_attended / days * 100), 1) if days > 0 else 0,
        "daily_breakdown": [{"date": k, **v} for k, v in sorted(daily.items())],
        "recent_logs": logs[:20]
    }

@router.put("/members/{member_id}/qr-mode")
async def set_member_qr_mode(member_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    if admin["role"] not in ("super_admin", "gym_admin") and admin.get("original_role") != "super_admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para cambiar el modo QR")
    qr_mode = body.get("qr_mode", "dynamic")
    if qr_mode not in ("dynamic", "static"):
        raise HTTPException(status_code=400, detail="qr_mode debe ser 'dynamic' o 'static'")
    update_data = {"qr_mode": qr_mode if qr_mode == "static" else None}
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    return {"message": f"QR mode set to {qr_mode} for member {member_id}"}

@router.get("/access/stats/hourly")
async def get_hourly_access_stats(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    query["timestamp"] = {"$gte": today_start.isoformat()}
    logs = await db.access_logs.find(query, {"_id": 0, "timestamp": 1}).to_list(10000)
    hourly = {f"{h:02d}:00": 0 for h in range(24)}
    for log in logs:
        try:
            hour = log["timestamp"][11:13]
            hourly[f"{hour}:00"] = hourly.get(f"{hour}:00", 0) + 1
        except (IndexError, KeyError):
            pass
    return [{"hour": k, "accesos": v} for k, v in hourly.items()]



@router.get("/access/display/{gym_id}")
async def get_display_data(gym_id: str):
    """Public endpoint for kiosk display - shows occupancy and recent access with initials only (LOPD)"""
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Occupancy
    query = {"gym_id": gym_id, "timestamp": {"$gte": today_start.isoformat()}}
    entries = await db.access_logs.count_documents({**query, "direction": "entrada"})
    exits = await db.access_logs.count_documents({**query, "direction": "salida"})
    current = max(0, entries - exits)
    max_capacity = gym.get("max_capacity")

    # Recent access logs (last 10) - only initials for LOPD
    recent_logs = await db.access_logs.find(
        {"gym_id": gym_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)

    def get_initials(name):
        if not name:
            return "?"
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + ". " + parts[-1][0] + ".").upper()
        return (parts[0][0] + ".").upper()

    display_logs = []
    for log in recent_logs:
        display_logs.append({
            "initials": get_initials(log.get("member_name", log.get("guest_name", ""))),
            "direction": log.get("direction", "entrada"),
            "timestamp": log.get("timestamp"),
            "is_guest": log.get("is_guest", False),
        })

    # Recent access events (approved + denied) - last 5
    recent_events = await db.access_events.find(
        {"gym_id": gym_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(5).to_list(5)

    return {
        "gym_name": gym.get("name"),
        "logo_url": gym.get("logo_url"),
        "primary_color": gym.get("primary_color", "#10b981"),
        "current_occupancy": current,
        "entries_today": entries,
        "exits_today": exits,
        "max_capacity": max_capacity,
        "recent_access": display_logs,
        "recent_events": recent_events,
    }


@router.post("/access/event")
async def log_access_event(body: dict):
    """Log access event (approved or denied) for kiosk display"""
    event = {
        "id": str(uuid.uuid4()),
        "gym_id": body.get("gym_id"),
        "approved": body.get("approved", False),
        "initials": body.get("initials", "?"),
        "direction": body.get("direction", "entrada"),
        "reason": body.get("reason", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.access_events.insert_one(event)
    event.pop("_id", None)
    return {"ok": True}
