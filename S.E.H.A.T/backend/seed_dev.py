import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy import select
from backend.database import engine, Base, AsyncSessionLocal
from backend.models.doctor import Doctor
from backend.models.chemist import Chemist, Medicine, ChemistStock
from backend.models.token import QueueToken, PrescriptionLog
from backend.models.patient import Patient, WhatsAppMessageLog
from backend.models.admin import Admin
from backend.models.blood_bank import BloodBank, BloodStock
from backend.services.auth_service import hash_password

async def main():
    """
    Seeding script for development/pilot environment.
    Recreates tables if needed and seeds baseline dataset (5 of each key entity).
    """
    print("Initializing database tables for seeding...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Seed Admins
        admin_res = await db.execute(select(Admin).where(Admin.email == "admin@sehat.in"))
        if not admin_res.scalar_one_or_none():
            print("Seeding default Admin (admin@sehat.in)...")
            db.add(Admin(
                email="admin@sehat.in",
                name="System Admin",
                password_hash=hash_password("sehat2026")
            ))
            await db.commit()

        # 2. Seed 5 Patients
        patient_phones = ["+919999999901", "+919999999902", "+919999999903", "+919999999904", "+919999999905"]
        patient_names = ["Mohan Singh", "Rajesh Kumar", "Priya Sharma", "Amit Patel", "Sunita Rani"]
        for phone, name in zip(patient_phones, patient_names):
            p_res = await db.execute(select(Patient).where(Patient.phone == phone))
            if not p_res.scalar_one_or_none():
                print(f"Seeding Patient: {name} ({phone})...")
                db.add(Patient(
                    phone=phone,
                    name=name,
                    language_preference="en",
                    last_search_doctor_ids=[]
                ))
        await db.commit()

        # 3. Seed 5 Doctors
        doctors_data = [
            ("Sharma", "General Physician", "+919999999999", "Sharma Health Clinic", "Sector 14, Vasundhara, Ghaziabad", 28.6612, 77.3584),
            ("Verma", "Pediatrician", "+919999999991", "Verma Care Clinic", "Sector 12, Vasundhara, Ghaziabad", 28.6620, 77.3590),
            ("Gupta", "Gynecologist", "+919999999992", "Gupta Women Clinic", "Sector 10, Vasundhara, Ghaziabad", 28.6640, 77.3610),
            ("Patel", "Cardiologist", "+919999999993", "Patel Heart Center", "Indirapuram, Ghaziabad", 28.6680, 77.3630),
            ("Singh", "Dermatologist", "+919999999994", "Singh Skin Clinic", "Vasundhara, Ghaziabad", 28.6590, 77.3560),
        ]
        for name, spec, phone, clinic, addr, lat, lon in doctors_data:
            d_res = await db.execute(select(Doctor).where(Doctor.phone == phone))
            if not d_res.scalar_one_or_none():
                print(f"Seeding Doctor: {name} ({phone})...")
                db.add(Doctor(
                    name=name,
                    specialization=spec,
                    phone=phone,
                    password_hash=hash_password("sehat123"),
                    clinic_name=clinic,
                    address=addr,
                    latitude=lat,
                    longitude=lon,
                    is_available=True,
                    avg_consultation_minutes=15
                ))
        await db.commit()

        # 4. Seed 5 Chemists
        chemists_data = [
            ("Mohan Kumar", "+918888888888", "Mohan Chemists", "Shop 4, Vasundhara, Ghaziabad", 28.6625, 77.3595),
            ("Gupta Owner", "+918888888881", "Gupta Pharmacy", "Sector 12, Vasundhara, Ghaziabad", 28.6635, 77.3605),
            ("City Owner", "+918888888882", "City Medicos", "Indirapuram, Ghaziabad", 28.6600, 77.3570),
            ("Apex Owner", "+918888888883", "Apex Pharma", "Sector 15, Vasundhara, Ghaziabad", 28.6660, 77.3620),
            ("Krishna Owner", "+918888888884", "Krishna Medicos", "Vasundhara, Ghaziabad", 28.6580, 77.3550),
        ]
        for name, phone, shop, addr, lat, lon in chemists_data:
            c_res = await db.execute(select(Chemist).where(Chemist.phone == phone))
            if not c_res.scalar_one_or_none():
                print(f"Seeding Chemist: {shop} ({phone})...")
                db.add(Chemist(
                    name=name,
                    phone=phone,
                    password_hash=hash_password("sehat123"),
                    shop_name=shop,
                    address=addr,
                    latitude=lat,
                    longitude=lon,
                    is_open=True
                ))
        await db.commit()

        # 5. Seed Medicines Catalog (6 entries)
        medicines_data = [
            # generic_name, brand_names, category, schedule, standard_dosages
            ("Paracetamol", ["Crocin", "Calpol", "Dolo 500"], "Analgesic", "H", ["500mg", "650mg"]),
            ("Amoxicillin", ["Novamox", "Mox", "Amoxil"], "Antibiotic", "H", ["250mg", "500mg"]),
            ("Metformin", ["Glycomet", "Obimet", "Gluformin"], "Antidiabetic", "H", ["500mg", "850mg"]),
            ("Atorvastatin", ["Lipvas", "Atorva", "Lipitor"], "Statins", "H", ["10mg", "20mg"]),
            ("Ibuprofen", ["Brufen", "Ibugesic"], "NSAID", "H", ["400mg"]),
            ("Amlodipine", ["Amlopin", "Amlodac"], "Antihypertensive", "H", ["5mg"]),
            ("Ferrous Sulfate", ["FeSO4", "Autrin", "Orofer", "Fefol", "Iron", "Imeron"], "Hematinic", "H", ["200mg"]),
            ("Ascorbic Acid", ["Vitamin C", "Limcee", "Celin", "Suckcee", "Ascorbic Acid"], "Vitamin", "OTC", ["100mg", "500mg"])
        ]
        for name, brands, cat, sched, dosages in medicines_data:
            m_res = await db.execute(select(Medicine).where(Medicine.generic_name == name))
            if not m_res.scalar_one_or_none():
                print(f"Seeding Medicine: {name}...")
                db.add(Medicine(
                    generic_name=name,
                    brand_names=brands,
                    category=cat,
                    schedule=sched,
                    standard_dosages=dosages
                ))
        await db.commit()

        # 6. Seed Chemist Stocks (ensure Mohan Chemists (id=1) has Paracetamol & Metformin)
        meds_res = await db.execute(select(Medicine))
        meds = meds_res.scalars().all()
        med_map = {m.generic_name: m.id for m in meds}

        # Mohan Chemists stocks
        c1_stocks = ["Paracetamol", "Metformin", "Ibuprofen", "Ferrous Sulfate", "Ascorbic Acid"]
        for m_name in c1_stocks:
            m_id = med_map.get(m_name)
            if m_id:
                s_res = await db.execute(select(ChemistStock).where(ChemistStock.chemist_id == 1, ChemistStock.medicine_id == m_id))
                if not s_res.scalar_one_or_none():
                    db.add(ChemistStock(chemist_id=1, medicine_id=m_id, is_available=True, last_updated=datetime.now()))

        # Gupta Pharmacy stocks (stocks Amoxicillin for split lookup tests)
        c2_stocks = ["Amoxicillin", "Atorvastatin"]
        for m_name in c2_stocks:
            m_id = med_map.get(m_name)
            if m_id:
                s_res = await db.execute(select(ChemistStock).where(ChemistStock.chemist_id == 2, ChemistStock.medicine_id == m_id))
                if not s_res.scalar_one_or_none():
                    db.add(ChemistStock(chemist_id=2, medicine_id=m_id, is_available=True, last_updated=datetime.now()))

        # Apex Pharma (id=4) stocks Ferrous Sulfate and Ascorbic Acid
        c4_stocks = ["Ferrous Sulfate", "Ascorbic Acid"]
        for m_name in c4_stocks:
            m_id = med_map.get(m_name)
            if m_id:
                s_res = await db.execute(select(ChemistStock).where(ChemistStock.chemist_id == 4, ChemistStock.medicine_id == m_id))
                if not s_res.scalar_one_or_none():
                    db.add(ChemistStock(chemist_id=4, medicine_id=m_id, is_available=True, last_updated=datetime.now()))
        await db.commit()

        # 7. Seed 5 Blood Banks
        blood_banks_data = [
            ("City Blood Bank", "10, Indirapuram, Ghaziabad", "+917777777777", 28.6610, 77.3580),
            ("Red Cross Blood Centre", "Sector 12, Vasundhara, Ghaziabad", "+917777777771", 28.6650, 77.3600),
            ("Metro Blood Bank", "Indirapuram, Ghaziabad", "+917777777772", 28.6585, 77.3565),
            ("Lifeline Blood Services", "Sector 15, Vasundhara, Ghaziabad", "+917777777773", 28.6700, 77.3650),
            ("Apex Blood Care", "Sector 6, Vasundhara, Ghaziabad", "+917777777774", 28.6520, 77.3500),
        ]
        for name, addr, phone, lat, lon in blood_banks_data:
            bb_res = await db.execute(select(BloodBank).where(BloodBank.phone == phone))
            if not bb_res.scalar_one_or_none():
                print(f"Seeding Blood Bank: {name} ({phone})...")
                db.add(BloodBank(
                    name=name,
                    address=addr,
                    phone=phone,
                    password_hash=hash_password("sehat123"),
                    latitude=lat,
                    longitude=lon,
                    is_open_24hrs=True
                ))
        await db.commit()

        # 8. Seed Blood Stocks per Bank (ensure units_available > 0)
        blood_groups = ["A+", "B+", "O-", "AB+", "O+", "A-", "B-", "AB-"]
        for bank_id in range(1, 6):
            for bg in blood_groups[:4]:  # seed 4 groups per bank
                s_res = await db.execute(select(BloodStock).where(BloodStock.blood_bank_id == bank_id, BloodStock.blood_group == bg))
                if not s_res.scalar_one_or_none():
                    db.add(BloodStock(
                        blood_bank_id=bank_id,
                        blood_group=bg,
                        units_available=10 if bank_id == 1 and bg == "B+" else (bank_id * 2),
                        last_updated=datetime.now()
                    ))
        await db.commit()

        # 9. Seed Queue Tokens for Showcase (Dr. Sharma and Dr. Verma)
        tokens_data = [
            # doctor_id, patient_phone, patient_name, token_number, position, status, wait
            (1, "+919999999901", "Mohan Singh", 1, 1, "waiting", 15),
            (1, "+919999999902", "Rajesh Kumar", 2, 2, "waiting", 30),
            (1, "+919999999903", "Priya Sharma", 3, 3, "called", 0),
            (2, "+919999999904", "Amit Patel", 1, 1, "waiting", 15),
            (2, "+919999999905", "Sunita Rani", 2, 2, "seen", 0)
        ]
        for doc_id, phone, name, t_num, pos, status, wait in tokens_data:
            t_res = await db.execute(
                select(QueueToken).where(
                    QueueToken.doctor_id == doc_id,
                    QueueToken.patient_phone == phone
                )
            )
            if not t_res.scalar_one_or_none():
                print(f"Seeding Queue Token #{t_num} for Doctor ID {doc_id}...")
                db.add(QueueToken(
                    doctor_id=doc_id,
                    patient_phone=phone,
                    patient_name=name,
                    token_number=t_num,
                    position=pos,
                    status=status,
                    estimated_wait_minutes=wait,
                    booked_at=datetime.now(),
                    called_at=datetime.now() if status == "called" else None,
                    seen_at=datetime.now() if status == "seen" else None
                ))
        await db.commit()

        # 10. Seed Prescription Logs for Showcase
        prescriptions_data = [
            ("+919999999901", "https://example.com/rx1.jpg", 0.95, 1,
             {"medicines": [{"name": "Paracetamol", "dosage": "500mg", "frequency": "twice a day"}]},
             "पैरासिटामोल 500mg - दिन में दो बार (दर्द और बुखार के लिए)"),
            ("+919999999902", "https://example.com/rx2.jpg", 0.88, 2,
             {"medicines": [{"name": "Amoxicillin", "dosage": "250mg", "frequency": "thrice a day"}]},
             "एमोक्सिसिलिन 250mg - दिन में तीन बार (बैक्टीरियल इन्फेक्शन के लिए)")
        ]
        for phone, url, conf, chemist_id, meds_json, hindi in prescriptions_data:
            p_res = await db.execute(select(PrescriptionLog).where(PrescriptionLog.patient_phone == phone))
            if not p_res.scalar_one_or_none():
                print(f"Seeding Prescription Log for {phone}...")
                db.add(PrescriptionLog(
                    patient_phone=phone,
                    image_url=url,
                    extracted_medicines=meds_json,
                    matched_chemist_id=chemist_id,
                    hindi_explanation=hindi,
                    ocr_confidence=conf,
                    created_at=datetime.now()
                ))
        await db.commit()

        print("Pilot environment database seeding completed successfully! (5 entries seeded for each table)")

if __name__ == "__main__":
    asyncio.run(main())
