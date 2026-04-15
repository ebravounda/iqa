"""
Redsys TPV Virtual - Utility functions using official redsys library (v0.3.1)
"""
from redsys import Client
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def generate_order_number() -> str:
    """Generate valid Redsys order number (4 numeric + 8 alphanumeric = 12 chars)"""
    ts = datetime.now(timezone.utc).strftime("%m%d")
    suffix = uuid.uuid4().hex[:8].upper()
    return f"{ts}{suffix}"


def _ensure_valid_key(secret_key_b64: str) -> str:
    """Ensure the secret key decodes to a valid 3DES key length (16 or 24 bytes)"""
    import base64
    decoded = base64.b64decode(secret_key_b64)
    if len(decoded) in (16, 24):
        return secret_key_b64
    if len(decoded) == 12:
        padded = decoded * 2  # 12 -> 24 bytes
        return base64.b64encode(padded).decode()
    if len(decoded) == 8:
        padded = decoded * 3  # 8 -> 24 bytes
        return base64.b64encode(padded).decode()
    # Generic: repeat until >= 24, then trim
    padded = (decoded * 3)[:24]
    return base64.b64encode(padded).decode()


def create_redsys_form_data(
    secret_key: str,
    merchant_code: str,
    terminal: str,
    order_number: str,
    amount: float,
    sandbox: bool = True,
    merchant_name: str = "",
    product_description: str = "",
    titular: str = "",
    notification_url: str = "",
    url_ok: str = "",
    url_ko: str = "",
) -> dict:
    """Create Redsys form data using the official redsys library"""
    client = Client(
        business_code=merchant_code,
        secret_key=secret_key,
        sandbox=sandbox,
    )

    # Amount in EUR as float - library converts to cents internally (amount * 100)
    amount_eur = float(amount)

    params = {
        "DS_MERCHANT_AMOUNT": amount_eur,
        "DS_MERCHANT_ORDER": order_number,
        "DS_MERCHANT_MERCHANTCODE": merchant_code,
        "DS_MERCHANT_CURRENCY": "978",
        "DS_MERCHANT_TRANSACTIONTYPE": "0",
        "DS_MERCHANT_TERMINAL": terminal,
        "DS_MERCHANT_MERCHANTURL": notification_url,
        "DS_MERCHANT_URLOK": url_ok,
        "DS_MERCHANT_URLKO": url_ko,
        "DS_MERCHANT_MERCHANTNAME": merchant_name,
        "DS_MERCHANT_TITULAR": titular,
        "DS_MERCHANT_PRODUCTDESCRIPTION": product_description,
        "DS_MERCHANT_CONSUMERLANGUAGE": "001",
    }

    args = client.redsys_generate_request(params)

    return {
        "redsys_url": client.redsys_url,
        "Ds_SignatureVersion": args.get("Ds_SignatureVersion", "HMAC_SHA256_V1"),
        "Ds_MerchantParameters": args.get("Ds_MerchantParameters", ""),
        "Ds_Signature": args.get("Ds_Signature", ""),
    }


def verify_redsys_response(secret_key: str, merchant_code: str, signature: str, merchant_parameters: str, sandbox: bool = True) -> dict:
    """Verify and decode Redsys notification response"""
    client = Client(
        business_code=merchant_code,
        secret_key=secret_key,
        sandbox=sandbox,
    )
    params = client.decode_parameters(merchant_parameters)
    order_number = params.get("Ds_Order", "")
    response_code = params.get("Ds_Response", "9999")

    # Verify signature
    computed_signature = client.redsys_generate_request({
        "Ds_Merchant_Order": order_number,
    })
    # For notification verification, recompute from params
    encrypted_order = client.encrypt_order_with_3DES(order_number)
    expected_sig = client.sign_hmac256(encrypted_order, merchant_parameters.encode())

    response_int = int(response_code) if response_code.isdigit() else 9999
    is_paid = 0 <= response_int <= 99

    return {
        "is_paid": is_paid,
        "order": order_number,
        "response_code": response_code,
        "params": params,
        "expected_signature": expected_sig.decode() if isinstance(expected_sig, bytes) else expected_sig,
    }


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
    if code in REDSYS_RESPONSE_MESSAGES:
        return REDSYS_RESPONSE_MESSAGES[code]
    code_int = int(code) if code.isdigit() else 9999
    if 0 <= code_int <= 99:
        return "Transaccion aprobada"
    return f"Transaccion denegada (codigo: {code})"
