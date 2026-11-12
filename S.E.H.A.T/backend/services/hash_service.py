import hashlib
import os

SALT = os.getenv("PATIENT_PHONE_SALT", "sehat_salt_2026_prod")

def hash_patient_phone(phone: str) -> str:
    """
    Generates a secure SHA256 hash of a patient's phone number.
    Ensures that patient identity (PII) is anonymized at rest.
    """
    clean_phone = phone.strip().replace("whatsapp:", "")
    hasher = hashlib.sha256()
    hasher.update(f"{clean_phone}{SALT}".encode("utf-8"))
    return hasher.hexdigest()
