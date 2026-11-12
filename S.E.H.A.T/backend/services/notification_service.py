import os
import logging
import httpx
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_service")

# Retrieve UltraMsg credentials
ULTRAMSG_INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID")
ULTRAMSG_TOKEN = os.getenv("ULTRAMSG_TOKEN")

if ULTRAMSG_INSTANCE_ID and ULTRAMSG_TOKEN:
    logger.info(f"UltraMsg WhatsApp provider active (Instance: {ULTRAMSG_INSTANCE_ID}).")
else:
    logger.warning("No live UltraMsg credentials found. Notification service running in MOCK mode.")


async def send_whatsapp_notification(to_phone: str, message_body: str) -> bool:
    """
    Sends a WhatsApp message to a patient using UltraMsg API.
    Gracefully falls back to console mock mode for local testing if credentials are absent.
    """
    # 1. Clean phone number (format: +<country_code><digits>)
    clean_phone = to_phone.replace("whatsapp:", "").replace("@c.us", "").replace("@s.whatsapp.net", "").strip()
    if not clean_phone.startswith("+"):
        clean_phone = f"+{clean_phone}"

    # 2. Dispatch via UltraMsg if configured
    instance_id = os.getenv("ULTRAMSG_INSTANCE_ID") or ULTRAMSG_INSTANCE_ID
    token = os.getenv("ULTRAMSG_TOKEN") or ULTRAMSG_TOKEN

    if instance_id and token:
        try:
            url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
            payload = {
                "token": token,
                "to": clean_phone,
                "body": message_body
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, data=payload)
                if resp.status_code == 200:
                    logger.info(f"WhatsApp sent via UltraMsg to {clean_phone}: {resp.json()}")
                    return True
                else:
                    logger.error(f"UltraMsg error response ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Failed to send via UltraMsg to {clean_phone}: {str(e)}")

    # 3. Mock mode fallback (local development / offline testing)
    logger.info(
        f"\n--- [MOCK WHATSAPP NOTIFICATION] ---\n"
        f"TO: {clean_phone}\n"
        f"BODY: {message_body}\n"
        f"------------------------------------\n"
    )
    return True
