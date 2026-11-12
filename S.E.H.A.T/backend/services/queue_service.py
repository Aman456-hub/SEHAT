import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Set
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.token import QueueToken
from backend.models.doctor import Doctor
from backend.schemas.doctor import DoctorCreate
from backend.services.notification_service import send_whatsapp_notification

logger = logging.getLogger("queue_service")

# In-memory deduplication tracker: token_id -> set of positions already notified
TOKEN_NOTIFIED_POSITIONS: Dict[int, Set[int]] = {}

async def register_doctor(db: AsyncSession, doctor_data: DoctorCreate) -> Doctor:
    """
    Register a new doctor in the database.
    Saves clinic coordinates, contact info, and specialized services.
    Every service function must have a docstring.
    """
    db_doctor = Doctor(
        name=doctor_data.name,
        phone=doctor_data.phone,
        clinic_name=doctor_data.clinic_name,
        address=doctor_data.address,
        latitude=doctor_data.latitude,
        longitude=doctor_data.longitude,
        specialization=doctor_data.specialization,
        avg_consultation_minutes=doctor_data.avg_consultation_minutes,
        is_available=True
    )
    db.add(db_doctor)
    await db.commit()
    await db.refresh(db_doctor)
    logger.info(f"Doctor registered successfully: {db_doctor.name} (ID: {db_doctor.id})")
    return db_doctor

async def book_queue_token(db: AsyncSession, doctor_id: int, patient_phone: str, patient_name: str) -> Optional[QueueToken]:
    """
    Book a new token in the queue for a specific doctor.
    Enforces the following logic:
    - Verifies the doctor exists and is currently available.
    - Calculates the token number (incrementing max token number booked today).
    - Calculates the queue position (active waiting/called tokens + 1).
    - Calculates estimated wait time: (position - 1) * average consultation minutes.
    - Logs the action and sends a confirmation WhatsApp notification.
    """
    # 1. Verify doctor availability
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor or not doctor.is_available:
        logger.warning(f"Booking failed: Doctor {doctor_id} does not exist or is unavailable.")
        return None

    # Check if patient already has an active token for this doctor
    active_token_result = await db.execute(
        select(QueueToken).where(
            and_(
                QueueToken.doctor_id == doctor_id,
                QueueToken.patient_phone == patient_phone,
                QueueToken.status.in_(["waiting", "called"])
            )
        )
    )
    if active_token_result.scalar_one_or_none():
        logger.warning(f"Booking failed: Patient {patient_phone} already has an active token for doctor {doctor_id}.")
        return None

    # 2. Calculate token number for today
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    today_end = datetime.combine(datetime.now().date(), datetime.max.time())
    
    token_num_result = await db.execute(
        select(func.max(QueueToken.token_number)).where(
            and_(
                QueueToken.doctor_id == doctor_id,
                QueueToken.booked_at >= today_start,
                QueueToken.booked_at <= today_end
            )
        )
    )
    max_token = token_num_result.scalar() or 0
    next_token_number = max_token + 1

    if next_token_number > 50:
        logger.warning(f"Booking failed: Doctor {doctor_id} has reached the maximum daily limit of 50 tokens.")
        return None

    # 3. Calculate position (count of active waiting/called tokens)
    active_tokens_result = await db.execute(
        select(func.count(QueueToken.id)).where(
            and_(
                QueueToken.doctor_id == doctor_id,
                QueueToken.status.in_(["waiting", "called"])
            )
        )
    )
    active_count = active_tokens_result.scalar() or 0
    next_position = active_count + 1

    # 4. Calculate estimated wait minutes
    estimated_wait = (next_position - 1) * doctor.avg_consultation_minutes

    # 5. Save the token
    new_token = QueueToken(
        doctor_id=doctor_id,
        patient_phone=patient_phone,
        patient_name=patient_name,
        token_number=next_token_number,
        position=next_position,
        status="waiting",
        estimated_wait_minutes=estimated_wait,
        booked_at=datetime.now()
    )
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)

    # Track initial position so patient isn't sent immediate duplicate alert
    TOKEN_NOTIFIED_POSITIONS[new_token.id] = {next_position}

    logger.info(f"Token Booked: Token #{new_token.token_number} | Position: {new_token.position} | Patient: {patient_name} ({patient_phone})")

    # 6. Send WhatsApp confirmation
    maps_link = f"https://www.google.com/maps/dir/?api=1&destination={doctor.latitude},{doctor.longitude}"
    msg = (
        f"🎉 *Appointment Confirmed!*\n\n"
        f"Hello {patient_name}, your booking is confirmed with *Dr. {doctor.name}* ({doctor.specialization}).\n"
        f"📍 *Clinic:* {doctor.clinic_name}\n"
        f"🎫 *Token Number:* #{new_token.token_number}\n"
        f"👥 *Queue Position:* #{new_token.position}\n"
        f"🕒 *Estimated Wait:* ~{new_token.estimated_wait_minutes} mins\n"
        f"🗺️ *Clinic Directions:* {maps_link}\n\n"
        f"We will notify you when your turn is close. Reply *STATUS* to check live queue or *CANCEL* if you cannot attend."
    )
    await send_whatsapp_notification(patient_phone, msg)

    return new_token

async def reorder_queue_and_notify(db: AsyncSession, doctor_id: int) -> None:
    """
    Recalculate positions and estimated wait times for all active tokens
    belonging to a doctor after a change in the queue (e.g., seen, cancelled).
    Notifies the next patient (position 2) that their turn is coming.
    """
    # Fetch doctor average consultation time
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor:
        return

    # Get remaining active tokens ordered by their existing position and booked_at
    result = await db.execute(
        select(QueueToken)
        .where(
            and_(
                QueueToken.doctor_id == doctor_id,
                QueueToken.status.in_(["waiting", "called"])
            )
        )
        .order_by(QueueToken.position, QueueToken.booked_at)
    )
    active_tokens = list(result.scalars().all())

    # Sort manually to ensure correct order
    active_tokens.sort(key=lambda t: (0 if t.status == "called" else 1, t.position, t.booked_at))

    # Update positions and wait times
    for idx, token in enumerate(active_tokens):
        new_position = idx + 1
        token.position = new_position
        token.estimated_wait_minutes = idx * doctor.avg_consultation_minutes
        
        # Save updates
        db.add(token)
        
        notified_set = TOKEN_NOTIFIED_POSITIONS.setdefault(token.id, set())

        # Notify if they are now at position 1 or 2 (waiting) and haven't received that position alert yet
        if new_position in (1, 2) and token.status == "waiting":
            if new_position not in notified_set:
                notified_set.add(new_position)
                instruction = (
                    "Please be ready outside the consultation room."
                    if new_position == 1
                    else "Please head to the clinic waiting area now."
                )
                maps_link = f"https://www.google.com/maps/dir/?api=1&destination={doctor.latitude},{doctor.longitude}"
                msg = (
                    f"⏳ *Almost Your Turn!*\n\n"
                    f"Dear {token.patient_name}, you are now *#{new_position} in line* for Dr. {doctor.name}.\n"
                    f"📍 *Clinic:* {doctor.clinic_name}\n"
                    f"🕒 *Est. Wait:* ~{token.estimated_wait_minutes} mins\n"
                    f"🗺️ *Directions:* {maps_link}\n\n"
                    f"{instruction}"
                )
                await send_whatsapp_notification(token.patient_phone, msg)

    await db.commit()

async def call_next_patient(db: AsyncSession, doctor_id: int) -> Optional[QueueToken]:
    """
    Call the next patient in the queue.
    Finds the first waiting patient, changes status to 'called', sets called_at,
    sends WhatsApp alert, and shifts/notifies the rest of the queue.
    """
    # Find doctor
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor:
        return None

    # Fetch the token with status waiting and lowest position
    result = await db.execute(
        select(QueueToken)
        .where(
            and_(
                QueueToken.doctor_id == doctor_id,
                QueueToken.status == "waiting"
            )
        )
        .order_by(QueueToken.position.asc())
        .limit(1)
    )
    next_token = result.scalar_one_or_none()

    if not next_token:
        logger.info(f"No waiting patients in queue for doctor {doctor_id}.")
        return None

    # Update token status to called
    next_token.status = "called"
    next_token.called_at = datetime.now()
    next_token.position = 1
    next_token.estimated_wait_minutes = 0
    db.add(next_token)
    await db.commit()
    await db.refresh(next_token)

    logger.info(f"Token Called: Token #{next_token.token_number} | Doctor: {doctor.name}")

    # Notify called patient
    msg = (
        f"🔔 *It's Your Turn!*\n\n"
        f"Hello {next_token.patient_name}, Token #{next_token.token_number} is now being called!\n"
        f"Please enter Dr. {doctor.name}'s consultation room at {doctor.clinic_name} now."
    )
    await send_whatsapp_notification(next_token.patient_phone, msg)

    # Reorder the rest of the queue (which handles notifying position 2)
    await reorder_queue_and_notify(db, doctor_id)

    return next_token

async def mark_token_status(db: AsyncSession, token_id: int, status: str) -> Optional[QueueToken]:
    """
    Mark a token as seen, called, or cancelled.
    Automatically handles queue reordering and triggering notifications for next patients.
    """
    result = await db.execute(select(QueueToken).where(QueueToken.id == token_id))
    token = result.scalar_one_or_none()
    if not token:
        logger.warning(f"Status update failed: Token {token_id} not found.")
        return None

    old_status = token.status
    token.status = status

    if status == "seen":
        token.seen_at = datetime.now()
        token.position = 0
        token.estimated_wait_minutes = 0
    elif status == "called":
        token.called_at = datetime.now()
        token.position = 1
        token.estimated_wait_minutes = 0
        db.add(token)
        await db.commit()
        await db.refresh(token)

        logger.info(f"Token {token_id} status updated to 'called'. Sending WhatsApp call alert...")

        # Fetch doctor details for notification
        doctor_res = await db.execute(select(Doctor).where(Doctor.id == token.doctor_id))
        doctor = doctor_res.scalar_one_or_none()
        doc_name = f"Dr. {doctor.name}" if doctor else "Doctor"
        clinic_info = f" at {doctor.clinic_name}" if doctor else ""
        
        call_msg = (
            f"🔔 *It's Your Turn!*\n\n"
            f"Hello {token.patient_name}, Token #{token.token_number} is now being called.\n"
            f"Please enter {doc_name}'s consultation room{clinic_info} now."
        )
        await send_whatsapp_notification(token.patient_phone, call_msg)

        # Reorder remaining queue and notify position 2
        await reorder_queue_and_notify(db, token.doctor_id)
        return token
    elif status == "cancelled":
        token.position = 0
        token.estimated_wait_minutes = 0

    db.add(token)
    await db.commit()
    await db.refresh(token)

    logger.info(f"Token {token_id} status updated from '{old_status}' to '{status}'.")

    # If the token left the active queue, trigger a reorder
    if status in ["seen", "cancelled"] and old_status in ["waiting", "called"]:
        TOKEN_NOTIFIED_POSITIONS.pop(token_id, None)
        if status == "seen":
            called_token = await call_next_patient(db, token.doctor_id)
            if not called_token:
                # If no waiting patient exists to call, reorder remaining queue
                await reorder_queue_and_notify(db, token.doctor_id)
        else:
            # Cancelled: reorder remaining queue
            await reorder_queue_and_notify(db, token.doctor_id)

    return token

async def toggle_doctor_availability(db: AsyncSession, doctor_id: int, is_available: bool) -> Optional[Doctor]:
    """
    Toggle doctor availability status.
    If toggled to unavailable (offline), cancels all waiting/called patients in their queue
    and notifies them immediately via WhatsApp (Adhering to Business Rule 2).
    """
    doctor_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = doctor_result.scalar_one_or_none()
    if not doctor:
        return None

    doctor.is_available = is_available
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)

    logger.info(f"Doctor {doctor.name} availability toggled to: {is_available}")

    if not is_available:
        # Cancel all active tokens and notify patients
        active_tokens_result = await db.execute(
            select(QueueToken).where(
                and_(
                    QueueToken.doctor_id == doctor_id,
                    QueueToken.status.in_(["waiting", "called"])
                )
            )
        )
        active_tokens = active_tokens_result.scalars().all()
        
        for token in active_tokens:
            token.status = "cancelled"
            token.position = 0
            token.estimated_wait_minutes = 0
            db.add(token)
            
            # Send notification
            msg = (
                f"Important: Dr. {doctor.name} has marked themselves as unavailable today. "
                f"Your Token #{token.token_number} has been cancelled. We apologize for the inconvenience."
            )
            await send_whatsapp_notification(token.patient_phone, msg)
            
        await db.commit()

    return doctor

async def auto_cancel_expired_tokens(db: AsyncSession) -> int:
    """
    Enforce Business Rule 1: Auto-cancel.
    If a patient does not arrive within 10 minutes of being called,
    cancel their token and notify the next patient automatically.
    Returns the count of cancelled tokens.
    """
    ten_minutes_ago = datetime.now() - timedelta(minutes=10)
    
    # Query tokens that were called more than 10 minutes ago and are still marked 'called'
    result = await db.execute(
        select(QueueToken).where(
            and_(
                QueueToken.status == "called",
                QueueToken.called_at <= ten_minutes_ago
            )
        )
    )
    expired_tokens = list(result.scalars().all())
    cancelled_count = len(expired_tokens)

    for token in expired_tokens:
        token.status = "cancelled"
        token.position = 0
        token.estimated_wait_minutes = 0
        db.add(token)

        # Notify the patient
        msg = (
            f"Your Token #{token.token_number} has been cancelled automatically because "
            f"you did not arrive within 10 minutes of being called. Please rebook if needed."
        )
        await send_whatsapp_notification(token.patient_phone, msg)
        
        # Commit this token's cancellation
        await db.commit()

        # Reorder the queue for this doctor and call the next patient
        await reorder_queue_and_notify(db, token.doctor_id)
        await call_next_patient(db, token.doctor_id)

    return cancelled_count

async def get_active_doctor_queue(db: AsyncSession, doctor_id: int) -> List[QueueToken]:
    """
    Retrieve all active queue tokens (status 'waiting' or 'called') for a doctor,
    ordered by position. Used to render live dashboard queues.
    Every service function must have a docstring.
    """
    result = await db.execute(
        select(QueueToken)
        .where(
            and_(
                QueueToken.doctor_id == doctor_id,
                QueueToken.status.in_(["waiting", "called"])
            )
        )
        .order_by(QueueToken.position.asc())
    )
    return list(result.scalars().all())
