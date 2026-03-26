import hmac
import hashlib
import base64
import os
import logging
import secrets
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

QR_SECRET = os.environ.get('QR_SECRET', 'qr_secret_change_me')

def generate_member_code():
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(chars) for _ in range(6))

def generate_qr_data(member_id: str, gym_id: str, timestamp: int) -> str:
    data = f"{member_id}|{gym_id}|{timestamp}"
    signature = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{data}|{signature}".encode()).decode()

def generate_static_qr_data(member_id: str, gym_id: str) -> str:
    data = f"STATIC|{member_id}|{gym_id}"
    signature = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(f"{data}|{signature}".encode()).decode()

def sanitize_qr_input(qr_code: str) -> str:
    cleaned = qr_code.strip().replace('\n', '').replace('\r', '').replace(' ', '')
    padding_needed = len(cleaned) % 4
    if padding_needed:
        cleaned += '=' * (4 - padding_needed)
    return cleaned

def validate_qr_data(qr_code: str, max_age_seconds: int = 15) -> dict:
    try:
        qr_code = sanitize_qr_input(qr_code)
        logger.info(f"QR validation - sanitized input length: {len(qr_code)}, first 30 chars: {qr_code[:30]}")
        decoded = base64.urlsafe_b64decode(qr_code.encode()).decode()
        parts = decoded.split('|')
        logger.info(f"QR validation - decoded parts count: {len(parts)}")
        
        if len(parts) == 4 and parts[0] == "STATIC":
            _, member_id, gym_id, signature = parts
            data = f"STATIC|{member_id}|{gym_id}"
            expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
            if signature != expected_sig:
                logger.warning(f"QR STATIC sig mismatch: got={signature}, expected={expected_sig}")
                return {"valid": False, "reason": "Invalid signature"}
            return {"valid": True, "member_id": member_id, "gym_id": gym_id}
        
        if len(parts) != 4:
            logger.warning(f"QR format error: expected 4 parts, got {len(parts)}: {parts}")
            return {"valid": False, "reason": "Invalid QR format"}
        
        member_id, gym_id, timestamp_str, signature = parts
        timestamp = int(timestamp_str)
        data = f"{member_id}|{gym_id}|{timestamp}"
        expected_sig = hmac.new(QR_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()[:16]
        if signature != expected_sig:
            logger.warning(f"QR DYNAMIC sig mismatch: got={signature}, expected={expected_sig}")
            return {"valid": False, "reason": "Invalid signature"}
        
        now = int(datetime.now(timezone.utc).timestamp())
        age = now - timestamp
        if age > max_age_seconds:
            logger.info(f"QR expired: age={age}s, max={max_age_seconds}s")
            return {"valid": False, "reason": "QR expired"}
        
        return {"valid": True, "member_id": member_id, "gym_id": gym_id}
    except Exception as e:
        logger.error(f"QR validation error: {e}, raw input (first 50): {qr_code[:50]}")
        return {"valid": False, "reason": "Invalid QR code"}
