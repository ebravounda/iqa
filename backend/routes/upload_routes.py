from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Response, Query, Header
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging

from database import db
from auth import get_current_admin, security, decode_jwt_token
from storage import put_object, get_object, init_storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

@router.post("/upload/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    payload = decode_jwt_token(credentials.credentials)
    user_id = payload.get("sub")
    
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes (JPG, PNG, WEBP)")
    
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 2MB")
    
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    
    path = f"gymaccess/avatars/{user_id}/{uuid.uuid4()}.{ext}"
    
    try:
        result = put_object(path, data, file.content_type or "image/jpeg")
        storage_path = result.get("path", path)
        
        # Save file record
        file_record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "storage_path": storage_path,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": len(data),
            "file_type": "avatar",
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.files.insert_one(file_record)
        
        # Update member avatar
        avatar_url = f"/api/files/{storage_path}"
        await db.members.update_one(
            {"id": user_id},
            {"$set": {"avatar_path": storage_path, "avatar_url": avatar_url, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"storage_path": storage_path, "avatar_url": avatar_url, "message": "Avatar subido correctamente"}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")

@router.post("/upload/avatar/admin/{member_id}")
async def upload_avatar_admin(
    member_id: str,
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes (JPG, PNG, WEBP)")
    
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 2MB")
    
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    
    path = f"gymaccess/avatars/{member_id}/{uuid.uuid4()}.{ext}"
    
    try:
        result = put_object(path, data, file.content_type or "image/jpeg")
        storage_path = result.get("path", path)
        
        file_record = {
            "id": str(uuid.uuid4()),
            "user_id": member_id,
            "storage_path": storage_path,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": len(data),
            "file_type": "avatar",
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.files.insert_one(file_record)
        
        await db.members.update_one(
            {"id": member_id},
            {"$set": {"avatar_path": storage_path, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"storage_path": storage_path, "message": "Avatar subido correctamente"}
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")

@router.get("/files/{path:path}")
async def serve_file(path: str, auth: Optional[str] = Query(None), authorization: Optional[str] = Header(None)):
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    except Exception as e:
        logger.error(f"File serve error: {e}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

@router.post("/upload/gym-logo/{gym_id}")
async def upload_gym_logo(
    gym_id: str,
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    gym = await db.gyms.find_one({"id": gym_id}, {"_id": 0})
    if not gym:
        raise HTTPException(status_code=404, detail="Gimnasio no encontrado")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes (JPG, PNG, WEBP)")
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 2MB")
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    path = f"gymaccess/logos/{gym_id}/{uuid.uuid4()}.{ext}"
    try:
        result = put_object(path, data, file.content_type or "image/jpeg")
        storage_path = result.get("path", path)
        # Build the full URL for the logo
        logo_url = f"/api/files/{storage_path}"
        await db.gyms.update_one(
            {"id": gym_id},
            {"$set": {"logo_url": logo_url, "logo_path": storage_path, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return {"logo_url": logo_url, "storage_path": storage_path, "message": "Logo subido correctamente"}
    except Exception as e:
        logger.error(f"Gym logo upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir logo: {str(e)}")


@router.post("/upload/product-image/{product_id}")
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    product = await db.pos_products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Solo se permiten imagenes (JPG, PNG, WEBP)")
    
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 2MB")
    
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "jpg"
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    
    path = f"gymaccess/products/{product_id}/{uuid.uuid4()}.{ext}"
    
    try:
        result = put_object(path, data, file.content_type or "image/jpeg")
        storage_path = result.get("path", path)
        
        file_record = {
            "id": str(uuid.uuid4()),
            "user_id": product_id,
            "storage_path": storage_path,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": len(data),
            "file_type": "product_image",
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.files.insert_one(file_record)
        
        await db.pos_products.update_one(
            {"id": product_id},
            {"$set": {"image_path": storage_path, "image_url": f"/api/files/{storage_path}", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"storage_path": storage_path, "message": "Imagen de producto subida correctamente"}
    except Exception as e:
        logger.error(f"Product image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir imagen: {str(e)}")
