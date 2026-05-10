import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

try:
    from jose import JWTError, jwt
except ImportError:
    JWTError = ValueError
    jwt = None

try:
    from passlib.context import CryptContext
except ImportError:
    CryptContext = None

from app.config import settings

password_context = (
    CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None
)


def _base64url_encode(value: bytes) -> str:
    """Encode bytes using unpadded base64url for JWT fallback support."""
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    """Decode unpadded base64url text for JWT fallback support."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    """Hash a plaintext password for database storage."""
    if password_context:
        return password_context.hash(password)

    salt = secrets.token_hex(16)
    iterations = 260000
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plaintext password matches a stored hash."""
    if password_context:
        return password_context.verify(password, password_hash)

    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected)


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for a user id."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at}
    if jwt:
        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    fallback_payload = {"sub": subject, "exp": int(expires_at.timestamp())}
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header).encode("utf-8")),
            _base64url_encode(json.dumps(fallback_payload).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_access_token(token: str) -> str:
    """Decode a JWT access token and return its subject user id."""
    if jwt is None:
        return _decode_fallback_access_token(token)

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise ValueError("Invalid authentication token") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("Invalid authentication token")
    return subject


def _decode_fallback_access_token(token: str) -> str:
    """Decode a fallback HS256 JWT when python-jose is unavailable."""
    try:
        header_text, payload_text, signature_text = token.split(".", 2)
        signing_input = f"{header_text}.{payload_text}"
        expected_signature = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        provided_signature = _base64url_decode(signature_text)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("Invalid authentication token")
        payload = json.loads(_base64url_decode(payload_text))
    except Exception as exc:
        raise ValueError("Invalid authentication token") from exc

    if int(payload.get("exp") or 0) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Invalid authentication token")
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("Invalid authentication token")
    return subject


def _fernet() -> Fernet:
    """Build a Fernet instance from the configured application secret."""
    digest = hashlib.sha256(settings.JWT_SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: str | None) -> str | None:
    """Encrypt a sensitive string before storing it in the database."""
    if value is None:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    """Decrypt a sensitive string read from the database."""
    if value is None:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored secret could not be decrypted") from exc
