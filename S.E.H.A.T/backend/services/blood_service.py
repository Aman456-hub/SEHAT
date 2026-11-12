import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models.blood_bank import BloodBank, BloodStock
from backend.schemas.blood_bank import BloodBankCreate, BloodStockUpdateBulk
from backend.services.location_service import calculate_haversine_distance

logger = logging.getLogger("blood_service")


def normalize_blood_group(query: str) -> Optional[str]:
    """
    Normalizes input text format into standard blood group codes.
    Accepts: 'BLOOD B+', 'KHOON B+', 'B+ blood', 'b positive', 'b+', 'B POSITIVE'
    Returns standard VARCHAR(3) code like 'B+', 'O-', 'AB+', or None if invalid.
    """
    q = query.upper().replace("KHOON", "").replace("BLOOD", "").replace(" ", "").strip()
    
    # Textual word normalization
    if "POSITIVE" in q:
        q = q.replace("POSITIVE", "+")
    if "NEGATIVE" in q:
        q = q.replace("NEGATIVE", "-")
        
    valid_groups = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}
    if q in valid_groups:
        return q
        
    # Check if they sent just letters and sign (e.g. "B+")
    for group in valid_groups:
        if q == group.replace("+", "") or q == group:
            return group
            
    return None


async def register_blood_bank(db: AsyncSession, data: BloodBankCreate) -> BloodBank:
    """Register a new blood bank clinic in the database."""
    logger.info(f"Registering blood bank '{data.name}' at address '{data.address}'")
    new_bank = BloodBank(
        name=data.name,
        address=data.address,
        phone=data.phone,
        latitude=data.latitude,
        longitude=data.longitude,
        is_open_24hrs=data.is_open_24hrs,
        opening_time=data.opening_time,
        closing_time=data.closing_time
    )
    db.add(new_bank)
    await db.commit()
    await db.refresh(new_bank)
    return new_bank


async def update_blood_stock(db: AsyncSession, blood_bank_id: int, stocks_data: BloodStockUpdateBulk) -> List[BloodStock]:
    """Bulk update or insert (upsert) blood stock availability counts for a blood bank."""
    logger.info(f"Updating blood stocks for bank ID {blood_bank_id}")
    updated_records = []
    
    for item in stocks_data.stocks:
        # Check if record already exists
        stmt = select(BloodStock).where(
            and_(
                BloodStock.blood_bank_id == blood_bank_id,
                BloodStock.blood_group == item.blood_group
            )
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        
        if record:
            record.units_available = item.units_available
            record.last_updated = datetime.now()
        else:
            record = BloodStock(
                blood_bank_id=blood_bank_id,
                blood_group=item.blood_group,
                units_available=item.units_available,
                last_updated=datetime.now()
            )
            db.add(record)
            
        updated_records.append(record)
        
    await db.commit()
    return updated_records


async def get_blood_bank_stock(db: AsyncSession, blood_bank_id: int) -> List[BloodStock]:
    """Retrieve all current inventory stock details for a specific blood bank."""
    stmt = select(BloodStock).where(BloodStock.blood_bank_id == blood_bank_id).order_by(BloodStock.blood_group)
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def search_nearby_blood(db: AsyncSession, blood_group: str, latitude: float, longitude: float) -> List[dict]:
    """
    Search blood banks with positive units (> 0) for a given blood group.
    Applies radius expansion rules:
      - Default search: 2km radius
      - Second pass: if no banks found, expand to 5km radius
      - Emergency pass: if still no results, find the absolute closest bank regardless of distance (Blood Emergency Rule 5)
    Marks stocks older than 12 hours as unverified (Rule 4).
    Filters out banks with 0 units (Rule 9).
    """
    logger.info(f"Searching nearby blood banks for {blood_group} near ({latitude}, {longitude})")
    
    # 1. Query all blood stocks with units > 0 matching the blood group, eager loading their blood bank details
    stmt = (
        select(BloodStock)
        .where(
            and_(
                BloodStock.blood_group == blood_group,
                BloodStock.units_available > 0
            )
        )
        .options(selectinload(BloodStock.blood_bank))
    )
    res = await db.execute(stmt)
    all_stocks = res.scalars().all()
    
    if not all_stocks:
        logger.info(f"No blood banks found with positive units of {blood_group} anywhere.")
        return []
        
    # Calculate distance for all candidates
    candidates = []
    stale_hours = int(os.getenv("BLOOD_STOCK_STALE_HOURS", "12"))
    now = datetime.now()
    
    for stock in all_stocks:
        bank = stock.blood_bank
        dist = calculate_haversine_distance(latitude, longitude, bank.latitude, bank.longitude)
        
        # Check if verified (updated within the last 12 hours)
        is_verified = (now - stock.last_updated) <= timedelta(hours=stale_hours)
        
        candidates.append({
            "stock": stock,
            "bank": bank,
            "distance": round(dist, 2),
            "is_verified": is_verified
        })
        
    # Sort candidates by distance (closest first)
    candidates.sort(key=lambda x: x["distance"])
    
    default_radius = float(os.getenv("DEFAULT_SEARCH_RADIUS_KM", 2.0))
    max_radius = float(os.getenv("MAX_SEARCH_RADIUS_KM", 5.0))
    
    # 1. Filter within default radius (2km)
    results = [c for c in candidates if c["distance"] <= default_radius]
    if results:
        logger.info(f"Found {len(results)} blood banks within default {default_radius}km radius.")
        return results
        
    # 2. Filter within maximum radius (5km)
    results = [c for c in candidates if c["distance"] <= max_radius]
    if results:
        logger.info(f"Found {len(results)} blood banks within expanded {max_radius}km radius.")
        return results
        
    # 3. Emergency Pass: Return the absolute closest available blood bank regardless of distance
    logger.info(f"No blood banks within {max_radius}km. Returning the closest available bank at {candidates[0]['distance']}km (Emergency Fallback).")
    return [candidates[0]]
