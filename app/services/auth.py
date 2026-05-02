from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from typing import Optional
from uuid import uuid4
import hashlib
import os

# Load env
load_dotenv()

# Password hashing config
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# Env variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")

# Validate env
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing in .env")

if not EXPIRE_MIN:
    raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES is missing in .env")

if not REFRESH_EXPIRE_DAYS:
    raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS is missing in .env")

EXPIRE_MIN = int(EXPIRE_MIN)
REFRESH_EXPIRE_DAYS = int(REFRESH_EXPIRE_DAYS)


# -------------------------
# Password utils
# -------------------------

def _pre_hash(password: str) -> str:
    """
    Pre-hash password using SHA256 to avoid bcrypt 72-byte limit
    """
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(_pre_hash(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_pre_hash(plain), hashed)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# -------------------------
# JWT utils
# -------------------------

def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + expires_delta

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": token_type,
        "jti": str(uuid4()),
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict) -> str:
    """
    Create access JWT token
    """
    return _create_token(data, timedelta(minutes=EXPIRE_MIN), "access")


def create_refresh_token(data: dict) -> str:
    """
    Create refresh JWT token
    """
    return _create_token(data, timedelta(days=REFRESH_EXPIRE_DAYS), "refresh")


def get_refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)


def decode_token(token: str, expected_type: Optional[str] = None) -> dict:
    """
    Decode JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if expected_type and token_type != expected_type:
            raise ValueError("Invalid token type")
        return payload

    except JWTError:
        raise ValueError("Invalid or expired token")