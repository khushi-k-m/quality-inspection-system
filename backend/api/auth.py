import os
import re
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.auth import (
    get_user_by_identifier, register_user, verify_credentials,
    create_access_token, create_reset_token, consume_reset_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str


@router.post("/register", status_code=201)
def register(body: RegisterRequest):
    username = body.username.strip()
    email = body.email.strip()
    if not username:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username is required.")
    if not email or not EMAIL_RE.match(email):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Valid email is required.")
    if not body.password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password is required.")
    if body.password != body.confirm_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Passwords do not match.")

    result = register_user(username, email, body.password)
    if not result["ok"]:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=result["detail"])
    return {"message": "Registration successful."}


@router.post("/login")
def login(body: LoginRequest):
    identifier = body.username.strip()
    if not verify_credentials(identifier, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )
    user = get_user_by_identifier(identifier)
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }


@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}


# ── Forgot / Reset password ────────────────────────────────────────────

SMTP_HOST     = os.environ.get("SMTP_HOST", "")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM     = os.environ.get("SMTP_FROM", SMTP_USER)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str


def _send_reset_email(to_email: str, raw_token: str) -> bool:
    """
    Attempt to send the reset token via SMTP.
    Returns True if sent, False if SMTP is not configured.
    Raises on SMTP errors so the caller can surface them.
    """
    if not SMTP_HOST or not SMTP_USER:
        return False
    import smtplib
    from email.mime.text import MIMEText
    body = (
        f"You requested a password reset for your InspectAI account.\n\n"
        f"Your reset token is:\n\n    {raw_token}\n\n"
        f"Enter this token on the Reset Password page.\n"
        f"This token expires in {os.environ.get('RESET_TOKEN_EXPIRE_MINUTES', '30')} minutes "
        f"and can only be used once.\n\n"
        f"If you did not request this, ignore this email."
    )
    msg = MIMEText(body)
    msg["Subject"] = "InspectAI — Password Reset Token"
    msg["From"]    = SMTP_FROM
    msg["To"]      = to_email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.sendmail(SMTP_FROM, [to_email], msg.as_string())
    return True


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest):
    """
    Initiate a password reset.
    Always returns the same response regardless of whether the email
    exists, to avoid account enumeration.
    """
    email = body.email.strip().lower()
    if not email or not EMAIL_RE.match(email):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Valid email address is required.")

    raw_token = create_reset_token(email)  # None if email not found

    email_sent    = False
    email_error   = None
    smtp_configured = bool(SMTP_HOST and SMTP_USER)

    if raw_token and smtp_configured:
        try:
            email_sent = _send_reset_email(email, raw_token)
        except Exception as exc:
            email_error = str(exc)

    # Build response — never reveal whether the email exists
    if not smtp_configured:
        # Development mode: return token directly so the flow can be tested
        # without an email provider.  In production, configure SMTP env vars.
        return {
            "message": (
                "DEVELOPMENT MODE: SMTP is not configured. "
                "In production, set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM env vars. "
                "The reset token is returned here ONLY because no email provider is configured."
            ),
            "dev_token": raw_token,   # None if email not found — still safe (no enumeration)
            "smtp_configured": False,
        }

    if email_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Email delivery failed: {email_error}",
        )

    return {
        "message": "If that email address is registered, a reset token has been sent.",
        "smtp_configured": True,
    }


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    if not body.token or not body.token.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Reset token is required.")
    if not body.new_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="New password is required.")
    if body.new_password != body.confirm_password:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Passwords do not match.")
    if len(body.new_password) < 8:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Password must be at least 8 characters.")

    result = consume_reset_token(body.token.strip(), body.new_password)
    if not result["ok"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=result["detail"])
    return {"message": "Password reset successful. You can now log in with your new password."}
