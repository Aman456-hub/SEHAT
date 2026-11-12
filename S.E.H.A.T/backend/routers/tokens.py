import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.common import APIResponse
from backend.schemas.token import TokenBook, TokenResponse, TokenUpdateStatus
from backend.services.queue_service import (
    book_queue_token,
    mark_token_status,
    get_active_doctor_queue
)
from backend.services.auth_service import get_current_doctor

router = APIRouter(prefix="/api/tokens", tags=["Tokens"])
logger = logging.getLogger("tokens_router")

@router.post("", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def create_token(token_in: TokenBook, db: AsyncSession = Depends(get_db)):
    """
    Book a new token in the queue for a doctor.
    Enforces doctor availability, checks duplicate active tokens,
    and returns booked token position and estimated wait time.
    Logs the booking action.
    """
    logger.info(f"POST /api/tokens - Booking token for patient {token_in.patient_phone} with doctor {token_in.doctor_id}")
    token = await book_queue_token(db, token_in.doctor_id, token_in.patient_phone, token_in.patient_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to book token. The doctor may be unavailable or you already have an active booking."
        )

    return APIResponse(
        success=True,
        data=TokenResponse.model_validate(token),
        message="Token booked successfully",
        error=None
    )

@router.patch("/{token_id}/status", response_model=APIResponse[TokenResponse])
async def update_token_status(
    token_id: int,
    status_in: TokenUpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_doctor)
):
    """
    Update the status of a queue token (waiting, called, seen, cancelled).
    Logs the update action.
    """
    new_status = status_in.status.lower()
    if new_status not in ["waiting", "called", "seen", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be one of: waiting, called, seen, cancelled"
        )

    logger.info(f"PATCH /api/tokens/{token_id}/status - Setting status to {new_status}")
    token = await mark_token_status(db, token_id, new_status)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Token with ID {token_id} not found"
        )

    return APIResponse(
        success=True,
        data=TokenResponse.model_validate(token),
        message=f"Token status updated to {new_status}",
        error=None
    )

@router.get("/doctor/{doctor_id}", response_model=APIResponse[List[TokenResponse]])
async def get_doctor_queue(
    doctor_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_doctor)
):
    """
    Retrieve the active live queue (waiting and called tokens) for a doctor.
    Used by the doctor dashboard to view their queue in real-time.
    """
    logger.info(f"GET /api/tokens/doctor/{doctor_id} - Fetching live queue")
    queue_tokens = await get_active_doctor_queue(db, doctor_id)
    
    response_list = [TokenResponse.model_validate(token) for token in queue_tokens]
    return APIResponse(
        success=True,
        data=response_list,
        message=f"Retrieved {len(response_list)} active tokens for doctor",
        error=None
    )
