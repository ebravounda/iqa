from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from database import db
from auth import get_current_admin, check_role
from models import CustomFormCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

@router.post("/forms")
async def create_custom_form(form: CustomFormCreate, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    form_dict = form.model_dump()
    form_dict["id"] = str(uuid.uuid4())
    form_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    form_dict["created_by"] = admin["id"]
    await db.custom_forms.insert_one(form_dict)
    form_dict.pop("_id", None)
    return form_dict

@router.get("/forms")
async def get_forms(gym_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"active": True}
    if admin["role"] != "super_admin":
        query["gym_id"] = admin.get("gym_id")
    elif gym_id:
        query["gym_id"] = gym_id
    forms = await db.custom_forms.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return forms

@router.get("/forms/public/{gym_id}")
async def get_public_forms(gym_id: str):
    forms = await db.custom_forms.find(
        {"gym_id": gym_id, "active": True, "show_on_registration": True}, {"_id": 0}
    ).to_list(10)
    return forms

@router.put("/forms/{form_id}")
async def update_form(form_id: str, body: dict, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    allowed = ["name", "description", "fields", "active", "show_on_registration"]
    update_data = {k: v for k, v in body.items() if k in allowed and v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.custom_forms.update_one({"id": form_id}, {"$set": update_data})
    form = await db.custom_forms.find_one({"id": form_id}, {"_id": 0})
    return form

@router.delete("/forms/{form_id}")
async def delete_form(form_id: str, admin: dict = Depends(get_current_admin)):
    check_role(admin, ["super_admin", "gym_admin"])
    await db.custom_forms.update_one({"id": form_id}, {"$set": {"active": False}})
    return {"message": "Formulario eliminado"}

@router.post("/forms/{form_id}/responses")
async def submit_form_response(form_id: str, body: dict):
    form = await db.custom_forms.find_one({"id": form_id, "active": True}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")
    response_dict = {
        "id": str(uuid.uuid4()),
        "form_id": form_id,
        "form_name": form.get("name"),
        "gym_id": form.get("gym_id"),
        "member_id": body.get("member_id"),
        "responses": body.get("responses", {}),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.form_responses.insert_one(response_dict)
    response_dict.pop("_id", None)
    return response_dict

@router.get("/forms/{form_id}/responses")
async def get_form_responses(form_id: str, admin: dict = Depends(get_current_admin)):
    responses = await db.form_responses.find({"form_id": form_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    for r in responses:
        if r.get("member_id"):
            member = await db.members.find_one({"id": r["member_id"]}, {"_id": 0, "name": 1, "code": 1})
            r["member"] = member
    return responses

@router.get("/members/{member_id}/form-responses")
async def get_member_form_responses(member_id: str, admin: dict = Depends(get_current_admin)):
    responses = await db.form_responses.find({"member_id": member_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return responses
