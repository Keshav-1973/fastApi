from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
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

# Validate env
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing in .env")

if not EXPIRE_MIN:
    raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES is missing in .env")

EXPIRE_MIN = int(EXPIRE_MIN)


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


# -------------------------
# JWT utils
# -------------------------

def create_access_token(data: dict) -> str:
    """
    Create JWT token
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode JWT token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except JWTError:
        raise Exception("Invalid or expired token")