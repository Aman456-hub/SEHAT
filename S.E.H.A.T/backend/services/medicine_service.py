import logging
import os
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.models.chemist import Chemist, ChemistStock, Medicine
from backend.schemas.chemist import ChemistCreate, StockUpdateBulk
from backend.services.location_service import calculate_haversine_distance

logger = logging.getLogger("medicine_service")

async def register_chemist(db: AsyncSession, chemist_data: ChemistCreate) -> Chemist:
    """
    Register a new chemist shop profile in the database.
    Saves shop details, contact phone, and location coordinates.
    Every service function must have a docstring.
    """
    db_chemist = Chemist(
        name=chemist_data.name,
        shop_name=chemist_data.shop_name,
        phone=chemist_data.phone,
        address=chemist_data.address,
        latitude=chemist_data.latitude,
        longitude=chemist_data.longitude,
        is_open=chemist_data.is_open
    )
    db.add(db_chemist)
    await db.commit()
    await db.refresh(db_chemist)
    logger.info(f"Chemist registered: {db_chemist.shop_name} (ID: {db_chemist.id})")
    return db_chemist

async def search_medicines(db: AsyncSession, query: str) -> List[Medicine]:
    """
    Search baseline medicines list using generic name or brand name.
    Matches case-insensitively across both criteria.
    """
    result = await db.execute(select(Medicine))
    all_medicines = result.scalars().all()

    if not query:
        return list(all_medicines)

    q_clean = query.strip().lower()
    matched = []

    for med in all_medicines:
        # Check generic name substring match
        if q_clean in med.generic_name.lower():
            matched.append(med)
            continue
        
        # Check brand names array match
        brand_match = False
        for brand in med.brand_names:
            if q_clean in brand.lower():
                brand_match = True
                break
        
        if brand_match:
            matched.append(med)

    return matched

async def update_chemist_stock(db: AsyncSession, chemist_id: int, stock_data: StockUpdateBulk) -> List[ChemistStock]:
    """
    Perform a bulk upsert of medicine stocks for a chemist shop.
    Sets is_available boolean, updates the last_updated timestamp,
    and returns the list of modified stocks.
    """
    updated_stocks = []
    
    for item in stock_data.stocks:
        # Check if stock record already exists for this chemist-medicine combo
        stmt = select(ChemistStock).where(
            and_(
                ChemistStock.chemist_id == chemist_id,
                ChemistStock.medicine_id == item.medicine_id
            )
        )
        result = await db.execute(stmt)
        stock_record = result.scalar_one_or_none()

        if stock_record:
            # Update existing record
            stock_record.is_available = item.is_available
            stock_record.last_updated = datetime.now()
        else:
            # Create a new stock record
            stock_record = ChemistStock(
                chemist_id=chemist_id,
                medicine_id=item.medicine_id,
                is_available=item.is_available,
                last_updated=datetime.now()
            )
            db.add(stock_record)
            
        updated_stocks.append(stock_record)

    await db.commit()
    logger.info(f"Updated {len(updated_stocks)} stock listings for Chemist ID: {chemist_id}")
    
    # Eagerly load the updated stock records with their medicine relationship
    updated_ids = [stock.id for stock in updated_stocks]
    if not updated_ids:
        return []
        
    stmt = (
        select(ChemistStock)
        .where(ChemistStock.id.in_(updated_ids))
        .options(selectinload(ChemistStock.medicine))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def get_chemist_stocks(db: AsyncSession, chemist_id: int) -> List[ChemistStock]:
    """
    Retrieve all stock records for a specific chemist, including nested medicine relationships.
    """
    stmt = (
        select(ChemistStock)
        .where(ChemistStock.chemist_id == chemist_id)
        .options(selectinload(ChemistStock.medicine))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def match_chemist_stocks(
    db: AsyncSession,
    medicine_names: List[str],
    latitude: float,
    longitude: float
) -> dict:
    """
    Match a list of requested medicine names against local chemist stock listings.
    Applies distance filtering, auto-expanding search radius (2km to 5km),
    generic/brand matching logic, staleness warnings, and partial combination fallbacks.
    Every service function must have a docstring.
    """
    # 1. Fetch all open chemist profiles
    stmt_chemists = select(Chemist).where(Chemist.is_open == True)
    res_chemists = await db.execute(stmt_chemists)
    all_chemists = res_chemists.scalars().all()
    
    if not all_chemists:
        logger.info("No open chemist shops registered in the database.")
        return {"type": "none"}
        
    # Calculate distance to each chemist
    chemists_with_dist = []
    for chemist in all_chemists:
        dist = calculate_haversine_distance(latitude, longitude, chemist.latitude, chemist.longitude)
        chemists_with_dist.append((chemist, dist))
        
    # 2. Filter chemists within radius (Business Rule 4: Default 5km, expanding up to 25km)
    default_radius = float(os.getenv("DEFAULT_SEARCH_RADIUS_KM", 5.0))
    max_radius = float(os.getenv("MAX_SEARCH_RADIUS_KM", 25.0))
    
    in_range = [item for item in chemists_with_dist if item[1] <= default_radius]
    radius_applied = default_radius
    
    if not in_range:
        logger.info(f"No chemists found within default {default_radius}km. Expanding radius to {max_radius}km.")
        in_range = [item for item in chemists_with_dist if item[1] <= max_radius]
        radius_applied = max_radius
        
    if not in_range:
        logger.warning(f"No chemists found within maximum {max_radius}km limit.")
        return {"type": "none"}

    # 3. Resolve requested input names to Medicine records (Fuzzy Bidirectional Matching)
    res_meds = await db.execute(select(Medicine))
    all_meds = res_meds.scalars().all()
    
    import re
    def normalize_med_token(text: str) -> str:
        # Strip common prescription words and units: tab, syp, mg, ml, etc.
        t = re.sub(r"\b(tab|tablet|tablets|syp|syrup|cap|capsule|inj|injection|mg|ml|gm)\b", "", text, flags=re.IGNORECASE)
        return re.sub(r"[^a-zA-Z0-9\s]", "", t).strip().lower()

    cleaned_names = [n.strip() for n in medicine_names if n.strip()]
    matched_med_ids = []
    med_id_to_obj = {}
    
    for raw_name in cleaned_names:
        norm_name = normalize_med_token(raw_name)
        tokens = [tk for tk in norm_name.split() if len(tk) >= 3]
        
        for med in all_meds:
            gen_clean = normalize_med_token(med.generic_name)
            brand_cleans = [normalize_med_token(b) for b in med.brand_names]
            
            is_match = False
            # 1. Exact or substring match on generic name (must be at least 3 chars)
            if norm_name and gen_clean and len(gen_clean) >= 3:
                if norm_name in gen_clean or gen_clean in norm_name:
                    is_match = True
                elif any(tk in gen_clean for tk in tokens if len(tk) >= 3):
                    is_match = True

            # 2. Check brands (must be at least 3 chars)
            if not is_match:
                for b_clean in brand_cleans:
                    if not b_clean or len(b_clean) < 3:
                        continue
                    if norm_name and (norm_name in b_clean or b_clean in norm_name):
                        is_match = True
                        break
                    if any(tk in b_clean for tk in tokens if len(tk) >= 3):
                        is_match = True
                        break
                        
            if is_match and med.id not in matched_med_ids:
                matched_med_ids.append(med.id)
                med_id_to_obj[med.id] = med
                break

    if not matched_med_ids:
        logger.warning(f"No database medicine entries matched requested search names: {medicine_names}")
        return {"type": "none"}

    target_set = set(matched_med_ids)
    stale_hours = float(os.getenv("STOCK_STALE_HOURS", 24.0))
    chemist_stock_profiles = []

    # 4. Gather stock profiles for each chemist in range
    for chemist, dist in in_range:
        stmt_stocks = select(ChemistStock).where(
            and_(
                ChemistStock.chemist_id == chemist.id,
                ChemistStock.medicine_id.in_(matched_med_ids),
                ChemistStock.is_available == True
            )
        )
        res_stocks = await db.execute(stmt_stocks)
        stocks_found = res_stocks.scalars().all()
        
        avail_ids = set()
        stale_ids = set()
        
        for stock in stocks_found:
            avail_ids.add(stock.medicine_id)
            # Business Rule 3: check if stock listing is stale (> 24 hours since last update)
            diff_hours = (datetime.now() - stock.last_updated).total_seconds() / 3600.0
            if diff_hours >= stale_hours:
                stale_ids.add(stock.medicine_id)
                
        chemist_stock_profiles.append({
            "chemist": chemist,
            "distance": dist,
            "available_ids": avail_ids,
            "stale_ids": stale_ids
        })

    # 5. Search for a single chemist with ALL medicines (Full Match)
    full_match_profiles = []
    for profile in chemist_stock_profiles:
        if target_set.issubset(profile["available_ids"]):
            full_match_profiles.append(profile)
            
    if full_match_profiles:
        # Select the closest full match chemist
        full_match_profiles.sort(key=lambda x: x["distance"])
        best = full_match_profiles[0]
        any_stale = len(best["stale_ids"]) > 0
        
        # Build clean strings for matching medicines details
        matched_meds_details = [
            f"{med_id_to_obj[mid].generic_name} ({', '.join(med_id_to_obj[mid].brand_names)})"
            for mid in target_set
        ]
        
        stale_names = [med_id_to_obj[mid].generic_name for mid in best["stale_ids"]]
        
        return {
            "type": "full",
            "chemist": best["chemist"],
            "distance": round(best["distance"], 1),
            "is_verified": not any_stale,
            "stale_medicines": stale_names,
            "medicines": matched_meds_details
        }

    # 6. Fallback: Search for best pair of chemists that cover the target list (Business Rule 6)
    best_pair = None
    best_coverage_count = 0
    min_combined_dist = float("inf")
    n_profiles = len(chemist_stock_profiles)
    
    for i in range(n_profiles):
        for j in range(i + 1, n_profiles):
            p1 = chemist_stock_profiles[i]
            p2 = chemist_stock_profiles[j]
            
            union_avail = p1["available_ids"].union(p2["available_ids"])
            coverage = len(union_avail.intersection(target_set))
            
            if coverage > best_coverage_count:
                best_coverage_count = coverage
                best_pair = (p1, p2)
                min_combined_dist = p1["distance"] + p2["distance"]
            elif coverage == best_coverage_count and coverage > 0:
                combined_dist = p1["distance"] + p2["distance"]
                if combined_dist < min_combined_dist:
                    best_pair = (p1, p2)
                    min_combined_dist = combined_dist

    if best_pair:
        p1, p2 = best_pair
        any_stale_1 = len(p1["stale_ids"]) > 0
        any_stale_2 = len(p2["stale_ids"]) > 0
        
        # Identify which medicines are available at which chemist
        m1_names = [med_id_to_obj[mid].generic_name for mid in p1["available_ids"].intersection(target_set)]
        m2_names = [med_id_to_obj[mid].generic_name for mid in p2["available_ids"].intersection(target_set)]
        
        return {
            "type": "combination",
            "chemist_1": p1["chemist"],
            "distance_1": round(p1["distance"], 1),
            "is_verified_1": not any_stale_1,
            "medicines_1": m1_names,
            "chemist_2": p2["chemist"],
            "distance_2": round(p2["distance"], 1),
            "is_verified_2": not any_stale_2,
            "medicines_2": m2_names,
            "coverage_count": best_coverage_count,
            "total_needed": len(target_set)
        }

    return {"type": "none"}

