from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from database import db
from auth import hash_password
from datetime import datetime, timezone
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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

async def auto_suspend_expired_memberships():
    while True:
        try:
            await asyncio.sleep(3600)
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
                            "suspension_reason": "Membresia vencida (automatico)",
                            "suspended_at": now
                        }})
                        suspended_count += 1
            if suspended_count > 0:
                logger.info(f"Auto-suspended {suspended_count} members with expired memberships")
        except Exception as e:
            logger.error(f"Error in auto-suspend task: {e}")

@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(auto_suspend_expired_memberships())

@app.on_event("shutdown")
async def shutdown_db_client():
    from database import client
    client.close()
