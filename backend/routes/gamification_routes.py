from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import db
from auth import get_current_admin, security, decode_jwt_token

router = APIRouter(prefix="/api")

BADGE_DEFINITIONS = [
    {"id": "first_visit", "name": "Primera Visita", "icon": "star", "description": "Completaste tu primera visita", "condition_type": "total_visits", "threshold": 1},
    {"id": "regular_10", "name": "Habitual", "icon": "fire", "description": "10 visitas totales", "condition_type": "total_visits", "threshold": 10},
    {"id": "committed_25", "name": "Comprometido", "icon": "trophy", "description": "25 visitas totales", "condition_type": "total_visits", "threshold": 25},
    {"id": "warrior_50", "name": "Guerrero", "icon": "sword", "description": "50 visitas totales", "condition_type": "total_visits", "threshold": 50},
    {"id": "legend_100", "name": "Leyenda", "icon": "crown", "description": "100 visitas totales", "condition_type": "total_visits", "threshold": 100},
    {"id": "streak_3", "name": "En Racha", "icon": "flame", "description": "3 dias consecutivos", "condition_type": "streak", "threshold": 3},
    {"id": "streak_7", "name": "Semana Perfecta", "icon": "calendar-check", "description": "7 dias consecutivos", "condition_type": "streak", "threshold": 7},
    {"id": "streak_14", "name": "Imparable", "icon": "zap", "description": "14 dias consecutivos", "condition_type": "streak", "threshold": 14},
    {"id": "streak_30", "name": "Inquebrantable", "icon": "shield", "description": "30 dias consecutivos", "condition_type": "streak", "threshold": 30},
    {"id": "early_bird", "name": "Madrugador", "icon": "sunrise", "description": "10 visitas antes de las 8am", "condition_type": "early_visits", "threshold": 10},
]

def calculate_streak(dates_set):
    if not dates_set:
        return 0, 0
    sorted_dates = sorted(dates_set, reverse=True)
    today = datetime.now(timezone.utc).date()
    current_streak = 0
    if sorted_dates[0] >= today - timedelta(days=1):
        current_streak = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i-1] - timedelta(days=1):
                current_streak += 1
            else:
                break
    max_streak = 1
    temp_streak = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i-1] - timedelta(days=1):
            temp_streak += 1
            max_streak = max(max_streak, temp_streak)
        else:
            temp_streak = 1
    return current_streak, max(max_streak, current_streak)

async def compute_member_gamification(member_id: str, gym_id: str):
    logs = await db.access_logs.find(
        {"member_id": member_id, "gym_id": gym_id, "direction": "entrada"},
        {"_id": 0, "timestamp": 1}
    ).to_list(10000)
    visit_dates = set()
    early_count = 0
    for log in logs:
        try:
            ts = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
            visit_dates.add(ts.date())
            if ts.hour < 8:
                early_count += 1
        except:
            pass
    total_visits = len(visit_dates)
    current_streak, max_streak = calculate_streak(visit_dates)
    earned_badges = []
    for badge in BADGE_DEFINITIONS:
        earned = False
        if badge["condition_type"] == "total_visits" and total_visits >= badge["threshold"]:
            earned = True
        elif badge["condition_type"] == "streak" and max_streak >= badge["threshold"]:
            earned = True
        elif badge["condition_type"] == "early_visits" and early_count >= badge["threshold"]:
            earned = True
        if earned:
            earned_badges.append(badge["id"])
    return {
        "total_visits": total_visits,
        "current_streak": current_streak,
        "max_streak": max_streak,
        "early_visits": early_count,
        "earned_badges": earned_badges,
        "all_badges": BADGE_DEFINITIONS,
        "points": total_visits * 10 + current_streak * 5 + max_streak * 3 + len(earned_badges) * 50,
    }

# ==================== Member endpoint ====================

@router.get("/gamification/me")
async def get_my_gamification(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_jwt_token(credentials.credentials)
    member_id = payload.get("sub")
    gym_id = payload.get("gym_id")
    data = await compute_member_gamification(member_id, gym_id)
    member = await db.members.find_one({"id": member_id}, {"_id": 0, "name": 1, "code": 1})
    data["member"] = member
    return data

# ==================== Admin: Ranking by gym ====================

@router.get("/gamification/ranking")
async def get_gym_ranking(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    target_gym_id = gym_id if admin["role"] == "super_admin" and gym_id else admin.get("gym_id")
    if not target_gym_id:
        return {"ranking": []}
    members = await db.members.find(
        {"gym_id": target_gym_id, "status": "active"}, {"_id": 0, "id": 1, "name": 1, "code": 1, "avatar_url": 1}
    ).to_list(500)
    ranking = []
    for m in members:
        data = await compute_member_gamification(m["id"], target_gym_id)
        ranking.append({
            "member_id": m["id"],
            "name": m["name"],
            "code": m["code"],
            "avatar_url": m.get("avatar_url"),
            "points": data["points"],
            "current_streak": data["current_streak"],
            "max_streak": data["max_streak"],
            "total_visits": data["total_visits"],
            "badges_count": len(data["earned_badges"]),
            "earned_badges": data["earned_badges"],
        })
    ranking.sort(key=lambda x: x["points"], reverse=True)
    for i, r in enumerate(ranking):
        r["rank"] = i + 1
    return {"ranking": ranking}
