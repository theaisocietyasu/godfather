"""Signed API tokens minted by the frontend and verified by the backend.

Format: gf1.<base64url(json payload)>.<base64url(hmac-sha256)>
The HMAC covers the string "gf1.<payload>" and uses GODFATHER_TOKEN_SECRET,
which the frontend and backend share. The payload carries the Discord user
ID in "sub" and a unix expiry in "exp".
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Dict, Optional

PREFIX = 'gf1'


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


def _signature(body: str, secret: str) -> str:
    mac = hmac.new(secret.encode(), f'{PREFIX}.{body}'.encode(), hashlib.sha256)
    return _b64encode(mac.digest())


def sign(payload: Dict, secret: str) -> str:
    """Return a signed token for a payload"""
    body = _b64encode(json.dumps(payload, separators=(',', ':')).encode())
    return f'{PREFIX}.{body}.{_signature(body, secret)}'


def verify(token: str, secret: str, now: Optional[float] = None) -> Optional[Dict]:
    """Return the payload of a valid, unexpired token, or None"""
    if not token or not secret:
        return None

    parts = token.split('.')
    if len(parts) != 3 or parts[0] != PREFIX:
        return None

    _, body, signature = parts
    if not hmac.compare_digest(signature, _signature(body, secret)):
        return None

    try:
        payload = json.loads(_b64decode(body))
    except (ValueError, TypeError):
        return None

    if not isinstance(payload, dict):
        return None

    sub = payload.get('sub')
    exp = payload.get('exp')
    if not isinstance(sub, str) or not sub.isdigit():
        return None
    if not isinstance(exp, (int, float)) or exp <= (now if now is not None else time.time()):
        return None

    return payload
