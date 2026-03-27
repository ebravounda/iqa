from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone, timedelta
from database import db
from auth import get_current_admin

router = APIRouter(prefix="/api/security")

MAX_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 15

async def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"

async def is_ip_blocked(ip: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    block = await db.blocked_ips.find_one({"ip": ip, "blocked_until": {"$gt": now}}, {"_id": 0})
    return block is not None

async def record_failed_attempt(ip: str, email_or_code: str, attempt_type: str, user_agent: str = ""):
    now = datetime.now(timezone.utc)
    await db.login_attempts.insert_one({
        "ip": ip,
        "identifier": email_or_code,
        "type": attempt_type,
        "user_agent": user_agent,
        "timestamp": now.isoformat(),
        "success": False
    })
    cutoff = (now - timedelta(minutes=BLOCK_DURATION_MINUTES)).isoformat()
    recent_fails = await db.login_attempts.count_documents({
        "ip": ip,
        "success": False,
        "timestamp": {"$gte": cutoff}
    })
    if recent_fails >= MAX_ATTEMPTS:
        blocked_until = (now + timedelta(minutes=BLOCK_DURATION_MINUTES)).isoformat()
        await db.blocked_ips.update_one(
            {"ip": ip},
            {"$set": {
                "ip": ip,
                "blocked_until": blocked_until,
                "reason": f"{recent_fails} intentos fallidos en {BLOCK_DURATION_MINUTES} min",
                "blocked_at": now.isoformat(),
                "last_identifier": email_or_code,
                "type": attempt_type
            }},
            upsert=True
        )
        return True
    return False

async def record_successful_login(ip: str, email_or_code: str, attempt_type: str):
    await db.login_attempts.insert_one({
        "ip": ip,
        "identifier": email_or_code,
        "type": attempt_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": True
    })

# --- Super Admin Endpoints ---

@router.get("/blocked-ips")
async def get_blocked_ips(admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    now = datetime.now(timezone.utc).isoformat()
    active_blocks = await db.blocked_ips.find(
        {"blocked_until": {"$gt": now}}, {"_id": 0}
    ).sort("blocked_at", -1).to_list(500)
    expired_blocks = await db.blocked_ips.find(
        {"blocked_until": {"$lte": now}}, {"_id": 0}
    ).sort("blocked_at", -1).to_list(100)
    return {"active": active_blocks, "expired": expired_blocks}

@router.delete("/blocked-ips/{ip}")
async def unblock_ip(ip: str, admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    result = await db.blocked_ips.delete_one({"ip": ip})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="IP no encontrada")
    return {"message": f"IP {ip} desbloqueada"}

@router.delete("/blocked-ips")
async def unblock_all_ips(admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    result = await db.blocked_ips.delete_many({})
    return {"message": f"{result.deleted_count} IPs desbloqueadas"}

@router.get("/login-attempts")
async def get_login_attempts(
    admin: dict = Depends(get_current_admin),
    limit: int = 100,
    attempt_type: str = None,
    success: bool = None
):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    query = {}
    if attempt_type:
        query["type"] = attempt_type
    if success is not None:
        query["success"] = success
    attempts = await db.login_attempts.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    return {"attempts": attempts, "total": len(attempts)}

@router.get("/stats")
async def get_security_stats(admin: dict = Depends(get_current_admin)):
    if admin["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Solo super admin")
    now = datetime.now(timezone.utc)
    last_24h = (now - timedelta(hours=24)).isoformat()
    last_7d = (now - timedelta(days=7)).isoformat()
    active_blocks = await db.blocked_ips.count_documents({"blocked_until": {"$gt": now.isoformat()}})
    fails_24h = await db.login_attempts.count_documents({"success": False, "timestamp": {"$gte": last_24h}})
    fails_7d = await db.login_attempts.count_documents({"success": False, "timestamp": {"$gte": last_7d}})
    success_24h = await db.login_attempts.count_documents({"success": True, "timestamp": {"$gte": last_24h}})
    total_blocks = await db.blocked_ips.count_documents({})
    return {
        "active_blocks": active_blocks,
        "total_blocks_history": total_blocks,
        "failed_24h": fails_24h,
        "failed_7d": fails_7d,
        "success_24h": success_24h
    }
