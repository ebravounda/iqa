from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import logging

from database import db
from auth import get_current_admin, create_jwt_token
from models import MemberPublicRegister
from qr_utils import generate_member_code
import uuid
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
ROOT_DIR = Path(__file__).parent.parent

# ==================== EMAIL ====================

async def send_gym_email(gym_id: str, to_email: str, subject: str, html_body: str):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    smtp_host = gym.get("smtp_host")
    smtp_port = gym.get("smtp_port", 587)
    smtp_user = gym.get("smtp_user")
    smtp_password = gym.get("smtp_password")
    smtp_from = gym.get("smtp_from_email", smtp_user)
    if not smtp_host or not smtp_user or not smtp_password:
        raise HTTPException(status_code=400, detail="SMTP no configurado para este gimnasio")
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{gym.get('name', 'IngresoQR')} <{smtp_from}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))
    try:
        await aiosmtplib.send(msg, hostname=smtp_host, port=smtp_port, username=smtp_user,
                              password=smtp_password, use_tls=smtp_port == 465, start_tls=smtp_port != 465)
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al enviar email: {str(e)}")

async def send_templated_email(gym_id: str, template_type: str, to_email: str, variables: dict):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        return False
    template = None
    for t in gym.get("email_templates", []):
        if t["type"] == template_type:
            template = t
            break
    if not template:
        return False
    subject = template["subject"]
    body = template["body"]
    for key, value in variables.items():
        subject = subject.replace(key, str(value))
        body = body.replace(key, str(value))
    color = gym.get("primary_color", "#E1FF01")
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:30px;background:#09090B;color:#fff;border-radius:16px;">
        <div style="text-align:center;margin-bottom:20px;">
            <h1 style="color:{color};margin:0;font-size:24px;">{gym.get('name','IngresoQR')}</h1>
        </div>
        <div style="line-height:1.6;">{body.replace(chr(10), '<br/>')}</div>
    </div>
    """
    try:
        await send_gym_email(gym_id, to_email, subject, html_body)
        return True
    except Exception:
        return False

@router.post("/email/test")
async def test_email(admin: dict = Depends(get_current_admin)):
    gym_id = admin.get("gym_id")
    if not gym_id:
        raise HTTPException(status_code=400, detail="Selecciona un gimnasio")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    to_email = gym.get("smtp_from_email") or gym.get("smtp_user")
    if not to_email:
        raise HTTPException(status_code=400, detail="SMTP no configurado")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px;">
        <h2 style="color:{gym.get('primary_color','#E1FF01')};">Prueba de Email</h2>
        <p>Este es un correo de prueba desde <strong>{gym.get('name','IngresoQR')}</strong>.</p>
        <p>Si recibes este correo, tu configuracion SMTP es correcta.</p>
    </div>
    """
    await send_gym_email(gym_id, to_email, f"[{gym.get('name')}] Prueba de configuracion SMTP", html)
    return {"message": f"Email de prueba enviado a {to_email}"}

@router.post("/email/welcome/{member_id}")
async def send_welcome_email(member_id: str, admin: dict = Depends(get_current_admin)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    gym_id = member.get("gym_id")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    color = gym.get("primary_color", "#E1FF01")
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:30px;background:#09090B;color:#fff;border-radius:16px;">
        <div style="text-align:center;margin-bottom:20px;">
            <h1 style="color:{color};margin:0;">{gym.get('name','IngresoQR')}</h1>
        </div>
        <h2>Bienvenido/a, {member.get('name','Socio')}</h2>
        <p>Tu registro en <strong>{gym.get('name')}</strong> ha sido completado.</p>
        <div style="background:#18181B;padding:20px;border-radius:12px;text-align:center;margin:20px 0;">
            <p style="color:#a1a1aa;margin:0 0 8px;">Tu codigo de acceso</p>
            <p style="font-size:32px;font-weight:900;color:{color};font-family:monospace;letter-spacing:4px;margin:0;">{member.get('code','------')}</p>
        </div>
    </div>
    """
    await send_gym_email(gym_id, member["email"], f"Bienvenido/a a {gym.get('name')}", html)
    return {"message": f"Email de bienvenida enviado a {member['email']}"}

# ==================== KIOSK ====================

@router.post("/kiosk/register")
async def kiosk_register(member: MemberPublicRegister):
    existing = await db.members.find_one({"email": member.email, "gym_id": member.gym_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya esta registrado en este gimnasio")
    gym = await db.gyms.find_one({"id": member.gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    member_dict = {
        "id": str(uuid.uuid4()), "email": member.email, "name": member.name,
        "phone": member.phone, "gym_id": member.gym_id,
        "code": generate_member_code(), "status": "pending",
        "registered_via": "kiosk", "created_at": datetime.now(timezone.utc).isoformat()
    }
    while await db.members.find_one({"code": member_dict["code"]}):
        member_dict["code"] = generate_member_code()
    await db.members.insert_one(member_dict)
    member_dict.pop("_id", None)
    token = create_jwt_token({"sub": member_dict["id"], "type": "member", "gym_id": member.gym_id})
    email_sent = False
    if gym.get("smtp_host") and gym.get("smtp_user"):
        try:
            plan = None
            if member.plan_id:
                plan = await db.plans.find_one({"id": member.plan_id}, {"_id": 0})
            variables = {
                "{gym_name}": gym.get("name", ""), "{member_name}": member.name,
                "{member_code}": member_dict["code"], "{member_email}": member.email,
                "{plan_name}": plan.get("name", "") if plan else ""
            }
            email_sent = await send_templated_email(member.gym_id, "welcome", member.email, variables)
        except Exception as e:
            logger.error(f"Kiosk email error: {e}")
    return {"member": member_dict, "token": token, "email_sent": email_sent,
            "message": f"Registro exitoso. Codigo: {member_dict['code']}"}

# ==================== DASHBOARD ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin)):
    gym_id = admin.get("gym_id") if admin["role"] != "super_admin" else None
    query = {}
    if gym_id:
        query["gym_id"] = gym_id
    total_members = await db.members.count_documents(query if query else {})
    active_members = await db.members.count_documents({**query, "status": "active"})
    pending_members = await db.members.count_documents({**query, "status": "pending"})
    suspended_members = await db.members.count_documents({**query, "status": "suspended"})
    
    # Access stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    access_query = {}
    if gym_id:
        access_query["gym_id"] = gym_id
    today_count = await db.access_logs.count_documents({**access_query, "timestamp": {"$gte": today_start.isoformat()}})
    from datetime import timedelta
    week_start = today_start - timedelta(days=today_start.weekday())
    week_count = await db.access_logs.count_documents({**access_query, "timestamp": {"$gte": week_start.isoformat()}})
    month_start = today_start.replace(day=1)
    month_count = await db.access_logs.count_documents({**access_query, "timestamp": {"$gte": month_start.isoformat()}})
    
    member_query = {"status": "active"}
    if gym_id:
        member_query["gym_id"] = gym_id
    active_memberships = await db.memberships.count_documents({"status": "active", **({"gym_id": gym_id} if gym_id else {})})
    
    # Revenue
    revenue_query = {"payment_status": "paid", "created_at": {"$gte": month_start.isoformat()}}
    if gym_id:
        revenue_query["gym_id"] = gym_id
    transactions = await db.payment_transactions.find(revenue_query, {"_id": 0}).to_list(1000)
    month_revenue = sum(t.get("amount", 0) for t in transactions)
    
    gyms_count = await db.gyms.count_documents({}) if admin["role"] == "super_admin" else 1
    classes_count = await db.classes.count_documents({**query, "active": True})
    today = datetime.now(timezone.utc).date().isoformat()
    today_schedules = await db.class_schedules.count_documents({**query, "date": today})
    today_bookings = await db.bookings.count_documents({"date": today, "status": "confirmed", **({"gym_id": gym_id} if gym_id else {})})
    
    capacity_info = None
    if gym_id:
        gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0, "max_members": 1})
        max_members = gym.get("max_members") if gym else None
        if max_members and max_members > 0:
            capacity_info = {"max_members": max_members, "active_members": active_members,
                            "usage_percent": round((active_members / max_members * 100), 1)}
    
    recent_accesses_enriched = []
    if admin["role"] == "super_admin":
        recent_logs = await db.access_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(15)
        gym_cache = {}
        for log in recent_logs:
            gid = log.get("gym_id")
            if gid and gid not in gym_cache:
                g = await db.gyms.find_one({"id": gid}, {"_id": 0, "name": 1})
                gym_cache[gid] = g.get("name", "?") if g else "?"
            log["gym_name"] = gym_cache.get(gid, "?")
            recent_accesses_enriched.append(log)
    
    return {
        "total_members": total_members, "active_members": active_members,
        "pending_members": pending_members, "suspended_members": suspended_members,
        "gyms_count": gyms_count, "month_revenue": month_revenue,
        "classes_count": classes_count, "today_schedules": today_schedules,
        "today_bookings": today_bookings, "capacity": capacity_info,
        "recent_accesses_by_gym": recent_accesses_enriched if admin["role"] == "super_admin" else [],
        "today_accesses": today_count, "week_accesses": week_count,
        "month_accesses": month_count, "active_memberships": active_memberships
    }

# ==================== DOWNLOADS ====================

@router.get("/download/server-py")
async def download_server():
    file_path = ROOT_DIR / "downloads" / "server.py"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename="server.py", media_type="text/plain")

@router.get("/download/raspberry-py")
async def download_raspberry():
    file_path = ROOT_DIR / "downloads" / "raspberry_access_control.py"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename="raspberry_access_control.py", media_type="text/plain")

@router.get("/download/frontend-build")
async def download_frontend_build():
    file_path = ROOT_DIR / "downloads" / "build.tar.gz"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename="build.tar.gz", media_type="application/gzip")

@router.get("/download/test-gpio")
async def download_test_gpio():
    file_path = ROOT_DIR / "downloads" / "test_gpio.py"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename="test_gpio.py", media_type="text/plain")

@router.get("/download/guia-google-play")
async def download_google_play_guide():
    file_path = ROOT_DIR.parent / "GUIA_GOOGLE_PLAY.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=str(file_path), filename="GUIA_GOOGLE_PLAY.md", media_type="text/markdown")
