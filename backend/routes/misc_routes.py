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

async def send_gym_email(gym_id: str, to_email: str, subject: str, html_body: str, member_id: str = None, email_type: str = "general"):
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
        # Log email
        log = {
            "id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": member_id,
            "to_email": to_email, "subject": subject, "email_type": email_type,
            "status": "sent", "sent_at": datetime.now(timezone.utc).isoformat()
        }
        await db.email_logs.insert_one(log)
        return True
    except Exception as e:
        logger.error(f"Email send error: {e}")
        log = {
            "id": str(uuid.uuid4()), "gym_id": gym_id, "member_id": member_id,
            "to_email": to_email, "subject": subject, "email_type": email_type,
            "status": "failed", "error": str(e), "sent_at": datetime.now(timezone.utc).isoformat()
        }
        await db.email_logs.insert_one(log)
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
    membership = await db.memberships.find_one({"member_id": member_id, "status": "active"}, {"_id": 0})
    plan = None
    payment_btn = ""
    if membership:
        plan = await db.plans.find_one({"id": membership.get("plan_id")}, {"_id": 0})
    if plan:
        payment_btn = f"""
        <div style="background:#18181B;padding:15px;border-radius:12px;margin:15px 0;">
            <p style="color:#a1a1aa;margin:0 0 5px;">Plan contratado</p>
            <p style="font-size:18px;font-weight:700;color:{color};margin:0;">{plan.get('name','')}</p>
            <p style="color:#a1a1aa;margin:5px 0 0;">{plan.get('price',0)} {gym.get('currency','EUR')} / {plan.get('duration_days',30)} dias</p>
        </div>
        <div style="text-align:center;margin:20px 0;">
            <a href="https://app.ingresoqr.com/app/login" style="display:inline-block;padding:14px 32px;background:{color};color:#000;font-weight:700;text-decoration:none;border-radius:10px;font-size:16px;">Acceder a Mi Cuenta</a>
        </div>
        """
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
        {payment_btn}
    </div>
    """
    await send_gym_email(gym_id, member["email"], f"Bienvenido/a a {gym.get('name')}", html, member_id=member_id, email_type="welcome")
    return {"message": f"Email de bienvenida enviado a {member['email']}"}

@router.get("/emails/member/{member_id}")
async def get_member_emails(member_id: str, admin: dict = Depends(get_current_admin)):
    """Get email history for a specific member"""
    emails = await db.email_logs.find({"member_id": member_id}, {"_id": 0}).sort("sent_at", -1).to_list(50)
    return emails

@router.post("/emails/resend/{email_id}")
async def resend_email(email_id: str, admin: dict = Depends(get_current_admin)):
    """Resend a previously sent email (max 1 per minute per member)"""
    email_log = await db.email_logs.find_one({"id": email_id}, {"_id": 0})
    if not email_log:
        raise HTTPException(status_code=404, detail="Email no encontrado")
    member_id = email_log.get("member_id")
    if member_id:
        one_min_ago = (datetime.now(timezone.utc) - __import__('datetime').timedelta(minutes=1)).isoformat()
        recent = await db.email_logs.find_one({
            "member_id": member_id, "sent_at": {"$gte": one_min_ago}, "status": "sent"
        })
        if recent:
            raise HTTPException(status_code=429, detail="Espera al menos 1 minuto entre reenvios")
    member = await db.members.find_one({"id": member_id}, {"_id": 0}) if member_id else None
    to_email = member.get("email") if member else email_log.get("to_email")
    gym_id = email_log.get("gym_id")
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if email_log.get("email_type") == "welcome" and member:
        color = gym.get("primary_color", "#E1FF01")
        membership = await db.memberships.find_one({"member_id": member_id, "status": "active"}, {"_id": 0})
        plan = None
        if membership:
            plan = await db.plans.find_one({"id": membership.get("plan_id")}, {"_id": 0})
        plan_info = ""
        if plan:
            plan_info = f"""
            <div style="background:#18181B;padding:15px;border-radius:12px;margin:15px 0;">
                <p style="color:#a1a1aa;margin:0 0 5px;">Plan contratado</p>
                <p style="font-size:18px;font-weight:700;color:{color};margin:0;">{plan.get('name','')}</p>
                <p style="color:#a1a1aa;margin:5px 0 0;">{plan.get('price',0)} {gym.get('currency','EUR')} / {plan.get('duration_days',30)} dias</p>
            </div>
            """
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
            {plan_info}
        </div>
        """
        await send_gym_email(gym_id, to_email, f"Bienvenido/a a {gym.get('name')}", html, member_id=member_id, email_type="welcome_resend")
    else:
        raise HTTPException(status_code=400, detail="Solo se pueden reenviar emails de bienvenida")
    return {"message": f"Email reenviado a {to_email}"}

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

# Documentation PDFs removed from public access



# ==================== Deploy Tools (Super Admin Only) ====================

@router.post("/deploy/sync-backend")
async def sync_backend_files(admin: dict = Depends(get_current_admin)):
    from auth import check_role
    check_role(admin, ["super_admin"])
    import glob, shutil, os
    # Search multiple possible Plesk paths
    search_patterns = [
        "/var/www/vhosts/*/c.ingresoqr.com",
        "/var/www/vhosts/*/c.ingresoqr.com/httpdocs",
        "/var/www/vhosts/c.ingresoqr.com",
        "/var/www/vhosts/ingresoqr.com/c.ingresoqr.com",
    ]
    plesk_base = None
    searched_paths = []
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        for m in matches:
            searched_paths.append(m)
            py_files = glob.glob(os.path.join(m, "*.py"))
            if py_files:
                plesk_base = m
                break
        if plesk_base:
            break
    if not plesk_base:
        return {"success": False, "message": f"No se encontraron archivos .py. Se busco en: {searched_paths or search_patterns}", "synced": 0}
    dest_base = "/opt/gymaccess"
    os.makedirs(dest_base, exist_ok=True)
    synced = []
    # 1. Sync root .py files
    for src in glob.glob(os.path.join(plesk_base, "*.py")):
        filename = os.path.basename(src)
        dest = os.path.join(dest_base, filename)
        try:
            shutil.copy2(src, dest)
            synced.append(filename)
        except Exception as e:
            logger.error(f"Error copying {src}: {e}")
    # 2. Sync routes/*.py
    routes_dest = os.path.join(dest_base, "routes")
    os.makedirs(routes_dest, exist_ok=True)
    for src in glob.glob(os.path.join(plesk_base, "routes", "*.py")):
        filename = os.path.basename(src)
        dest = os.path.join(routes_dest, filename)
        try:
            shutil.copy2(src, dest)
            synced.append(f"routes/{filename}")
        except Exception as e:
            logger.error(f"Error copying {src}: {e}")
    # 3. Sync downloads/*
    downloads_dest = os.path.join(dest_base, "downloads")
    os.makedirs(downloads_dest, exist_ok=True)
    for src in glob.glob(os.path.join(plesk_base, "downloads", "*")):
        filename = os.path.basename(src)
        dest = os.path.join(downloads_dest, filename)
        try:
            shutil.copy2(src, dest)
            synced.append(f"downloads/{filename}")
        except Exception as e:
            logger.error(f"Error copying {src}: {e}")
    if not synced:
        return {"success": False, "message": f"Directorio encontrado ({plesk_base}) pero sin archivos .py", "synced": 0}
    return {"success": True, "message": f"{len(synced)} archivos sincronizados desde {plesk_base}", "synced": len(synced), "files": synced}

@router.post("/deploy/restart-backend")
async def restart_backend(admin: dict = Depends(get_current_admin)):
    from auth import check_role
    check_role(admin, ["super_admin"])
    import subprocess, os
    script = """#!/bin/bash
sleep 2
kill $(pgrep -f 'uvicorn server:app') 2>/dev/null
sleep 2
cd /opt/gymaccess && nohup /opt/gymaccess/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 > /opt/gymaccess/nohup.out 2>&1 &
"""
    script_path = "/tmp/restart_backend.sh"
    with open(script_path, "w") as f:
        f.write(script)
    os.chmod(script_path, 0o755)
    subprocess.Popen(["/bin/bash", script_path], start_new_session=True)
    return {"success": True, "message": "Backend reiniciando en 3 segundos..."}
