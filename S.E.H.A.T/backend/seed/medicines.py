import asyncio
import sys
from sqlalchemy import select
from backend.database import engine, Base, AsyncSessionLocal
from backend.models.chemist import Medicine

# Baseline list of common medicines in semi-urban India
BASELINE_MEDICINES = [
    {
        "generic_name": "Paracetamol 500mg",
        "brand_names": ["Crocin", "Calpol", "Dolo 500"],
        "category": "Analgesic / Antipyretic",
        "schedule": "G",
        "standard_dosages": ["1 tablet every 6 hours", "1 tablet after meals for fever"]
    },
    {
        "generic_name": "Ibuprofen 400mg",
        "brand_names": ["Brufen 400", "Combiflam", "Ibugesic"],
        "category": "NSAID / Painkiller",
        "schedule": "H",
        "standard_dosages": ["1 tablet twice daily after meals", "1 tablet as needed for severe pain"]
    },
    {
        "generic_name": "Amoxicillin 500mg",
        "brand_names": ["Amoxil", "Novamox 500", "Mox 500"],
        "category": "Antibiotic",
        "schedule": "H",
        "standard_dosages": ["1 capsule three times daily for 5 days", "1 capsule twice daily for 7 days"]
    },
    {
        "generic_name": "Cetirizine 10mg",
        "brand_names": ["Alerid", "Okacet", "Zyrtec"],
        "category": "Antihistamine / Anti-allergy",
        "schedule": "G",
        "standard_dosages": ["1 tablet at bedtime", "1 tablet daily in the morning"]
    },
    {
        "generic_name": "Metformin 500mg",
        "brand_names": ["Glycomet 500", "Obimet", "Glucophage"],
        "category": "Antidiabetic",
        "schedule": "H",
        "standard_dosages": ["1 tablet twice daily with meals", "1 tablet daily with breakfast"]
    },
    {
        "generic_name": "Pantoprazole 40mg",
        "brand_names": ["Pan 40", "Pantocid", "Pantosec"],
        "category": "Antacid / Proton Pump Inhibitor",
        "schedule": "H",
        "standard_dosages": ["1 tablet daily in the morning on an empty stomach"]
    }
]

async def seed_medicines():
    """
    Seeds baseline medicines list in the database.
    Ensures no duplicates by checking generic_name before inserting.
    """
    print("Verifying database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("Seeding baseline medicines database...")
        seeded_count = 0
        for med_data in BASELINE_MEDICINES:
            # Check if medicine already exists
            stmt = select(Medicine).where(Medicine.generic_name == med_data["generic_name"])
            result = await db.execute(stmt)
            existing_med = result.scalar_one_or_none()

            if not existing_med:
                new_med = Medicine(
                    generic_name=med_data["generic_name"],
                    brand_names=med_data["brand_names"],
                    category=med_data["category"],
                    schedule=med_data["schedule"],
                    standard_dosages=med_data["standard_dosages"]
                )
                db.add(new_med)
                seeded_count += 1
                print(f"Added medicine: {med_data['generic_name']} ({', '.join(med_data['brand_names'])})")
            else:
                # Update brand names if needed
                existing_brands = set(existing_med.brand_names)
                new_brands = set(med_data["brand_names"])
                if not new_brands.issubset(existing_brands):
                    existing_med.brand_names = list(existing_brands.union(new_brands))
                    db.add(existing_med)
                    print(f"Updated brand names for: {existing_med.generic_name}")

        await db.commit()
        print(f"Medicine seeding complete. {seeded_count} new entries created.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_medicines())
