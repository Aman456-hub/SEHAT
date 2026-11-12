import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.common import APIResponse
from backend.schemas.doctor import DoctorCreate, DoctorResponse, DoctorUpdateAvailability, NearbyDoctorResponse
from backend.services.queue_service import register_doctor, toggle_doctor_availability
from backend.services.location_service import get_nearby_available_doctors
from backend.services.auth_service import get_current_doctor

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])
logger = logging.getLogger("doctors_router")

@router.post("", response_model=APIResponse[DoctorResponse], status_code=status.HTTP_201_CREATED)
async def create_doctor(doctor_in: DoctorCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new doctor clinic profile.
    Logs the registration event.
    """
    logger.info(f"POST /api/doctors - Registering doctor with phone {doctor_in.phone}")
    try:
        doctor = await register_doctor(db, doctor_in)
        return APIResponse(
            success=True,
            data=DoctorResponse.model_validate(doctor),
            message="Doctor registered successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error registering doctor: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to register doctor",
            error=str(e)
        )

@router.patch("/{doctor_id}/availability", response_model=APIResponse[DoctorResponse])
async def update_availability(
    doctor_id: int,
    availability: DoctorUpdateAvailability,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_doctor)
):
    """
    Toggle a doctor's availability status.
    If toggled to false, will cancel all waiting queue tokens and notify patients.
    Logs the update action.
    """
    logger.info(f"PATCH /api/doctors/{doctor_id}/availability - Setting availability to {availability.is_available}")
    doctor = await toggle_doctor_availability(db, doctor_id, availability.is_available)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found"
        )
    
    return APIResponse(
        success=True,
        data=DoctorResponse.model_validate(doctor),
        message=f"Doctor availability updated to {availability.is_available}",
        error=None
    )

@router.get("/nearby", response_model=APIResponse[List[NearbyDoctorResponse]])
async def get_nearby_doctors(
    latitude: float = Query(..., description="Patient current latitude"),
    longitude: float = Query(..., description="Patient current longitude"),
    db: AsyncSession = Depends(get_db)
):
    """
    Find nearby available doctors from the patient's coordinates.
    Implements search radius auto-expansion rules (2km default, 5km fallback).
    """
    logger.info(f"GET /api/doctors/nearby - Location: ({latitude}, {longitude})")
    nearby_data = await get_nearby_available_doctors(db, latitude, longitude)
    
    response_list = []
    for doctor, distance in nearby_data:
        # Map doctor to NearbyDoctorResponse, calculating distance details
        response_list.append(
            NearbyDoctorResponse(
                id=doctor.id,
                name=doctor.name,
                phone=doctor.phone,
                clinic_name=doctor.clinic_name,
                address=doctor.address,
                latitude=doctor.latitude,
                longitude=doctor.longitude,
                specialization=doctor.specialization,
                avg_consultation_minutes=doctor.avg_consultation_minutes,
                is_available=doctor.is_available,
                created_at=doctor.created_at,
                updated_at=doctor.updated_at,
                distance_km=round(distance, 2),
                # If they are at the top of the queue, estimated wait is 0,
                # otherwise estimate based on queue position
                estimated_wait_minutes=0  # Wait service computes this dynamically
            )
        )
        
    return APIResponse(
        success=True,
        data=response_list,
        message=f"Found {len(response_list)} available doctors nearby",
        error=None
    )

@router.get("/prescriptions", response_model=APIResponse)
async def get_doctor_prescriptions(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_doctor)):
    """
    Retrieve prescription scans history for clinical review.
    """
    logger.info("GET /api/doctors/prescriptions - Fetching prescription scans history")
    try:
        from backend.models.token import PrescriptionLog
        result = await db.execute(select(PrescriptionLog).order_by(PrescriptionLog.created_at.desc()))
        logs = result.scalars().all()
        data = [{
            "id": l.id,
            "patient_phone": l.patient_phone,
            "image_url": l.image_url,
            "ocr_confidence": l.ocr_confidence,
            "extracted_medicines": l.extracted_medicines,
            "hindi_explanation": l.hindi_explanation,
            "created_at": l.created_at.isoformat() if l.created_at else None
        } for l in logs]
        return APIResponse(
            success=True,
            data=data,
            message="Prescription logs retrieved successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error fetching prescriptions: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to retrieve prescription logs",
            error=str(e)
        )


@router.get("", response_model=APIResponse[List[DoctorResponse]])
async def list_doctors(db: AsyncSession = Depends(get_db)):
    """
    Retrieve all registered doctors.
    """
    logger.info("GET /api/doctors - Listing all doctors")
    from backend.models.doctor import Doctor
    result = await db.execute(select(Doctor).order_by(Doctor.id.asc()))
    doctors = result.scalars().all()
    response_data = [DoctorResponse.model_validate(d) for d in doctors]
    return APIResponse(
        success=True,
        data=response_data,
        message=f"Retrieved {len(response_data)} doctors",
        error=None
    )


@router.get("/{doctor_id}", response_model=APIResponse[DoctorResponse])
async def get_doctor_by_id(doctor_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve details of a specific doctor by ID.
    Used by dashboard clients to render doctor profiles.
    """
    logger.info(f"GET /api/doctors/{doctor_id} - Fetching doctor info")
    # Fetch doctor model
    from backend.models.doctor import Doctor
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found"
        )
    return APIResponse(
        success=True,
        data=DoctorResponse.model_validate(doctor),
        message="Doctor details retrieved",
        error=None
    )
