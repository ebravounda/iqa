import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Local storage directory
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/opt/gymaccess/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def init_storage():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return "local"

def put_object(path: str, data: bytes, content_type: str) -> dict:
    file_path = UPLOAD_DIR / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(data)
    logger.info(f"File saved locally: {path} ({len(data)} bytes)")
    return {"path": path}

def get_object(path: str) -> tuple:
    file_path = UPLOAD_DIR / path
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    data = file_path.read_bytes()
    ext = file_path.suffix.lower()
    content_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    content_type = content_types.get(ext, "application/octet-stream")
    return data, content_type
