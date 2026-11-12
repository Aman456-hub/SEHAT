import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.common import APIResponse
from backend.schemas.chemist import (
    ChemistCreate,
    ChemistResponse,
    StockUpdateBulk,
    ChemistStockResponse,
    MedicineResponse
)
from backend.services.medicine_service import (
    register_chemist,
    search_medicines,
    update_chemist_stock,
    get_chemist_stocks
)
from backend.services.auth_service import get_current_chemist

router = APIRouter(prefix="/api/chemists", tags=["Chemists"])
logger = logging.getLogger("chemists_router")

@router.post("", response_model=APIResponse[ChemistResponse], status_code=status.HTTP_201_CREATED)
async def create_chemist(chemist_in: ChemistCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new chemist shop profile.
    Logs the registration event.
    """
    logger.info(f"POST /api/chemists - Registering shop '{chemist_in.shop_name}'")
    try:
        chemist = await register_chemist(db, chemist_in)
        return APIResponse(
            success=True,
            data=ChemistResponse.model_validate(chemist),
            message="Chemist shop registered successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error registering chemist: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to register chemist",
            error=str(e)
        )

@router.get("/medicines/search", response_model=APIResponse[List[MedicineResponse]])
async def search_medicines_list(
    q: str = Query("", description="Generic or brand name search query"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search baseline medicines list using a query string.
    Supports autocomplete stock additions on the chemist dashboard.
    """
    logger.info(f"GET /api/chemists/medicines/search - Query: '{q}'")
    meds = await search_medicines(db, q)
    response_data = [MedicineResponse.model_validate(m) for m in meds]
    return APIResponse(
        success=True,
        data=response_data,
        message=f"Found {len(response_data)} matching medicines",
        error=None
    )

@router.post("/{chemist_id}/stock", response_model=APIResponse[List[ChemistStockResponse]])
async def update_stock(
    chemist_id: int,
    stock_in: StockUpdateBulk,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_chemist)
):
    """
    Bulk update (upsert) stock availability for a chemist.
    Logs the action.
    """
    logger.info(f"POST /api/chemists/{chemist_id}/stock - Updating {len(stock_in.stocks)} stock records")
    try:
        updated = await update_chemist_stock(db, chemist_id, stock_in)
        
        # Load relationships before returning validation
        response_data = []
        for stock in updated:
            # Re-fetch or build schema with nested medicine details
            response_data.append(ChemistStockResponse.model_validate(stock))
            
        return APIResponse(
            success=True,
            data=response_data,
            message="Chemist stock updated successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error updating stock: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to update stock",
            error=str(e)
        )

@router.get("/{chemist_id}/stock", response_model=APIResponse[List[ChemistStockResponse]])
async def get_stock(
    chemist_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_chemist)
):
    """
    Fetch all current medicine stock records for a specific chemist.
    """
    logger.info(f"GET /api/chemists/{chemist_id}/stock - Fetching stock")
    stocks = await get_chemist_stocks(db, chemist_id)
    response_data = [ChemistStockResponse.model_validate(s) for s in stocks]
    return APIResponse(
        success=True,
        data=response_data,
        message=f"Retrieved {len(response_data)} stock entries for chemist",
        error=None
    )

@router.get("/{chemist_id}", response_model=APIResponse[ChemistResponse])
async def get_chemist_by_id(chemist_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve details of a specific chemist by ID.
    Used by dashboard clients to render chemist profiles.
    """
    logger.info(f"GET /api/chemists/{chemist_id} - Fetching chemist info")
    # Fetch chemist model
    from backend.models.chemist import Chemist
    result = await db.execute(select(Chemist).where(Chemist.id == chemist_id))
    chemist = result.scalar_one_or_none()
    if not chemist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chemist with ID {chemist_id} not found"
        )
    return APIResponse(
        success=True,
        data=ChemistResponse.model_validate(chemist),
        message="Chemist details retrieved",
        error=None
    )


@router.get("", response_model=APIResponse[List[ChemistResponse]])
async def list_chemists(db: AsyncSession = Depends(get_db)):
    """
    Retrieve all registered chemists.
    """
    logger.info("GET /api/chemists - Listing all chemists")
    from backend.models.chemist import Chemist
    result = await db.execute(select(Chemist).order_by(Chemist.id.asc()))
    chemists = result.scalars().all()
    response_data = [ChemistResponse.model_validate(c) for c in chemists]
    return APIResponse(
        success=True,
        data=response_data,
        message=f"Retrieved {len(response_data)} chemists",
        error=None
    )
