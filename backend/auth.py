from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import hashlib
import hmac
import os
import secrets
import sqlite3

import jwt

SECRET_KEY = os.environ.get("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

ROOT_DIR = Path(__file__).resolve().parent.parent
AUTH_DATABASE_PATH = ROOT_DIR / "database" / "inspection.db"
HASH_ITERATIONS = 310_000


def _connect():
    AUTH_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(AUTH_DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def initialize_auth_database():
    """Create the users table and optionally bootstrap one env-configured user."""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operator',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    username = os.environ.get("APP_USERNAME", "").strip()
    password = os.environ.get("APP_PASSWORD", "").strip()
    if username and password:
        conn.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, _hash_password(password), "operator"),
        )
    conn.commit()
    conn.close()


def verify_credentials(username: str, password: str) -> bool:
    initialize_auth_database()
    conn = _connect()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    conn.close()
    return bool(row and _verify_password(password, row["password_hash"]))


def get_user_role(username: str) -> Optional[str]:
    conn = _connect()
    row = conn.execute(
        "SELECT role FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    conn.close()
    return row["role"] if row else None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    if not SECRET_KEY:
        raise RuntimeError("JWT_SECRET is not configured")
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    if not SECRET_KEY:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
