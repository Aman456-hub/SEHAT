import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from backend.services.notification_service import send_whatsapp_notification

# Default test recipient (user's active phone)
DEFAULT_PHONE = os.getenv("TEST_WHATSAPP_PHONE", "+919868401672")
PATIENT_NAME = "Aman Chhimwal"

NOTIFICATION_PRESETS = {
    "1": {
        "title": "🎫 Token Booking Confirmation",
        "description": "Sent when patient books an appointment via WhatsApp or web",
        "message": (
            f"🎉 *Appointment Confirmed!*\n\n"
            f"Hello {PATIENT_NAME}, your booking is confirmed with *Dr. Patel* (Cardiologist).\n"
            f"📍 *Clinic:* Patel Heart Center\n"
            f"🎫 *Token Number:* #1\n"
            f"👥 *Queue Position:* #1\n"
            f"🕒 *Estimated Wait:* ~0 mins\n"
            f"🗺️ *Clinic Directions:* https://www.google.com/maps/dir/?api=1&destination=28.668,77.363\n\n"
            f"We will notify you when your turn is close. Reply *STATUS* to check live queue or *CANCEL* if you cannot attend."
        )
    },
    "2": {
        "title": "🔔 Patient Called (Doctor Calling You Now)",
        "description": "Sent when the doctor presses 'Call Patient' on the dashboard",
        "message": (
            f"🔔 *It's Your Turn!*\n\n"
            f"Hello {PATIENT_NAME}, Token #1 is now being called!\n"
            f"Please enter Dr. Patel's consultation room at Patel Heart Center now."
        )
    },
    "3": {
        "title": "⏳ Almost Your Turn (Queue Shift / Position #2 Alert)",
        "description": "Sent automatically when patient reaches position #2 in queue",
        "message": (
            f"⏳ *Almost Your Turn!*\n\n"
            f"Dear {PATIENT_NAME}, you are now *#2 in line* for Dr. Patel.\n"
            f"📍 *Clinic:* Patel Heart Center\n"
            f"🕒 *Est. Wait:* ~10 mins\n"
            f"🗺️ *Directions:* https://www.google.com/maps/dir/?api=1&destination=28.668,77.363\n\n"
            f"Please head to the clinic waiting area now."
        )
    },
    "3b": {
        "title": "⏳ Next in Line (Queue Shift / Position #1 Alert)",
        "description": "Sent automatically when patient reaches position #1 in queue",
        "message": (
            f"⏳ *Almost Your Turn!*\n\n"
            f"Dear {PATIENT_NAME}, you are now *#1 in line* for Dr. Patel.\n"
            f"📍 *Clinic:* Patel Heart Center\n"
            f"🕒 *Est. Wait:* ~0 mins\n"
            f"🗺️ *Directions:* https://www.google.com/maps/dir/?api=1&destination=28.668,77.363\n\n"
            f"Please be ready outside the consultation room."
        )
    },
    "4": {
        "title": "⏱️ Doctor Delay Announcement",
        "description": "Sent when doctor reports a delay or emergency delay in queue",
        "message": (
            f"⚠️ *Clinic Schedule Update*\n\n"
            f"Dear {PATIENT_NAME}, Dr. Patel is currently attending to an emergency procedure and running *~20 minutes behind schedule*.\n\n"
            f"🎫 Your Token #1 remains active.\n"
            f"🕒 Revised Estimated Wait: ~25 mins.\n"
            f"We apologize for the inconvenience."
        )
    },
    "5": {
        "title": "❌ Doctor Emergency / Cancellation",
        "description": "Sent if doctor marks themselves unavailable/offline",
        "message": (
            f"📢 *Doctor Unavailable Alert*\n\n"
            f"Dear {PATIENT_NAME}, Dr. Patel has marked themselves unavailable for today due to an unavoidable emergency.\n\n"
            f"Your Token #1 has been cancelled. Text *DOCTOR* to book with another nearby clinic. We apologize for the inconvenience."
        )
    },
    "6": {
        "title": "💊 Chemist Stock Availability (Prescription / Dawa)",
        "description": "Sent when local chemist inventory matches prescribed medicines",
        "message": (
            f"*Scan Complete!* 🔬\n\n"
            f"*Medicines Extracted:*\n"
            f"• Paracetamol 650mg (Dolo 650)\n"
            f"• Pantoprazole 40mg (Pan 40)\n\n"
            f"📍 *Available Nearby:* Apex Pharma (1.8 km away)\n"
            f"📞 Phone: +918888888883\n"
            f"🗺️ *Directions:* https://www.google.com/maps/dir/?api=1&destination=28.666,77.362\n\n"
            f"Reply with *EXPLAIN* to receive explanations for these medicines in simple Hindi."
        )
    },
    "7": {
        "title": "🇮🇳 Hindi Medicine Explanation (EXPLAIN)",
        "description": "Sent when user replies 'EXPLAIN' for conversational Hindi dosage advice",
        "message": (
            f"यह रही आपकी दवाइयों की सरल जानकारी:\n\n"
            f"1. Dolo 650 (पैरासिटामोल):\n"
            f"→ यह दवाई बुखार और बदन दर्द के लिए है।\n"
            f"→ इसे खाना खाने के बाद लेना है।\n"
            f"→ दिन में 2 बार (सुबह और रात)।\n"
            f"→ 3 दिन तक लें।\n\n"
            f"2. Pan 40 (पैंटोप्राजोल):\n"
            f"→ यह दवाई गैस और एसिडिटी रोकने के लिए है।\n"
            f"→ सुबह खाली पेट पानी के साथ लें।\n"
            f"→ दिन में 1 बार।\n\n"
            f"⚠️ *Disclaimer:* This Hindi translation is AI-generated for informational support. Please verify all medications and instructions with your doctor or pharmacist."
        )
    },
    "8": {
        "title": "🩸 Emergency Blood Bank Availability",
        "description": "Sent when patient searches for blood group (e.g. O+ or B+)",
        "message": (
            f"🩸 *O+ Blood Available Near You:*\n\n"
            f"1. *Ghaziabad District Red Cross Blood Center* - Navyug Market (2.4 km away)\n"
            f"   Units: 8 units  |  Contact: +911202888101\n"
            f"   Open: 24 hours\n"
            f"   🗺️ Directions: https://www.google.com/maps/dir/?api=1&destination=28.667,77.432\n\n"
            f"2. *Rotary Blood Bank* - Sector 10 Vasundhara (5.8 km away)\n"
            f"   Units: 4 units  |  Contact: +911202888102\n"
            f"   Open: 24 hours\n"
            f"   🗺️ Directions: https://www.google.com/maps/dir/?api=1&destination=28.661,77.364"
        )
    }
}

async def send_single_test(phone: str, key: str):
    preset = NOTIFICATION_PRESETS.get(key)
    if not preset:
        print(f"❌ Invalid selection: {key}")
        return False
    print(f"\n🚀 Sending: {preset['title']}")
    print(f"📱 To: {phone}")
    success = await send_whatsapp_notification(phone, preset["message"])
    if success:
        print("✅ WhatsApp message delivered successfully via UltraMsg!")
    else:
        print("❌ Delivery failed. Check terminal logs.")
    return success

async def run_all_tests(phone: str):
    print(f"\n=======================================================")
    print(f"   S.E.H.A.T Full Notification Test Suite (All 8)")
    print(f"   Target Phone: {phone}")
    print(f"=======================================================\n")
    for key, preset in sorted(NOTIFICATION_PRESETS.items()):
        await send_single_test(phone, key)
        await asyncio.sleep(2)
    print("\n🎉 All 8 test notifications sent!")

async def main():
    phone = DEFAULT_PHONE
    if len(sys.argv) > 1 and sys.argv[1].startswith("+"):
        phone = sys.argv[1]
        action = sys.argv[2] if len(sys.argv) > 2 else None
    elif len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = None

    if action:
        if action == "all" or action == "9":
            await run_all_tests(phone)
        elif action in NOTIFICATION_PRESETS:
            await send_single_test(phone, action)
        else:
            print(f"Unknown action '{action}'. Available: 1-8 or 'all'")
        return

    # Interactive menu
    print("\n=======================================================")
    print("   🏥 S.E.H.A.T WhatsApp Notification Testing Tool")
    print(f"   Target Phone: {phone}")
    print("=======================================================")
    print("Select a notification to test:\n")
    for k, p in sorted(NOTIFICATION_PRESETS.items()):
        print(f"  [{k}] {p['title']}")
        print(f"      ({p['description']})")
    print(f"  [9] 🚀 Send ALL 8 Notifications Sequentially")
    print(f"  [0] ❌ Exit\n")

    try:
        choice = input("Enter choice (0-9) [Default: 2 - Call Patient]: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        return

    if not choice:
        choice = "2"

    if choice == "0":
        print("Exited.")
        return
    elif choice == "9" or choice.lower() == "all":
        await run_all_tests(phone)
    elif choice in NOTIFICATION_PRESETS:
        await send_single_test(phone, choice)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    asyncio.run(main())
