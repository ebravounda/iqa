from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging

from database import db
from auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.get("/analytics/overview")
async def get_analytics_overview(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    gid = admin.get("gym_id") if admin["role"] != "super_admin" else gym_id
    query = {"gym_id": gid} if gid else {}
    
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today.replace(day=1)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    
    # Member counts
    active = await db.members.count_documents({**query, "status": "active"})
    suspended = await db.members.count_documents({**query, "status": "suspended"})
    total = await db.members.count_documents(query)
    
    # New members this month vs last month
    new_this_month = await db.members.count_documents({**query, "created_at": {"$gte": month_start.isoformat()}})
    new_last_month = await db.members.count_documents({**query, "created_at": {"$gte": prev_month_start.isoformat(), "$lt": month_start.isoformat()}})
    
    # Retention: members active now who were also active last month
    retention_rate = round((active / total * 100), 1) if total > 0 else 0
    
    # Access today
    today_accesses = await db.access_logs.count_documents({**({"gym_id": gid} if gid else {}), "timestamp": {"$gte": today.isoformat()}})
    
    return {
        "total_members": total,
        "active_members": active,
        "suspended_members": suspended,
        "new_this_month": new_this_month,
        "new_last_month": new_last_month,
        "member_growth": new_this_month - new_last_month,
        "retention_rate": retention_rate,
        "today_accesses": today_accesses,
    }

@router.get("/analytics/hourly-heatmap")
async def get_hourly_heatmap(gym_id: Optional[str] = None, days: int = 30, admin: dict = Depends(get_current_admin)):
    gid = admin.get("gym_id") if admin["role"] != "super_admin" else gym_id
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).isoformat()
    query = {"timestamp": {"$gte": start}}
    if gid:
        query["gym_id"] = gid
    
    logs = await db.access_logs.find(query, {"_id": 0, "timestamp": 1}).to_list(50000)
    
    day_names = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
    heatmap = {}
    for d in range(7):
        for h in range(24):
            heatmap[f"{d}-{h}"] = 0
    
    for log in logs:
        try:
            ts = log["timestamp"]
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            weekday = dt.weekday()
            hour = dt.hour
            heatmap[f"{weekday}-{hour}"] = heatmap.get(f"{weekday}-{hour}", 0) + 1
        except:
            pass
    
    result = []
    for d in range(7):
        for h in range(24):
            result.append({"day": d, "day_name": day_names[d], "hour": h, "count": heatmap.get(f"{d}-{h}", 0)})
    
    return result

@router.get("/analytics/revenue-comparison")
async def get_revenue_comparison(gym_id: Optional[str] = None, months: int = 6, admin: dict = Depends(get_current_admin)):
    gid = admin.get("gym_id") if admin["role"] != "super_admin" else gym_id
    now = datetime.now(timezone.utc)
    
    monthly_data = []
    month_names_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for i in range(months - 1, -1, -1):
        month_date = now - timedelta(days=i * 30)
        m_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            next_m = (m_start + timedelta(days=32)).replace(day=1)
        else:
            next_m = now
        
        # Membership revenue
        pay_query = {"payment_status": "paid", "created_at": {"$gte": m_start.isoformat(), "$lt": next_m.isoformat()}}
        if gid:
            pay_query["gym_id"] = gid
        transactions = await db.payment_transactions.find(pay_query, {"_id": 0, "amount": 1}).to_list(5000)
        membership_rev = sum(t.get("amount", 0) for t in transactions)
        
        # POS revenue
        pos_query = {"created_at": {"$gte": m_start.isoformat(), "$lt": next_m.isoformat()}}
        if gid:
            pos_query["gym_id"] = gid
        pos_sales = await db.pos_sales.find(pos_query, {"_id": 0, "total": 1}).to_list(5000)
        pos_rev = sum(s.get("total", 0) for s in pos_sales)
        
        monthly_data.append({
            "month": month_names_es[m_start.month - 1],
            "year": m_start.year,
            "membresias": round(membership_rev, 2),
            "pos": round(pos_rev, 2),
            "total": round(membership_rev + pos_rev, 2),
        })
    
    return monthly_data

@router.get("/analytics/member-retention")
async def get_member_retention(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    gid = admin.get("gym_id") if admin["role"] != "super_admin" else gym_id
    now = datetime.now(timezone.utc)
    
    monthly_retention = []
    month_names_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=i * 30)
        m_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_m = (m_start + timedelta(days=32)).replace(day=1)
        
        query = {} if not gid else {"gym_id": gid}
        
        total_at_month = await db.members.count_documents({**query, "created_at": {"$lt": next_m.isoformat()}})
        active_at_month = await db.memberships.count_documents({
            **({"gym_id": gid} if gid else {}),
            "status": "active",
            "start_date": {"$lt": next_m.isoformat()},
            "end_date": {"$gte": m_start.isoformat()}
        })
        
        new_members = await db.members.count_documents({
            **query,
            "created_at": {"$gte": m_start.isoformat(), "$lt": next_m.isoformat()}
        })
        
        rate = round((active_at_month / total_at_month * 100), 1) if total_at_month > 0 else 0
        
        monthly_retention.append({
            "month": month_names_es[m_start.month - 1],
            "total": total_at_month,
            "active": active_at_month,
            "new": new_members,
            "retention": rate,
        })
    
    return monthly_retention

@router.get("/analytics/peak-hours")
async def get_peak_hours(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    gid = admin.get("gym_id") if admin["role"] != "super_admin" else gym_id
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=30)).isoformat()
    
    query = {"timestamp": {"$gte": start}, "direction": "entrada"}
    if gid:
        query["gym_id"] = gid
    
    logs = await db.access_logs.find(query, {"_id": 0, "timestamp": 1}).to_list(50000)
    
    hourly = {h: 0 for h in range(24)}
    for log in logs:
        try:
            hour = int(log["timestamp"][11:13])
            hourly[hour] += 1
        except:
            pass
    
    total_days = 30
    result = [{"hour": f"{h:02d}:00", "entries": hourly[h], "avg": round(hourly[h] / total_days, 1)} for h in range(24)]
    
    peak = max(result, key=lambda x: x["entries"]) if result else None
    
    return {"hourly": result, "peak_hour": peak}
