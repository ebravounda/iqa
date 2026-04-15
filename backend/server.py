from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from database import db
from auth import hash_password
from datetime import datetime, timezone, timedelta
import asyncio
import logging

# Import all route modules
from routes.auth_routes import router as auth_router
from routes.gym_routes import router as gym_router
from routes.member_routes import router as member_router
from routes.plan_routes import router as plan_router
from routes.access_routes import router as access_router
from routes.device_routes import router as device_router
from routes.payment_routes import router as payment_router
from routes.class_routes import router as class_router
from routes.notification_guest_routes import router as notif_guest_router
from routes.accounting_routes import router as accounting_router
from routes.saas_routes import router as saas_router
from routes.pos_routes import router as pos_router
from routes.misc_routes import router as misc_router
from routes.mercadopago_routes import router as mp_router
from routes.upload_routes import router as upload_router
from routes.form_routes import router as form_router
from routes.analytics_routes import router as analytics_router
from routes.device_member_routes import router as device_member_router
from routes.security_routes import router as security_router
from routes.device_management_routes import router as device_mgmt_router
from routes.gamification_routes import router as gamification_router
from routes.routine_routes import router as routine_router
from routes.stripe_auto_routes import router as stripe_auto_router
from routes.demo_routes import router as demo_router
from routes.whmcs_routes import router as whmcs_router
from routes.redsys_routes import router as redsys_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Gym Access Control System")

# Root API endpoints
@app.get("/api/")
async def root():
    return {"message": "Gym Access Control API", "version": "2.0.0"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}



# Register all routers
app.include_router(auth_router)
app.include_router(gym_router)
app.include_router(member_router)
app.include_router(plan_router)
app.include_router(access_router)
app.include_router(device_router)
app.include_router(payment_router)
app.include_router(class_router)
app.include_router(notif_guest_router)
app.include_router(accounting_router)
app.include_router(saas_router)
app.include_router(pos_router)
app.include_router(misc_router)
app.include_router(mp_router)
app.include_router(upload_router)
app.include_router(form_router)
app.include_router(analytics_router)
app.include_router(device_member_router)
app.include_router(security_router)
app.include_router(device_mgmt_router)
app.include_router(gamification_router)
app.include_router(routine_router)
app.include_router(stripe_auto_router)
app.include_router(demo_router)
app.include_router(whmcs_router)
app.include_router(redsys_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.on_event("startup")
async def init_super_admin():
    existing = await db.admins.find_one({"role": "super_admin"})
    if not existing:
        admin = {
            "id": "sa-default",
            "email": "admin@gymaccess.com",
            "password": hash_password("admin123"),
            "name": "Super Admin",
            "role": "super_admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.admins.insert_one(admin)
        logger.info("Super admin created: admin@gymaccess.com / admin123")

async def run_daily_at_midnight(func):
    """Utility: calculates seconds until next midnight UTC, sleeps, then runs func in a loop."""
    while True:
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (tomorrow - now).total_seconds()
        logger.info(f"[CRON] Next run of {func.__name__} in {wait_seconds:.0f}s (midnight UTC)")
        await asyncio.sleep(wait_seconds)
        try:
            await func()
        except Exception as e:
            logger.error(f"[CRON] Error in {func.__name__}: {e}")

async def do_auto_suspend():
    """Suspend members whose memberships have expired."""
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
                    "suspension_type": "payment",
                    "suspension_reason": "Membresia vencida (automatico)",
                    "suspended_at": now
                }})
                suspended_count += 1
    if suspended_count > 0:
        logger.info(f"[CRON] Auto-suspended {suspended_count} members with expired memberships")

async def do_send_expiration_reminders():
    """Send email reminders for memberships expiring in 1, 3, and 7 days."""
    import aiosmtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    now = datetime.now(timezone.utc)
    reminder_days = [1, 3, 7]
    total_sent = 0

    for days in reminder_days:
        target_date = now + timedelta(days=days)
        day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end = target_date.replace(hour=23, minute=59, second=59).isoformat()

        expiring = await db.memberships.find({
            "status": "active",
            "end_date": {"$gte": day_start, "$lte": day_end}
        }, {"_id": 0}).to_list(5000)

        for ms in expiring:
            member = await db.members.find_one({"id": ms["member_id"]}, {"_id": 0})
            if not member or not member.get("email"):
                continue
            gym = await db.gyms.find_one({"id": ms.get("gym_id", member.get("gym_id"))}, {"_id": 0})
            if not gym or not gym.get("smtp_host") or not gym.get("smtp_user") or not gym.get("smtp_password"):
                continue
            plan = await db.plans.find_one({"id": ms.get("plan_id")}, {"_id": 0})
            plan_name = plan.get("name", "Plan") if plan else "Plan"
            color = gym.get("primary_color", "#E1FF01")
            gym_name = gym.get("name", "Gimnasio")
            end_date_str = ms.get("end_date", "")[:10]

            html = f"""
            <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:30px;background:#09090B;color:#fff;border-radius:16px;">
                <div style="text-align:center;margin-bottom:20px;">
                    <h1 style="color:{color};margin:0;font-size:24px;">{gym_name}</h1>
                </div>
                <h2 style="color:#FAFAFA;">Recordatorio de Vencimiento</h2>
                <p>Hola <strong>{member.get('name','Socio')}</strong>,</p>
                <p>Tu membresia <strong>{plan_name}</strong> en <strong>{gym_name}</strong> vence en <strong>{days} dia{'s' if days > 1 else ''}</strong> ({end_date_str}).</p>
                <div style="background:#18181B;padding:16px;border-radius:12px;text-align:center;margin:20px 0;">
                    <p style="color:{color};font-size:20px;font-weight:bold;margin:0;">Renueva tu membresia</p>
                    <p style="color:#a1a1aa;margin:8px 0 0;">Accede a la app para renovar y seguir entrenando.</p>
                </div>
            </div>
            """
            try:
                msg = MIMEMultipart("alternative")
                smtp_from = gym.get("smtp_from_email", gym.get("smtp_user"))
                msg["From"] = f"{gym_name} <{smtp_from}>"
                msg["To"] = member["email"]
                msg["Subject"] = f"Tu membresia vence en {days} dia{'s' if days > 1 else ''} - {gym_name}"
                msg.attach(MIMEText(html, "html"))
                smtp_port = gym.get("smtp_port", 587)
                await aiosmtplib.send(
                    msg, hostname=gym["smtp_host"], port=smtp_port,
                    username=gym["smtp_user"], password=gym["smtp_password"],
                    use_tls=smtp_port == 465, start_tls=smtp_port != 465
                )
                total_sent += 1
            except Exception as e:
                logger.warning(f"[CRON] Failed to send reminder to {member['email']}: {e}")

    if total_sent > 0:
        logger.info(f"[CRON] Sent {total_sent} expiration reminder emails")

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(run_daily_at_midnight(do_auto_suspend))
    asyncio.create_task(run_daily_at_midnight(do_send_expiration_reminders))
    # Also run auto-suspend once on startup to catch any already expired
    asyncio.create_task(do_auto_suspend())

@app.on_event("shutdown")
async def shutdown_db_client():
    from database import client
    client.close()
