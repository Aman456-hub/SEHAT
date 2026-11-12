"""
S.E.H.A.T (Smart Emergency & Healthcare Access Terminal)
UltraMsg WhatsApp Live Webhook Runner

This script starts the S.E.H.A.T FastAPI server configured to receive and reply to
WhatsApp messages via UltraMsg webhook at:
  - http://localhost:8000/ultramsg
  - http://localhost:8000/api/whatsapp/webhook
"""

import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Automatically switch to project's virtual environment if executed with system Python
venv_python = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
    sys.exit(subprocess.call([venv_python] + sys.argv))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import uvicorn
from backend.main import app

def print_banner(port: int):
    print("=" * 70)
    print(">> S.E.H.A.T WHATSAPP LIVE WEBHOOK SERVER (UltraMsg Gateway)")
    print("=" * 70)
    print(f"[*] Local Server Running on: http://127.0.0.1:{port}")
    print(f"[*] Swagger API Docs:        http://127.0.0.1:{port}/docs")
    print("-" * 70)
    print("[*] HOW TO CONNECT TO ULTRAMSG (Your Active Gateway):")
    print("1. In a second terminal, start ngrok:")
    print(f"     npx ngrok http {port}")
    print("\n2. In your UltraMsg Dashboard (Instance Settings):")
    print("   Set 'Webhook on Received' to ON")
    print("   Paste your Ngrok URL into 'Webhook URL on Received':")
    print("     https://<your-ngrok-subdomain>.ngrok-free.app/ultramsg")
    print("\n3. Send messages from your phone to test S.E.H.A.T:")
    print("   * 'Hi' or 'Hello'  -> Welcome menu & instructions")
    print("   * Send Location    -> Finds nearby open doctors & wait times")
    print("   * '1' or '2'        -> Books real-time clinic queue token")
    print("   * 'CANCEL'          -> Cancels appointment & notifies patients")
    print("   * Photo upload     -> Gemini Vision OCR & Hindi explanation")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    # Default port is 8000. Can override with PORT env var or cli arg.
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif os.getenv("PORT"):
        try:
            port = int(os.getenv("PORT"))
        except ValueError:
            pass

    print_banner(port)
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
