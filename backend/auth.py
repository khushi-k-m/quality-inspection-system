from datetime import datetime, timedelta
from typing import Optional
import jwt
import hashlib
import os

SECRET_KEY = os.environ.get("JWT_SECRET", "steelvision-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Single operator account — credentials checked against env or defaults
# In production replace with a real user table
VALID_USERNAME = os.environ.get("APP_USERNAME", "admin")
VALID_PASSWORD = os.environ.get("APP_PASSWORD", "steelvision2024")


def verify_credentials(username: str, password: str) -> bool:
    return username == VALID_USERNAME and password == VALID_PASSWORD


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
