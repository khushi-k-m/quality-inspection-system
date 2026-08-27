from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.auth import get_user_role, verify_credentials, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    if not verify_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    token = create_access_token({
        "sub": body.username,
        "role": get_user_role(body.username) or "operator",
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": body.username,
        "role": "operator"
    }


@router.post("/logout")
def logout():
    # JWT is stateless; client discards the token
    return {"message": "Logged out successfully"}
