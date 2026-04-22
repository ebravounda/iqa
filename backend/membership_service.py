"""
Centralized membership service.
All membership creation, expiration, and activation logic lives here.
"""
from datetime import datetime, timezone, timedelta
import uuid
import logging

from database import db

logger = logging.getLogger(__name__)


async def expire_active_memberships(member_id: str, also_pending: bool = False):
    """Expire all active memberships for a member. Optionally also expire pending_payment ones."""
    statuses = ["active"]
    if also_pending:
        statuses.append("pending_payment")
    result = await db.memberships.update_many(
        {"member_id": member_id, "status": {"$in": statuses}},
        {"$set": {"status": "expired"}}
    )
    return result.modified_count


async def create_membership(
    member_id: str,
    plan_id: str,
    gym_id: str,
    payment_method: str = None,
    payment_id: str = None,
    extra_fields: dict = None
) -> dict:
    """Create a new active membership, expiring any existing active ones first."""
    plan = await db.plans.find_one({"id": plan_id}, {"_id": 0})
    duration_days = plan.get("duration_days", 30) if plan else 30

    await expire_active_memberships(member_id, also_pending=True)

    now = datetime.now(timezone.utc)
    membership = {
        "id": str(uuid.uuid4()),
        "member_id": member_id,
        "plan_id": plan_id,
        "gym_id": gym_id,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=duration_days)).isoformat(),
        "status": "active",
        "created_at": now.isoformat(),
    }
    if payment_method:
        membership["payment_method"] = payment_method
    if payment_id:
        membership["payment_id"] = payment_id
    if extra_fields:
        membership.update(extra_fields)

    await db.memberships.insert_one(membership)
    membership.pop("_id", None)

    logger.info(f"[MEMBERSHIP] Created for member={member_id}, plan={plan_id}, method={payment_method}")
    return membership


async def activate_member(member_id: str):
    """Set member status to active and clear suspension."""
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"status": "active"}, "$unset": {"suspension_type": "", "suspension_reason": ""}}
    )


async def create_membership_and_activate(
    member_id: str,
    plan_id: str,
    gym_id: str,
    payment_method: str = None,
    payment_id: str = None,
    extra_fields: dict = None
) -> dict:
    """Create membership + activate member in one call. Used by payment gateways."""
    membership = await create_membership(
        member_id=member_id,
        plan_id=plan_id,
        gym_id=gym_id,
        payment_method=payment_method,
        payment_id=payment_id,
        extra_fields=extra_fields,
    )
    await activate_member(member_id)
    return membership
