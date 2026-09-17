from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import hashlib
import hmac
import os
import secrets
import sqlite3

import jwt
from dotenv import load_dotenv

# Load .env from project root (parent of backend/)
_ROOT_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ROOT_ENV, override=False)

SECRET_KEY = os.environ.get("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

ROOT_DIR = Path(__file__).resolve().parent.parent
AUTH_DATABASE_PATH = ROOT_DIR / "database" / "users.db"
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


# Password-reset token expiry in minutes (configurable via env var)
RESET_TOKEN_EXPIRE_MINUTES = int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", "30"))


def initialize_auth_database():
    """Create the users and password_reset_tokens tables in users.db."""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL DEFAULT '',
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operator',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Only a HASH of the token is stored — never the raw token
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def register_user(username: str, email: str, password: str) -> dict:
    """
    Register a new user. Returns {'ok': True} or {'ok': False, 'field': ..., 'detail': ...}.
    Never stores plaintext password.
    """
    initialize_auth_database()
    username = username.strip()
    email = email.strip().lower()
    conn = _connect()
    try:
        existing = conn.execute(
            "SELECT username, email FROM users WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if existing:
            if existing["username"] == username:
                return {"ok": False, "field": "username", "detail": "Username already taken."}
            return {"ok": False, "field": "email", "detail": "Email already registered."}
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role, is_active) VALUES (?, ?, ?, 'operator', 1)",
            (username, email, _hash_password(password)),
        )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


def verify_credentials(identifier: str, password: str) -> bool:
    """Accept username or email as identifier."""
    initialize_auth_database()
    identifier = identifier.strip()
    conn = _connect()
    row = conn.execute(
        "SELECT password_hash FROM users WHERE (username = ? OR email = ?) AND is_active = 1",
        (identifier, identifier.lower()),
    ).fetchone()
    conn.close()
    return bool(row and _verify_password(password, row["password_hash"]))


def get_user_by_identifier(identifier: str) -> Optional[dict]:
    """Return user dict (without password_hash) for username or email."""
    conn = _connect()
    row = conn.execute(
        "SELECT id, username, email, role FROM users WHERE (username = ? OR email = ?) AND is_active = 1",
        (identifier.strip(), identifier.strip().lower()),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


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


# ── Password-reset token helpers ──────────────────────────────────────

def _hash_reset_token(raw_token: str) -> str:
    """SHA-256 hash of the raw reset token (stored in DB)."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_reset_token(email: str) -> Optional[str]:
    """
    If *email* belongs to an active account, generate a cryptographically
    random single-use reset token, store only its hash, and return the
    raw token (to be delivered out-of-band).

    Returns None if the email is not found — caller must NOT reveal this
    distinction to the end user.
    """
    initialize_auth_database()
    email = email.strip().lower()
    conn = _connect()
    row = conn.execute(
        "SELECT id FROM users WHERE email = ? AND is_active = 1", (email,)
    ).fetchone()
    if row is None:
        conn.close()
        return None

    user_id   = row["id"]
    raw_token = secrets.token_urlsafe(32)
    tok_hash  = _hash_reset_token(raw_token)
    expires   = (
        datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    ).strftime("%Y-%m-%d %H:%M:%S")

    # Invalidate any existing unused tokens for this user
    conn.execute(
        "UPDATE password_reset_tokens SET used = 1 WHERE user_id = ? AND used = 0",
        (user_id,),
    )
    conn.execute(
        "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, tok_hash, expires),
    )
    conn.commit()
    conn.close()
    return raw_token


def consume_reset_token(raw_token: str, new_password: str) -> dict:
    """
    Validate *raw_token*, update the password, and invalidate the token.

    Returns {'ok': True} or {'ok': False, 'detail': str}.
    Uses the EXISTING _hash_password / PBKDF2 system.
    """
    initialize_auth_database()
    tok_hash = _hash_reset_token(raw_token)
    now      = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    conn = _connect()
    row = conn.execute(
        """
        SELECT prt.id, prt.user_id, prt.expires_at, prt.used
        FROM password_reset_tokens prt
        WHERE prt.token_hash = ?
        """,
        (tok_hash,),
    ).fetchone()

    if row is None or row["used"]:
        conn.close()
        return {"ok": False, "detail": "Invalid or already-used reset token."}

    if row["expires_at"] < now:
        conn.close()
        return {"ok": False, "detail": "Reset token has expired."}

    new_hash = _hash_password(new_password)
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_hash, row["user_id"]),
    )
    conn.execute(
        "UPDATE password_reset_tokens SET used = 1 WHERE id = ?",
        (row["id"],),
    )
    conn.commit()
    conn.close()
    return {"ok": True}
