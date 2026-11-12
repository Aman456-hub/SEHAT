import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models.doctor import Doctor
from backend.models.chemist import Chemist
from backend.models.admin import Admin
from backend.models.blood_bank import BloodBank
from backend.services.auth_service import (
    verify_password,
    create_access_token,
    get_current_user,
)
from backend.schemas.common import APIResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
logger = logging.getLogger("auth_router")


class LoginRequest(BaseModel):
    """Login request body accepting phone/email + password + role."""
    identifier: str  # phone for doctor/chemist, email for admin
    password: str
    role: str  # "doctor", "chemist", or "admin"


@router.post("/login", response_model=APIResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user by phone/email + password + role.
    Returns a JWT access token and user profile on success.
    """
    logger.info(f"Login attempt: role={body.role}, identifier={body.identifier}")

    role = body.role.lower().strip()
    identifier = body.identifier.strip()

    if role == "doctor":
        result = await db.execute(select(Doctor).where(Doctor.phone == identifier))
        user = result.scalar_one_or_none()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone number or password.")

        token = create_access_token({"sub": str(user.id), "role": "doctor", "name": user.name})
        return APIResponse(
            success=True,
            data={
                "token": token,
                "role": "doctor",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "phone": user.phone,
                    "clinic_name": user.clinic_name,
                    "specialization": user.specialization,
                },
            },
            message=f"Welcome, Dr. {user.name}!",
            error=None,
        )

    elif role == "chemist":
        result = await db.execute(select(Chemist).where(Chemist.phone == identifier))
        user = result.scalar_one_or_none()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone number or password.")

        token = create_access_token({"sub": str(user.id), "role": "chemist", "name": user.name})
        return APIResponse(
            success=True,
            data={
                "token": token,
                "role": "chemist",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "phone": user.phone,
                    "shop_name": user.shop_name,
                },
            },
            message=f"Welcome, {user.name}!",
            error=None,
        )

    elif role == "admin":
        result = await db.execute(select(Admin).where(Admin.email == identifier))
        user = result.scalar_one_or_none()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        token = create_access_token({"sub": str(user.id), "role": "admin", "name": user.name})
        return APIResponse(
            success=True,
            data={
                "token": token,
                "role": "admin",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                },
            },
            message=f"Welcome, {user.name}!",
            error=None,
        )

    elif role == "blood_bank":
        result = await db.execute(select(BloodBank).where(BloodBank.phone == identifier))
        user = result.scalar_one_or_none()
        if not user or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone number or password.")

        token = create_access_token({"sub": str(user.id), "role": "blood_bank", "name": user.name})
        return APIResponse(
            success=True,
            data={
                "token": token,
                "role": "blood_bank",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "phone": user.phone,
                },
            },
            message=f"Welcome, {user.name}!",
            error=None,
        )

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role. Must be 'doctor', 'chemist', 'admin', or 'blood_bank'.")


@router.get("/me", response_model=APIResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile from the JWT payload.
    Requires a valid Bearer token.
    """
    logger.info(f"GET /api/auth/me - user={current_user.get('sub')}, role={current_user.get('role')}")
    return APIResponse(
        success=True,
        data={
            "id": current_user.get("sub"),
            "role": current_user.get("role"),
            "name": current_user.get("name"),
        },
        message="Authenticated user profile.",
        error=None,
    )
