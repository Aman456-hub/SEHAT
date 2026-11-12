import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.common import APIResponse
from backend.schemas.blood_bank import (
    BloodBankCreate,
    BloodBankResponse,
    BloodStockUpdateBulk,
    BloodStockResponse
)
from backend.services.blood_service import (
    register_blood_bank,
    get_blood_bank_stock,
    update_blood_stock
)
from backend.services.auth_service import get_current_admin, get_current_blood_bank

router = APIRouter(prefix="/api/blood-banks", tags=["Blood Banks"])
logger = logging.getLogger("blood_banks_router")


@router.post("", response_model=APIResponse[BloodBankResponse], status_code=status.HTTP_201_CREATED)
async def create_blood_bank(
    bank_in: BloodBankCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Register a new blood bank profile in the system.
    Protected: Only Admin roles can register new blood banks.
    """
    logger.info(f"POST /api/blood-banks - Registering bank '{bank_in.name}'")
    try:
        bank = await register_blood_bank(db, bank_in)
        return APIResponse(
            success=True,
            data=BloodBankResponse.model_validate(bank),
            message="Blood bank registered successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error registering blood bank: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to register blood bank",
            error=str(e)
        )


@router.post("/{bank_id}/stock", response_model=APIResponse[List[BloodStockResponse]])
async def update_stock(
    bank_id: int,
    stock_in: BloodStockUpdateBulk,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_blood_bank)
):
    """
    Bulk update (upsert) available blood group units for a blood bank.
    Protected: Requires authenticated blood_bank role.
    """
    logger.info(f"POST /api/blood-banks/{bank_id}/stock - Updating {len(stock_in.stocks)} stock records")
    try:
        updated = await update_blood_stock(db, bank_id, stock_in)
        response_data = [BloodStockResponse.model_validate(stock) for stock in updated]
        return APIResponse(
            success=True,
            data=response_data,
            message="Blood stock updated successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error updating blood stock: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to update blood stock",
            error=str(e)
        )


@router.get("/{bank_id}/stock", response_model=APIResponse[List[BloodStockResponse]])
async def get_stock(
    bank_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_blood_bank)
):
    """
    Fetch all current blood group inventory levels for a specific blood bank.
    Protected: Requires authenticated blood_bank role.
    """
    logger.info(f"GET /api/blood-banks/{bank_id}/stock - Fetching stock levels")
    stocks = await get_blood_bank_stock(db, bank_id)
    response_data = [BloodStockResponse.model_validate(s) for s in stocks]
    return APIResponse(
        success=True,
        data=response_data,
        message="Retrieved current blood stock levels",
        error=None
    )


@router.get("/{bank_id}", response_model=APIResponse[BloodBankResponse])
async def get_blood_bank_by_id(bank_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve profile details of a specific blood bank by ID.
    Publicly accessible.
    """
    logger.info(f"GET /api/blood-banks/{bank_id} - Fetching profile details")
    from backend.models.blood_bank import BloodBank
    result = await db.execute(select(BloodBank).where(BloodBank.id == bank_id))
    bank = result.scalar_one_or_none()
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blood bank with ID {bank_id} not found"
        )
    return APIResponse(
        success=True,
        data=BloodBankResponse.model_validate(bank),
        message="Blood bank details retrieved",
        error=None
    )


@router.get("", response_model=APIResponse[List[BloodBankResponse]])
async def list_blood_banks(db: AsyncSession = Depends(get_db)):
    """
    Retrieve all registered blood banks.
    """
    logger.info("GET /api/blood-banks - Listing all blood banks")
    from backend.models.blood_bank import BloodBank
    result = await db.execute(select(BloodBank).order_by(BloodBank.id.asc()))
    banks = result.scalars().all()
    response_data = [BloodBankResponse.model_validate(b) for b in banks]
    return APIResponse(
        success=True,
        data=response_data,
        message=f"Retrieved {len(response_data)} blood banks",
        error=None
    )
