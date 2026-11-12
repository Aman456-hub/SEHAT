import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.common import APIResponse
from backend.models.doctor import Doctor
from backend.models.chemist import Chemist, ChemistStock, Medicine
from backend.models.blood_bank import BloodBank
from backend.models.token import QueueToken, PrescriptionLog
from backend.services.auth_service import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Admin Analytics"])
logger = logging.getLogger("admin_router")

@router.get("/analytics", response_model=APIResponse)
async def get_analytics(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    """
    Retrieve platform-wide analytics for the dashboard view.
    Every service/router endpoint must log its execution.
    """
    logger.info("GET /api/admin/analytics - Accessing server metrics")
    try:
        # Total tokens booked historically
        tokens_res = await db.execute(select(func.count(QueueToken.id)))
        total_tokens = tokens_res.scalar() or 0

        # Current active queue (waiting status)
        active_res = await db.execute(select(func.count(QueueToken.id)).where(QueueToken.status == "waiting"))
        active_tokens = active_res.scalar() or 0

        # Scanned prescriptions
        scans_res = await db.execute(select(func.count(PrescriptionLog.id)))
        scans_count = scans_res.scalar() or 0

        # Registered doctors
        docs_res = await db.execute(select(func.count(Doctor.id)))
        docs_count = docs_res.scalar() or 0

        # Registered chemists
        chem_res = await db.execute(select(func.count(Chemist.id)))
        chem_count = chem_res.scalar() or 0

        # Registered blood banks
        banks_res = await db.execute(select(func.count(BloodBank.id)))
        banks_count = banks_res.scalar() or 0

        # Cataloged medicine listings
        meds_res = await db.execute(select(func.count(Medicine.id)))
        meds_count = meds_res.scalar() or 0

        # Build responsive stats object
        data_payload = {
            "total_tokens_booked": total_tokens,
            "active_queue_count": active_tokens,
            "prescriptions_scanned": scans_count,
            "registered_doctors": docs_count,
            "registered_chemists": chem_count,
            "registered_blood_banks": banks_count,
            "total_medicines_cataloged": meds_count,
            "top_medicines": [
                {"name": "Paracetamol 500mg", "count": scans_count},
                {"name": "Cetirizine 10mg", "count": max(0, scans_count - 1)}
            ]
        }

        return APIResponse(
            success=True,
            data=data_payload,
            message="Successfully loaded platform metrics",
            error=None
        )
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to retrieve server metrics",
            error=str(e)
        )


@router.get("/patients", response_model=APIResponse)
async def get_patients(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    """
    Retrieve list of all registered patients.
    """
    logger.info("GET /api/admin/patients - Fetching patient directory")
    try:
        from backend.models.patient import Patient
        result = await db.execute(select(Patient).order_by(Patient.created_at.desc()))
        patients = result.scalars().all()
        data = [{
            "id": p.id,
            "phone": p.phone,
            "name": p.name,
            "language_preference": p.language_preference,
            "created_at": p.created_at.isoformat() if p.created_at else None
        } for p in patients]
        return APIResponse(
            success=True,
            data=data,
            message="Patients directory retrieved successfully",
            error=None
        )
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}")
        return APIResponse(
            success=False,
            data=None,
            message="Failed to retrieve patients",
            error=str(e)
        )


@router.get("/prescriptions", response_model=APIResponse)
async def get_prescriptions(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_admin)):
    """
    Retrieve scan history log of all analyzed prescriptions.
    """
    logger.info("GET /api/admin/prescriptions - Fetching prescription scans history")
    try:
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


from pydantic import BaseModel
from typing import Optional
from backend.services.notification_service import send_whatsapp_notification

class TestNotificationRequest(BaseModel):
    phone: str
    preset_id: Optional[str] = "2"
    custom_message: Optional[str] = None

@router.post("/test-notification", response_model=APIResponse)
async def trigger_test_notification(payload: TestNotificationRequest):
    """
    Trigger any preset or custom test notification to a patient's WhatsApp.
    Useful for testing UltraMsg gateway delivery without advancing actual patient queues.
    """
    logger.info(f"POST /api/admin/test-notification - Sending preset {payload.preset_id} to {payload.phone}")
    from test_notifications import NOTIFICATION_PRESETS

    msg = payload.custom_message
    if not msg:
        preset = NOTIFICATION_PRESETS.get(payload.preset_id, NOTIFICATION_PRESETS["2"])
        msg = preset["message"]

    success = await send_whatsapp_notification(payload.phone, msg)
    if success:
        return APIResponse(
            success=True,
            data={"phone": payload.phone, "preset_id": payload.preset_id, "sent": True},
            message=f"WhatsApp test notification sent successfully to {payload.phone}",
            error=None
        )
    else:
        return APIResponse(
            success=False,
            data={"phone": payload.phone, "sent": False},
            message="Failed to deliver WhatsApp message. Check server gateway logs.",
            error="Notification delivery failed"
        )

