from __future__ import annotations

import hashlib
import hmac


def hash_password(raw_password: str) -> str:
    digest = hashlib.sha256(raw_password.encode("utf-8")).hexdigest()
    return f"sha256${digest}"


def verify_password(raw_password: str, stored_hash: str) -> bool:
    if not stored_hash.startswith("sha256$"):
        return False
    expected = hash_password(raw_password)
    return hmac.compare_digest(expected, stored_hash)

