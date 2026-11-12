import os
import re
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from fastapi import APIRouter, Depends, Form, Request, Response, BackgroundTasks
from sqlalchemy import desc, func, and_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db, AsyncSessionLocal
from backend.models.patient import Patient, WhatsAppMessageLog
from backend.models.doctor import Doctor
from backend.models.token import QueueToken, PrescriptionLog
from backend.services.location_service import get_nearby_available_doctors, calculate_haversine_distance
from backend.services.queue_service import book_queue_token, get_active_doctor_queue, reorder_queue_and_notify
from backend.services.ocr_service import parse_prescription
from backend.services.translation_service import explain_in_hindi
from backend.services.medicine_service import match_chemist_stocks, search_medicines
from backend.services.blood_service import normalize_blood_group, search_nearby_blood
from backend.services.notification_service import send_whatsapp_notification
from backend.services.hash_service import hash_patient_phone

router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger("whatsapp_router")

# Default coordinates (Central Delhi-NCR / Ghaziabad anchor)
DEFAULT_LATITUDE = float(os.getenv("DEFAULT_LATITUDE", "28.6692"))
DEFAULT_LONGITUDE = float(os.getenv("DEFAULT_LONGITUDE", "77.4538"))

# In-memory store for remembering the patient's last reported location
PATIENT_LAST_LOCATION: dict[str, Tuple[float, float]] = {}


async def process_prescription_background(
    raw_patient_phone: str,
    media_url: str,
    latitude: Optional[float],
    longitude: Optional[float]
):
    """
    Background task to download prescription, run OCR, match stocks, log/save, and send WhatsApp response out-of-band.
    """
    patient_phone = hash_patient_phone(raw_patient_phone)
    logger.info(f"Background processing of prescription started for raw: {raw_patient_phone} (hashed: {patient_phone})...")
    
    # 1. Download image from media_url
    image_bytes = None
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(media_url)
            if resp.status_code != 200:
                raise Exception(f"Download returned status code {resp.status_code}")
            image_bytes = resp.content
    except Exception as err:
        logger.error(f"Error downloading attachment media: {str(err)}")
        await send_whatsapp_notification(
            raw_patient_phone,
            "Sorry, we were unable to download your prescription photo. Please try capturing and sending it again."
        )
        return

    # 2. Run OCR via Gemini 3.6 Flash
    ocr_data = await parse_prescription(image_bytes)
    overall_conf = ocr_data.get("overall_confidence", 0.0)
    medicines = ocr_data.get("medicines", [])

    if not medicines and overall_conf < 0.40:
        logger.warning(f"Prescription OCR low confidence ({overall_conf}) from {raw_patient_phone}.")
        await send_whatsapp_notification(
            raw_patient_phone,
            "The prescription photo you sent is too blurry or unclear. "
            "Please capture a clearer, flat photo under good lighting and send again."
        )
        return

    if not medicines:
        logger.warning(f"No medicines extracted from prescription for {raw_patient_phone}.")
        await send_whatsapp_notification(
            raw_patient_phone,
            "We couldn't read any medicine names from this image. Please make sure the doctor's handwriting is clearly visible."
        )
        return

    medicine_names = [med.get("name") for med in medicines if med.get("name")]
    logger.info(f"Extracted medicines for {raw_patient_phone}: {medicine_names}")

    # 3. Match against chemist inventory
    # Use patient's cached location if available
    cached_loc = PATIENT_LAST_LOCATION.get(raw_patient_phone)
    lat = latitude if latitude is not None else (cached_loc[0] if cached_loc else DEFAULT_LATITUDE)
    lon = longitude if longitude is not None else (cached_loc[1] if cached_loc else DEFAULT_LONGITUDE)

    async with AsyncSessionLocal() as db:
        match_res = await match_chemist_stocks(db, medicine_names, lat, lon)
        reply_body = ""
        matched_chemist_id = None

        # Format doctor's actual prescribed medicines cleanly
        rx_meds_lines = []
        for med_dict in medicines:
            m_name = med_dict.get("name", "").strip()
            if not m_name:
                continue
            dosage = med_dict.get("dosage", "").strip()
            freq = med_dict.get("frequency", "").strip()
            dur = med_dict.get("duration", "").strip()
            meta = []
            if dosage and dosage.lower() not in m_name.lower():
                meta.append(dosage)
            if freq:
                meta.append(freq)
            if dur:
                meta.append(dur)
            meta_str = f" ({', '.join(meta)})" if meta else ""
            rx_meds_lines.append(f"• *{m_name}*{meta_str}")

        prescribed_str = "\n".join(rx_meds_lines) if rx_meds_lines else "\n".join([f"• *{n}*" for n in medicine_names])

        if match_res["type"] == "full":
            chemist = match_res["chemist"]
            dist = match_res["distance"]
            is_verified = match_res["is_verified"]
            matched_chemist_id = chemist.id
            stale_warning = "" if is_verified else "\n⚠️ (Warning: Stock info is unverified and has not been updated in 24 hours.)"
            maps_link = f"https://www.google.com/maps/dir/?api=1&destination={chemist.latitude},{chemist.longitude}"

            reply_body = (
                f"*Prescription Scan Complete!* 🔬\n\n"
                f"📋 *Medicines on Prescription:*\n{prescribed_str}\n\n"
                f"📍 *Available Nearby:* {chemist.shop_name} ({dist} km away){stale_warning}\n"
                f"📞 Phone: {chemist.phone}\n"
                f"🗺️ *Directions:* {maps_link}\n\n"
                f"Reply with *EXPLAIN* to receive explanations for these medicines in simple Hindi."
            )

        elif match_res["type"] == "combination":
            c1 = match_res["chemist_1"]
            d1 = match_res["distance_1"]
            v1 = match_res["is_verified_1"]
            m1 = ", ".join(match_res["medicines_1"])
            map1 = f"https://www.google.com/maps/dir/?api=1&destination={c1.latitude},{c1.longitude}"

            c2 = match_res["chemist_2"]
            d2 = match_res["distance_2"]
            v2 = match_res["is_verified_2"]
            m2 = ", ".join(match_res["medicines_2"])
            map2 = f"https://www.google.com/maps/dir/?api=1&destination={c2.latitude},{c2.longitude}"

            warn1 = "" if v1 else " (⚠️ Unverified)"
            warn2 = "" if v2 else " (⚠️ Unverified)"

            reply_body = (
                f"*Prescription Scan Complete!* 🔬\n\n"
                f"📋 *Medicines on Prescription:*\n{prescribed_str}\n\n"
                f"⚠️ *No single chemist has all medicines.* Best split combination:\n\n"
                f"1. *{c1.shop_name}* ({d1} km away){warn1}\n"
                f"   Medicines: {m1}\n"
                f"   🗺️ Directions: {map1}\n\n"
                f"2. *{c2.shop_name}* ({d2} km away){warn2}\n"
                f"   Medicines: {m2}\n"
                f"   🗺️ Directions: {map2}\n\n"
                f"Reply with *EXPLAIN* to receive explanations in simple Hindi."
            )
        else:
            reply_body = (
                f"*Prescription Scan Complete!* 🔬\n\n"
                f"📋 *Medicines on Prescription:*\n{prescribed_str}\n\n"
                f"❌ Sorry, we couldn't find any nearby chemist with confirmed stock for these medicines.\n\n"
                f"Reply with *EXPLAIN* to receive instructions on how each medicine should be taken."
            )

        # 4. Save PrescriptionLog
        log_entry = PrescriptionLog(
            patient_phone=patient_phone,
            image_url=media_url,
            extracted_medicines=medicines,
            matched_chemist_id=matched_chemist_id,
            ocr_confidence=overall_conf,
            hindi_explanation=""
        )
        db.add(log_entry)
        await db.commit()
        logger.info(f"PrescriptionLog saved successfully for patient {raw_patient_phone} (hash: {patient_phone}).")

    await send_whatsapp_notification(raw_patient_phone, reply_body)


async def process_explain_background(raw_patient_phone: str):
    """
    Background task to generate simple Hindi explanation for prescription medicines and reply.
    """
    patient_phone = hash_patient_phone(raw_patient_phone)
    logger.info(f"Background processing of EXPLAIN started for raw: {raw_patient_phone} (hashed: {patient_phone})...")
    async with AsyncSessionLocal() as db:
        log_stmt = (
            select(PrescriptionLog)
            .where(PrescriptionLog.patient_phone == patient_phone)
            .order_by(desc(PrescriptionLog.created_at))
            .limit(1)
        )
        res_log = await db.execute(log_stmt)
        latest_log = res_log.scalar_one_or_none()

        if not latest_log or not latest_log.extracted_medicines:
            await send_whatsapp_notification(
                raw_patient_phone,
                "No recent prescription found to explain. Please upload a photo of your prescription first."
            )
            return

        if latest_log.hindi_explanation:
            await send_whatsapp_notification(raw_patient_phone, latest_log.hindi_explanation)
            return

        hindi_explanation = await explain_in_hindi(latest_log.extracted_medicines)
        disclaimer = "\n\n⚠️ *Disclaimer:* This Hindi translation is AI-generated for informational support. Please verify all medications and instructions with your doctor or pharmacist."
        full_explanation = f"{hindi_explanation}{disclaimer}"

        latest_log.hindi_explanation = full_explanation
        db.add(latest_log)
        await db.commit()
        logger.info(f"Hindi explanation saved successfully in PrescriptionLog ID {latest_log.id}")

    await send_whatsapp_notification(raw_patient_phone, full_explanation)


async def handle_doctor_discovery(
    db: AsyncSession,
    patient: Patient,
    latitude: float,
    longitude: float,
    is_approximate: bool = False
) -> str:
    """
    Find nearby available doctors and format the booking list with 1-tap Google Maps directions.
    If outside 25km radius (e.g. testing from home), gracefully falls back to showing nearest
    registered clinics so testing and token booking always work.
    """
    default_radius = float(os.getenv("DEFAULT_SEARCH_RADIUS_KM", "5.0"))
    max_radius = float(os.getenv("MAX_SEARCH_RADIUS_KM", "25.0"))

    nearby_data = await get_nearby_available_doctors(db, latitude, longitude, default_radius, max_radius)
    is_outside_pilot = False

    if not nearby_data:
        # Fallback for evaluation / remote testing: show all available clinics ranked by distance
        result = await db.execute(select(Doctor).where(Doctor.is_available == True))
        all_docs = result.scalars().all()
        if all_docs:
            all_with_dist = []
            for d in all_docs:
                dist = calculate_haversine_distance(latitude, longitude, d.latitude, d.longitude)
                all_with_dist.append((d, dist))
            all_with_dist.sort(key=lambda x: x[1])
            nearby_data = all_with_dist[:5]
            is_outside_pilot = True
        else:
            return (
                "Currently, all registered clinics are offline or unavailable.\n"
                "Please check back shortly or text *STATUS*."
            )

    patient.last_search_doctor_ids = [doctor.id for doctor, _ in nearby_data]
    db.add(patient)
    await db.commit()

    if is_outside_pilot:
        header = (
            "📍 *Available S.E.H.A.T Doctors:*\n"
            "_(Note: You are currently outside our primary 25km pilot zone. "
            "Showing nearest registered clinics for consultation & testing):_"
        )
    elif is_approximate:
        header = "📍 *Nearby Doctors (Delhi-NCR Area):*\n_(Tip: Send your GPS location pin 📍 anytime for exact distance)_"
    else:
        header = "📍 *Nearby Available Doctors:*"

    reply_lines = [header, ""]
    for idx, (doctor, distance) in enumerate(nearby_data):
        active_queue = await get_active_doctor_queue(db, doctor.id)
        est_wait = len(active_queue) * doctor.avg_consultation_minutes
        maps_link = f"https://www.google.com/maps/dir/?api=1&destination={doctor.latitude},{doctor.longitude}"

        dist_str = f"{round(distance, 1)} km away" if distance < 100 else f"{int(round(distance))} km away"
        line = (
            f"*{idx + 1}. Dr. {doctor.name}* ({doctor.specialization})\n"
            f"📍 {doctor.clinic_name} ({dist_str})\n"
            f"🕒 Est. Wait: ~{est_wait} mins (Queue: {len(active_queue)} waiting)\n"
            f"🗺️ *Directions:* {maps_link}\n"
        )
        reply_lines.append(line)

    reply_lines.append("Reply with the number (e.g. *1* or *2*) to book a token instantly.")
    return "\n".join(reply_lines)


async def process_patient_dialogue(
    patient_phone: str,
    message_body: str,
    profile_name: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
    media_url: Optional[str],
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    is_location_msg: bool = False
) -> Optional[str]:
    """
    Core dialogue processor for S.E.H.A.T healthcare platform.
    Used by incoming UltraMsg WhatsApp webhook.
    """
    message_body = message_body.strip() if message_body else ""
    hashed_patient_phone = hash_patient_phone(patient_phone)

    # Cache user coordinates if provided
    if latitude is not None and longitude is not None:
        PATIENT_LAST_LOCATION[patient_phone] = (latitude, longitude)
    elif patient_phone in PATIENT_LAST_LOCATION:
        cached_lat, cached_lng = PATIENT_LAST_LOCATION[patient_phone]
        if latitude is None:
            latitude = cached_lat
        if longitude is None:
            longitude = cached_lng

    logger.info(f"WhatsApp processing from raw: {patient_phone} (hashed: {hashed_patient_phone}) | Body: '{message_body}' | Location: ({latitude}, {longitude}) | is_loc: {is_location_msg} | MediaUrl: {media_url}")

    # 1. Rate Limiting: Configurable per hour (Default 25)
    max_rate = int(os.getenv("WHATSAPP_RATE_LIMIT_PER_HOUR", "25"))
    one_hour_ago = datetime.now() - timedelta(hours=1)
    rate_limit_stmt = (
        select(func.count(WhatsAppMessageLog.id))
        .where(
            and_(
                WhatsAppMessageLog.patient_phone == hashed_patient_phone,
                WhatsAppMessageLog.timestamp >= one_hour_ago
            )
        )
    )
    count_res = await db.execute(rate_limit_stmt)
    msg_count = count_res.scalar() or 0

    if msg_count >= max_rate:
        logger.warning(f"Rate limit exceeded for patient {patient_phone}")
        is_hindi = "KHOON" in message_body.upper() or any(u"\u0900" <= char <= u"\u097F" for char in message_body)
        if is_hindi:
            return "⚠️ आप एक घंटे में अधिकतम संदेश सीमा पार कर चुके हैं। कृपया कुछ समय बाद पुनः प्रयास करें।"
        else:
            return "⚠️ Rate limit exceeded. You have reached the hourly message limit. Please try again in a little while."

    # Record message timestamp
    log_msg = WhatsAppMessageLog(patient_phone=hashed_patient_phone, timestamp=datetime.now())
    db.add(log_msg)
    await db.commit()

    # 2. Lookup or create patient profile
    patient_result = await db.execute(select(Patient).where(Patient.phone == patient_phone))
    patient = patient_result.scalar_one_or_none()

    if not patient:
        patient = Patient(
            phone=patient_phone,
            name=profile_name or "Patient",
            language_preference="en",
            last_search_doctor_ids=[]
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        logger.info(f"Registered new patient profile for phone: {patient_phone} (Name: {patient.name})")
    elif profile_name and (patient.name == "Patient" or not patient.name):
        patient.name = profile_name
        db.add(patient)
        await db.commit()

    # 3. Handle Prescription Photo Attachment (FLOW 2)
    if media_url:
        logger.info(f"Prescription photo upload detected from patient {patient_phone}.")
        background_tasks.add_task(process_prescription_background, patient_phone, media_url, latitude, longitude)
        return "Received your prescription photo! 🔬 We are analyzing it. You will receive medicine stock status shortly..."

    cmd = message_body.upper().strip()
    blood_group = normalize_blood_group(message_body)
    is_cancel = cmd == "CANCEL"
    is_status = cmd in ["STATUS", "QUEUE", "MY APPOINTMENT", "MY BOOKING", "TOKEN"]
    is_explain = cmd == "EXPLAIN"
    is_greeting = cmd in [
        "HI", "HELLO", "HEY", "HLO", "HALO", "HELO", "MENU", "HELP", "START",
        "NAMASTE", "NAMASKAR", "SEHAT", "GREETINGS", "TEST"
    ]

    # If user sent a greeting or menu request, return the welcome menu
    if is_greeting:
        return (
            f"Hello {patient.name}! Welcome to *S.E.H.A.T* (Swasthya Electronic Health Assistance Terminal) 🩺\n\n"
            "• *Find & Book Doctor:* Text *DOCTOR* or share your location pin 📍\n"
            "• *Check Queue Status:* Text *STATUS*\n"
            "• *Cancel Appointment:* Text *CANCEL*\n"
            "• *Search Medicine Stock:* Send a prescription photo 📸 or text *MED <name>*\n"
            "• *Emergency Blood Bank:* Type blood group (e.g. *O+*, *B+*, *KHOON A+*)"
        )

    # 4. Handle Location Pin Input (Nearby Doctors Discovery)
    # Trigger doctor search ONLY if user explicitly sent a location message/pin
    if is_location_msg and not is_cancel and not is_status and not is_explain and not blood_group:
        lat = latitude if latitude is not None else DEFAULT_LATITUDE
        lon = longitude if longitude is not None else DEFAULT_LONGITUDE
        logger.info(f"Processing GPS location pin shared by patient {patient_phone}: ({lat}, {lon})")
        return await handle_doctor_discovery(db, patient, lat, lon, is_approximate=False)

    # 5. Text Command inputs
    cmd = message_body.upper().strip()

    # 5a. Cancel appointment
    if cmd == "CANCEL":
        # Search using both formats (+ and without +)
        phone_variants = [patient_phone, patient_phone.lstrip("+"), f"+{patient_phone.lstrip('+')}"]
        token_stmt = (
            select(QueueToken)
            .where(
                and_(
                    QueueToken.patient_phone.in_(phone_variants),
                    QueueToken.status.in_(["waiting", "called"])
                )
            )
        )
        token_res = await db.execute(token_stmt)
        active_token = token_res.scalar_one_or_none()

        if not active_token:
            return "You do not have any active appointments to cancel. ⚠️ Reply *DOCTOR* to find open clinics."

        doc_id = active_token.doctor_id
        active_token.status = "cancelled"
        db.add(active_token)
        await db.commit()

        await reorder_queue_and_notify(db, doc_id)
        return "Your appointment has been cancelled successfully. ❌ Any patients behind you in the queue have been notified."

    # 5b. Check Queue / Booking Status
    if cmd in ["STATUS", "QUEUE", "MY APPOINTMENT", "MY BOOKING", "TOKEN"]:
        phone_variants = [patient_phone, patient_phone.lstrip("+"), f"+{patient_phone.lstrip('+')}"]
        token_stmt = (
            select(QueueToken)
            .where(
                and_(
                    QueueToken.patient_phone.in_(phone_variants),
                    QueueToken.status.in_(["waiting", "called"])
                )
            )
        )
        token_res = await db.execute(token_stmt)
        active_token = token_res.scalar_one_or_none()

        if not active_token:
            return "You don't have any active appointments right now. Reply *DOCTOR* to find and book a clinic near you! 🏥"

        doc_res = await db.execute(select(Doctor).where(Doctor.id == active_token.doctor_id))
        doc = doc_res.scalar_one_or_none()
        doc_name = f"Dr. {doc.name}" if doc else "Doctor"
        clinic_name = doc.clinic_name if doc else "Clinic"
        maps_link = f"https://www.google.com/maps/dir/?api=1&destination={doc.latitude},{doc.longitude}" if doc else ""

        return (
            f"🎫 *Your Active Appointment Details:*\n\n"
            f"👨‍⚕️ *Doctor:* {doc_name} ({doc.specialization if doc else ''})\n"
            f"📍 *Clinic:* {clinic_name}\n"
            f"🔢 *Token Number:* #{active_token.token_number}\n"
            f"👥 *Queue Position:* #{active_token.position}\n"
            f"🕒 *Estimated Wait:* ~{active_token.estimated_wait_minutes} mins\n"
            f"🚦 *Status:* {active_token.status.title()}\n"
            f"🗺️ *Directions:* {maps_link}\n\n"
            f"Reply *CANCEL* if you cannot attend."
        )

    # 5c. Blood Group query (FLOW 3)
    blood_group = normalize_blood_group(message_body)
    if blood_group:
        lat = latitude if latitude is not None else DEFAULT_LATITUDE
        lon = longitude if longitude is not None else DEFAULT_LONGITUDE

        banks = await search_nearby_blood(db, blood_group, lat, lon)
        is_hindi = "KHOON" in message_body.upper() or any(u"\u0900" <= char <= u"\u097F" for char in message_body)

        if not banks:
            if is_hindi:
                return f"अस्पताल के ५ किमी के दायरे में कोई {blood_group} रक्त उपलब्ध नहीं है।"
            else:
                return f"No {blood_group} blood is currently available in nearby registered blood banks."

        reply_lines = []
        if is_hindi:
            reply_lines.append(f"🩸 आपके पास उपलब्ध {blood_group} रक्त:")
        else:
            reply_lines.append(f"🩸 {blood_group} Blood Available Near You:")
        reply_lines.append("")

        for idx, item in enumerate(banks):
            bank = item["bank"]
            dist = item["distance"]
            stock = item["stock"]
            is_verified = item["is_verified"]

            time_str = "24 hours" if bank.is_open_24hrs else f"{bank.opening_time.strftime('%I%p').lstrip('0')} - {bank.closing_time.strftime('%I%p').lstrip('0')}"
            map_link = f"https://www.google.com/maps/dir/?api=1&destination={bank.latitude},{bank.longitude}"
            if is_hindi:
                time_str_hi = "२४ घंटे खुला" if bank.is_open_24hrs else f"सुबह {bank.opening_time.strftime('%I')} से रात {bank.closing_time.strftime('%I')} बजे तक"
                stale_warn = "" if is_verified else " (⚠️ असत्यापित)"
                line = (
                    f"{idx + 1}. *{bank.name}* - {bank.address} ({dist} किमी दूर){stale_warn}\n"
                    f"   मात्रा: {stock.units_available} यूनिट  |  संपर्क: {bank.phone}\n"
                    f"   समय: {time_str_hi}\n"
                    f"   🗺️ दिशा-निर्देश: {map_link}\n"
                )
            else:
                stale_warn = "" if is_verified else " (⚠️ Unverified)"
                line = (
                    f"{idx + 1}. *{bank.name}* - {bank.address} ({dist} km away){stale_warn}\n"
                    f"   Units: {stock.units_available}  |  Contact: {bank.phone}\n"
                    f"   Open: {time_str}\n"
                    f"   🗺️ Directions: {map_link}\n"
                )
            reply_lines.append(line)

        return "\n".join(reply_lines)

    # 5d. Doctor Discovery Keywords (Supports typos like 'doctore', English & Hindi variations)
    doctor_keywords = [
        "DOCTOR", "DOCTORS", "DOCTORE", "DOC", "DOCS", "CLINIC", "CLINICS",
        "HOSPITAL", "HOSPITALS", "APPOINTMENT", "APPOINTMENTS", "BOOK", "BOOKING",
        "DR", "DR.", "CONSULT", "CONSULTATION", "CHECKUP"
    ]
    is_doc_request = (
        cmd in doctor_keywords
        or any(kw in cmd for kw in [
            "DOCTOR", "DOCTORE", "CLINIC", "APPOINTMENT", "BOOK DOCTOR", "DOCTOR BOOKING",
            "FIND DOCTOR", "SEE DOCTOR", "NEARBY DOCTOR", "NEAREST DOCTOR", "DR."
        ])
        or any(h_kw in message_body for h_kw in ["डॉक्टर", "डॉ", "दवाखाना", "क्लीनिक", "अस्पताल", "दिखाना"])
    )
    if is_doc_request:
        lat = latitude if latitude is not None else DEFAULT_LATITUDE
        lon = longitude if longitude is not None else DEFAULT_LONGITUDE
        is_approx = (latitude is None or longitude is None)
        return await handle_doctor_discovery(db, patient, lat, lon, is_approximate=is_approx)

    # 5e. Prescription explanation in Hindi
    if cmd == "EXPLAIN":
        log_stmt = (
            select(PrescriptionLog)
            .where(PrescriptionLog.patient_phone == hashed_patient_phone)
            .order_by(desc(PrescriptionLog.created_at))
            .limit(1)
        )
        res_log = await db.execute(log_stmt)
        latest_log = res_log.scalar_one_or_none()

        if not latest_log or not latest_log.extracted_medicines:
            return "No recent prescription found to explain. Please upload a photo of your prescription first."

        if latest_log.hindi_explanation:
            return latest_log.hindi_explanation

        background_tasks.add_task(process_explain_background, patient_phone)
        return "Generating simple Hindi explanation for your prescription... Please wait a moment."

    # 5f. Digit selections (Booking confirmation)
    if cmd.isdigit():
        choice = int(cmd)
        search_ids = patient.last_search_doctor_ids or []

        if not search_ids:
            return (
                "No active doctor search found. Please reply *DOCTOR* to see available clinics, "
                "or share your location pin 📍 first."
            )

        if choice < 1 or choice > len(search_ids):
            return f"Invalid selection. Please choose a number between 1 and {len(search_ids)}."

        doctor_id = search_ids[choice - 1]

        # Check if already booked
        phone_variants = [patient_phone, patient_phone.lstrip("+"), f"+{patient_phone.lstrip('+')}"]
        existing_token_res = await db.execute(
            select(QueueToken).where(
                and_(
                    QueueToken.patient_phone.in_(phone_variants),
                    QueueToken.status.in_(["waiting", "called"])
                )
            )
        )
        existing_token = existing_token_res.scalar_one_or_none()
        if existing_token:
            return (
                f"⚠️ You already have an active booking (Token #{existing_token.token_number})!\n"
                f"Please reply *STATUS* to check your place in queue, or *CANCEL* if you wish to re-book."
            )

        token = await book_queue_token(db, doctor_id, patient.phone, patient.name)
        if not token:
            return (
                "Unable to book token. The doctor may have marked themselves offline "
                "or reached the maximum daily capacity (50 tokens). Please try another doctor."
            )
        # book_queue_token sends confirmation WhatsApp notification directly to patient!
        return None

    # 5g. Direct text medicine stock search (e.g. "medicine Dolo", "med Paracetamol", "Dolo 650", "Pan 40")
    med_query = message_body
    for prefix in ["MEDICINE", "MED", "DAWA", "DAWAI", "PILL", "SEARCH"]:
        if cmd.startswith(prefix + " "):
            med_query = message_body[len(prefix) + 1:].strip()
            break

    # Check if query matches known database medicines
    matched_medicines = await search_medicines(db, med_query)
    if matched_medicines:
        lat = latitude if latitude is not None else DEFAULT_LATITUDE
        lon = longitude if longitude is not None else DEFAULT_LONGITUDE
        search_target = [matched_medicines[0].generic_name]

        stock_res = await match_chemist_stocks(db, search_target, lat, lon)
        if stock_res.get("type") == "full":
            ch = stock_res["chemist"]
            d = stock_res["distance"]
            v = stock_res["is_verified"]
            stale_str = "" if v else " (⚠️ Unverified stock)"
            mlink = f"https://www.google.com/maps/dir/?api=1&destination={ch.latitude},{ch.longitude}"

            med_obj = matched_medicines[0]
            brands = ", ".join(med_obj.brand_names) if med_obj.brand_names else med_obj.generic_name
            return (
                f"💊 *Medicine In Stock Nearby!*\n\n"
                f"• *{med_obj.generic_name}* (Brands: {brands})\n\n"
                f"📍 *Available at:* {ch.shop_name} ({d} km away){stale_str}\n"
                f"📞 *Contact:* {ch.phone}\n"
                f"🗺️ *Directions:* {mlink}\n\n"
                f"Send a photo of your prescription to check multiple medicines at once."
            )
        elif stock_res.get("type") in ["combination", "none"]:
            return (
                f"💊 Searched for *{med_query.title()}*:\n\n"
                f"Currently, no open registered chemist within search radius has this medicine in stock.\n"
                f"Tip: Send a full prescription photo to check all prescribed medicines."
            )

    # 6. Fallback greeting
    greeting = (
        f"Hello {patient.name}! Welcome to *S.E.H.A.T* (Swasthya Electronic Health Assistance Terminal) 🩺\n\n"
        "• *Find & Book Doctor:* Text *DOCTOR* or share your location pin 📍\n"
        "• *Check Queue Status:* Text *STATUS*\n"
        "• *Cancel Appointment:* Text *CANCEL*\n"
        "• *Search Medicine Stock:* Send a prescription photo 📸 or text *MED <name>*\n"
        "• *Emergency Blood Bank:* Type blood group (e.g. *O+*, *B+*, *KHOON A+*)"
    )
    return greeting


@router.post("/webhook")
@router.post("/ultramsg")
@router.post("/ultramsg/webhook")
@router.post("/reply_whatsapp")
async def ultramsg_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    UltraMsg webhook receiver endpoint for WhatsApp messages.
    Receives JSON payload on incoming WhatsApp messages.
    Handles chats, location pins, and prescription photo uploads.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "invalid JSON"}

    event_type = payload.get("event_type")
    if event_type and event_type != "message_received":
        return {"status": "ignored", "event": event_type}

    data = payload.get("data", {})
    raw_from = data.get("from", "")

    # Ignore group messages (@g.us) or messages sent by ourselves
    if not raw_from or "@g.us" in raw_from or data.get("fromMe") is True:
        return {"status": "ignored"}

    clean_phone = raw_from.split("@")[0].replace("whatsapp:", "").strip()
    if not clean_phone.startswith("+"):
        clean_phone = f"+{clean_phone}"

    message_body = data.get("body", "")
    profile_name = data.get("pushname") or "Patient"
    msg_type = data.get("type", "chat")

    # 1. Comprehensive Location Extraction (UltraMsg payload formats)
    lat = (
        data.get("lat")
        or data.get("latitude")
        or (data.get("location") or {}).get("lat")
        or (data.get("location") or {}).get("latitude")
        or (data.get("loc") or {}).get("lat")
        or (data.get("loc") or {}).get("latitude")
        or (data.get("message") or {}).get("lat")
        or (data.get("message") or {}).get("latitude")
    )
    lng = (
        data.get("lng")
        or data.get("longitude")
        or (data.get("location") or {}).get("lng")
        or (data.get("location") or {}).get("longitude")
        or (data.get("loc") or {}).get("lng")
        or (data.get("loc") or {}).get("longitude")
        or (data.get("message") or {}).get("lng")
        or (data.get("message") or {}).get("longitude")
    )

    is_location_msg = (
        msg_type in ["location", "live_location", "loc"]
        or "maps.google.com" in message_body
        or "maps.app.goo.gl" in message_body
        or "geo:" in message_body
    )

    # If coordinates are in message_body (e.g. Google Maps link or "lat, lng" string)
    if (lat is None or lng is None) and message_body:
        coord_match = re.search(r"(-?\d{1,3}\.\d+)[,\s/]+(-?\d{1,3}\.\d+)", message_body)
        if coord_match:
            try:
                c_lat = float(coord_match.group(1))
                c_lng = float(coord_match.group(2))
                if -90 <= c_lat <= 90 and -180 <= c_lng <= 180:
                    lat = c_lat
                    lng = c_lng
                    is_location_msg = True
            except ValueError:
                pass

    # If message type is location but coordinates could not be parsed, default to central coordinates
    if is_location_msg and (lat is None or lng is None):
        logger.info(f"Location message without explicit coordinates from {clean_phone}. Using Delhi-NCR center fallback.")
        lat = DEFAULT_LATITUDE
        lng = DEFAULT_LONGITUDE

    latitude = float(lat) if lat is not None else None
    longitude = float(lng) if lng is not None else None

    # Remember location in memory
    if latitude is not None and longitude is not None:
        PATIENT_LAST_LOCATION[clean_phone] = (latitude, longitude)

    # 2. Media / Prescription Extraction
    media_url = (
        data.get("media")
        or data.get("mediaUrl")
        or data.get("url")
        or (data.get("message") or {}).get("media")
        or (data.get("message") or {}).get("url")
    )

    # If image received but media URL not directly in webhook payload, fetch from UltraMsg API
    if not media_url and (msg_type in ["image", "document", "photo"] or "image" in str(data)):
        msg_id = data.get("id")
        instance_id = os.getenv("ULTRAMSG_INSTANCE_ID")
        token = os.getenv("ULTRAMSG_TOKEN")
        if msg_id and instance_id and token:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    api_resp = await client.get(f"https://api.ultramsg.com/{instance_id}/messages?token={token}&id={msg_id}")
                    if api_resp.status_code == 200:
                        m_data = api_resp.json()
                        msgs = m_data.get("messages", []) if isinstance(m_data, dict) else (m_data if isinstance(m_data, list) else [])
                        if msgs:
                            media_url = msgs[0].get("media") or msgs[0].get("url")
            except Exception as e:
                logger.error(f"Error querying UltraMsg API for media URL: {e}")


    logger.info(f"UltraMsg incoming from {clean_phone}: type='{msg_type}', is_loc={is_location_msg}, lat={latitude}, lng={longitude}, media={media_url}")

    # If an image was received but media could still not be fetched
    if not media_url and msg_type in ["image", "document", "photo"]:
        warning_msg = (
            "📸 We received your prescription photo! However, 'Webhook Download Media' "
            "must be turned ON in your UltraMsg settings so we can download and analyze it.\n\n"
            "Please turn it ON in your UltraMsg instance settings and send the photo again."
        )
        await send_whatsapp_notification(clean_phone, warning_msg)
        return {"status": "ok"}

    reply_text = await process_patient_dialogue(
        patient_phone=clean_phone,
        message_body=message_body,
        profile_name=profile_name,
        latitude=latitude,
        longitude=longitude,
        media_url=media_url,
        db=db,
        background_tasks=background_tasks,
        is_location_msg=is_location_msg
    )

    if reply_text:
        await send_whatsapp_notification(clean_phone, reply_text)

    return {"status": "ok"}

