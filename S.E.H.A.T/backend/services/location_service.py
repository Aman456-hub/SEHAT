import math
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.doctor import Doctor

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in kilometers.
    """
    R = 6371.0  # Earth's radius in kilometers

    # Convert coordinates to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Apply Haversine formula
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c

    return distance

async def get_nearby_available_doctors(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    default_radius_km: float = 5.0,
    max_radius_km: float = 25.0
) -> List[Tuple[Doctor, float]]:
    """
    Query available doctors from the database and filter by proximity.
    Enforces the business rule: Search first within default_radius_km (2km).
    If no available doctors are found, expand search up to max_radius_km (5km).
    Returns a list of tuples containing the Doctor object and their distance in km,
    sorted by proximity (closest first).
    """
    # Fetch all doctors who are currently marked as available
    result = await db.execute(select(Doctor).where(Doctor.is_available == True))
    all_available_doctors = result.scalars().all()

    nearby_doctors = []
    
    # 1. First Pass: Search within default_radius_km
    for doctor in all_available_doctors:
        dist = calculate_haversine_distance(latitude, longitude, doctor.latitude, doctor.longitude)
        if dist <= default_radius_km:
            nearby_doctors.append((doctor, dist))
            
    # 2. Second Pass: If no results found, expand search to max_radius_km
    if not nearby_doctors and max_radius_km > default_radius_km:
        for doctor in all_available_doctors:
            dist = calculate_haversine_distance(latitude, longitude, doctor.latitude, doctor.longitude)
            if dist <= max_radius_km:
                nearby_doctors.append((doctor, dist))

    # Sort results by distance (closest first)
    nearby_doctors.sort(key=lambda x: x[1])
    return nearby_doctors
