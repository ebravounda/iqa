"""
Redsys TPV Virtual - Utility functions for HMAC SHA256 payment requests
"""
import json
import base64
import hmac
import hashlib
import uuid
from datetime import datetime, timezone
from Crypto.Cipher import DES3


REDSYS_SANDBOX_URL = "https://sis-t.redsys.es:25443/sis/realizarPago"
REDSYS_PRODUCTION_URL = "https://sis.redsys.es/sis/realizarPago"


def generate_order_number() -> str:
    """Generate valid Redsys order number (4 numeric + 8 alphanumeric = 12 chars)"""
    ts = datetime.now(timezone.utc).strftime("%m%d")
    suffix = uuid.uuid4().hex[:8].upper()
    return f"{ts}{suffix}"


def _pad_to_block(data: bytes, block_size: int = 8) -> bytes:
    """Pad data with null bytes to block_size boundary"""
    remainder = len(data) % block_size
    if remainder:
        data += b'\x00' * (block_size - remainder)
    return data


def _encrypt_3des(order_number: str, secret_key_b64: str) -> bytes:
    """Derive transaction key using 3DES(order_number, merchant_key)"""
    key_bytes = base64.b64decode(secret_key_b64)
    order_bytes = _pad_to_block(order_number.encode('utf-8'))
    cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv=b'\x00' * 8)
    return cipher.encrypt(order_bytes)


def sign_request(merchant_params_b64: str, order_number: str, secret_key_b64: str) -> str:
    """Generate HMAC SHA256 signature for Redsys request"""
    tx_key = _encrypt_3des(order_number, secret_key_b64)
    signature = hmac.new(tx_key, merchant_params_b64.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(merchant_params_b64: str, received_signature: str, order_number: str, secret_key_b64: str) -> bool:
    """Verify notification signature from Redsys"""
    expected = sign_request(merchant_params_b64, order_number, secret_key_b64)
    # URL-safe base64 comparison
    expected_safe = expected.replace('+', '-').replace('/', '_')
    received_safe = received_signature.replace('+', '-').replace('/', '_')
    return hmac.compare_digest(expected, received_signature) or hmac.compare_digest(expected_safe, received_safe)


def build_merchant_parameters(
    merchant_code: str,
    terminal: str,
    order_number: str,
    amount_cents: int,
    currency: str = "978",
    transaction_type: str = "0",
    merchant_name: str = "",
    product_description: str = "",
    titular: str = "",
    notification_url: str = "",
    url_ok: str = "",
    url_ko: str = "",
) -> str:
    """Build and base64-encode merchant parameters JSON"""
    params = {
        "DS_MERCHANT_AMOUNT": str(amount_cents),
        "DS_MERCHANT_ORDER": order_number,
        "DS_MERCHANT_MERCHANTCODE": merchant_code,
        "DS_MERCHANT_CURRENCY": currency,
        "DS_MERCHANT_TRANSACTIONTYPE": transaction_type,
        "DS_MERCHANT_TERMINAL": terminal,
        "DS_MERCHANT_MERCHANTURL": notification_url,
        "DS_MERCHANT_URLOK": url_ok,
        "DS_MERCHANT_URLKO": url_ko,
        "DS_MERCHANT_MERCHANTNAME": merchant_name,
        "DS_MERCHANT_TITULAR": titular,
        "DS_MERCHANT_PRODUCTDESCRIPTION": product_description,
        "DS_MERCHANT_CONSUMERLANGUAGE": "001",
    }
    return base64.b64encode(json.dumps(params).encode('utf-8')).decode('utf-8')


def decode_merchant_parameters(params_b64: str) -> dict:
    """Decode base64 merchant parameters from Redsys response"""
    decoded = base64.b64decode(params_b64)
    return json.loads(decoded.decode('utf-8'))


def get_redsys_url(sandbox: bool = True) -> str:
    return REDSYS_SANDBOX_URL if sandbox else REDSYS_PRODUCTION_URL


REDSYS_RESPONSE_MESSAGES = {
    "0000": "Transaccion aprobada",
    "0099": "Transaccion aprobada",
    "0101": "Tarjeta caducada",
    "0102": "Tarjeta bloqueada temporalmente",
    "0106": "Intentos de PIN excedidos",
    "0125": "Tarjeta no efectiva",
    "0129": "CVV incorrecto",
    "0180": "Tarjeta no reconocida",
    "0184": "Error de autenticacion",
    "0190": "Denegacion sin especificar",
    "0191": "Fecha de caducidad erronea",
    "0202": "Tarjeta bloqueada por fraude",
    "0904": "Error en comercio",
    "0909": "Error de sistema",
    "0912": "Emisor no disponible",
    "0913": "Pedido repetido",
    "9915": "Pago cancelado por el usuario",
}


def get_response_message(code: str) -> str:
    """Get human-readable message for Redsys response code"""
    if code in REDSYS_RESPONSE_MESSAGES:
        return REDSYS_RESPONSE_MESSAGES[code]
    code_int = int(code) if code.isdigit() else 9999
    if 0 <= code_int <= 99:
        return "Transaccion aprobada"
    return f"Transaccion denegada (codigo: {code})"
