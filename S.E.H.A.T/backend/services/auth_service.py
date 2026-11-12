import os
import logging
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger("auth_service")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sehat-dev-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# HTTP Bearer security scheme
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the given payload data.
    Default expiry is ACCESS_TOKEN_EXPIRE_HOURS (24h).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"JWT token created for sub={data.get('sub')} role={data.get('role')} expires={expire.isoformat()}")
    return encoded_jwt


async def verify_supabase_token(token: str) -> dict:
    """
    Validates the bearer token against the Supabase Auth API.
    Called when SUPABASE_URL and SUPABASE_ANON_KEY are configured in the environment.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_anon_key:
        raise ValueError("Supabase URL and Anon Key must be configured.")

    headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {token}"
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{supabase_url}/auth/v1/user", headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Supabase token verification failed with status {resp.status_code}: {resp.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Supabase authentication token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user_data = resp.json()
            metadata = user_data.get("user_metadata", {})
            return {
                "sub": str(user_data.get("id")),
                "email": user_data.get("email"),
                "phone": user_data.get("phone"),
                "role": metadata.get("role", "doctor"),  # default fallback role
                "name": metadata.get("name", "User")
            }
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to Supabase Auth API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable."
        )


def verify_token(token: str) -> dict:
    """
    Decode and validate a JWT token. Returns the payload dict.
    Raises HTTPException 401 if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency that extracts and validates the current user.
    Uses Supabase Auth API if SUPABASE_URL is set, otherwise falls back to local JWT signature decoding.
    """
    token = credentials.credentials
    supabase_url = os.getenv("SUPABASE_URL")
    
    if supabase_url and supabase_url.strip():
        payload = await verify_supabase_token(token)
    else:
        payload = verify_token(token)
        
    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier.",
        )
    return payload


async def require_role(required_role: str, payload: dict) -> dict:
    """
    Validates that the JWT payload contains the required role.
    Allows 'admin' to bypass and access all workspace endpoints.
    Raises 403 Forbidden if the role doesn't match.
    """
    user_role = payload.get("role")
    if user_role != required_role and user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. This endpoint requires '{required_role}' role.",
        )
    return payload


async def get_current_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: requires the caller to be an authenticated doctor."""
    payload = await get_current_user(credentials)
    return await require_role("doctor", payload)


async def get_current_chemist(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: requires the caller to be an authenticated chemist."""
    payload = await get_current_user(credentials)
    return await require_role("chemist", payload)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: requires the caller to be an authenticated admin."""
    payload = await get_current_user(credentials)
    return await require_role("admin", payload)


async def get_current_blood_bank(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: requires the caller to be an authenticated blood_bank."""
    payload = await get_current_user(credentials)
    return await require_role("blood_bank", payload)

