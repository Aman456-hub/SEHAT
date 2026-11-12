import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment configuration variables
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base, AsyncSessionLocal
from backend.routers import doctors, tokens, whatsapp, chemists, admin, auth, blood_banks
from backend.services.queue_service import auto_cancel_expired_tokens

# Register all models for SQLAlchemy table creation
from backend.models.doctor import Doctor
from backend.models.chemist import Chemist, Medicine, ChemistStock
from backend.models.token import QueueToken, PrescriptionLog
from backend.models.patient import Patient, WhatsAppMessageLog
from backend.models.admin import Admin
from backend.models.blood_bank import BloodBank, BloodStock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

from datetime import datetime

async def run_auto_cancel_loop():
    """
    Background execution loop to automatically enforce Business Rule 1 (Token auto-cancel).
    Runs every 30 seconds to clean up patients who failed to arrive within 10 minutes
    after being called, advancing the queue.
    """
    logger.info("Background token auto-cancellation scheduler started.")
    while True:
        try:
            await asyncio.sleep(30)
            async with AsyncSessionLocal() as db:
                cancelled_count = await auto_cancel_expired_tokens(db)
                if cancelled_count > 0:
                    logger.info(f"[Scheduler] Automatically cancelled {cancelled_count} expired tokens.")
        except asyncio.CancelledError:
            logger.info("Background token auto-cancellation scheduler cancelling...")
            break
        except Exception as e:
            logger.error(f"[Scheduler Error] Error in auto-cancellation scheduler: {str(e)}")

async def run_cron_jobs_loop():
    """
    Periodic background loop running every 60 seconds to check and trigger cron schedules:
    - At 00:00 midnight: reset active doctor queues
    - At 09:00 AM: trigger stale stock update notifications
    """
    logger.info("Background cron jobs scheduler loop started.")
    last_run_date = None
    last_reminder_date = None
    while True:
        try:
            await asyncio.sleep(60)
            now = datetime.now()
            
            # Midnight reset
            if now.hour == 0 and now.minute == 0 and now.date() != last_run_date:
                async with AsyncSessionLocal() as db:
                    from backend.services.cron_jobs import run_midnight_queue_cleanup
                    await run_midnight_queue_cleanup(db)
                last_run_date = now.date()
                
            # 09:00 AM stock reminders
            if now.hour == 9 and now.minute == 0 and now.date() != last_reminder_date:
                async with AsyncSessionLocal() as db:
                    from backend.services.cron_jobs import trigger_stale_stock_reminders
                    await trigger_stale_stock_reminders(db)
                last_reminder_date = now.date()
                
        except asyncio.CancelledError:
            logger.info("Background cron jobs scheduler cancelling...")
            break
        except Exception as e:
            logger.error(f"[Cron Scheduler Error] {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup Logic
    logger.info("Initializing S.E.H.A.T Database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified.")

    # Start background task loops
    bg_task = asyncio.create_task(run_auto_cancel_loop())
    cron_task = asyncio.create_task(run_cron_jobs_loop())
    
    yield  # Hand over control to FastAPI request listener
    
    # 2. Shutdown Logic
    logger.info("Stopping background tasks and releasing database engine pools...")
    bg_task.cancel()
    cron_task.cancel()
    try:
        await bg_task
        await cron_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    logger.info("S.E.H.A.T application shutdown complete.")

# Initialize the FastAPI App with lifespan context
app = FastAPI(
    title="SEHAT API",
    description="Backend coordinator API for the SEHAT WhatsApp-first healthcare platform.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
# Allows React dashboards (typically on localhost:5173) to fetch the API safely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production/staging config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(doctors.router)
app.include_router(tokens.router)
app.include_router(whatsapp.router)
app.include_router(chemists.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(blood_banks.router)

# Primary and alias webhook routes for UltraMsg gateway
app.add_api_route("/ultramsg", whatsapp.ultramsg_webhook, methods=["POST"])
app.add_api_route("/api/ultramsg/webhook", whatsapp.ultramsg_webhook, methods=["POST"])
app.add_api_route("/reply_whatsapp", whatsapp.ultramsg_webhook, methods=["POST"])
app.add_api_route("/", whatsapp.ultramsg_webhook, methods=["POST"])

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to the SEHAT Healthcare API",
        "data": {
            "status": "healthy",
            "environment": "development"
        },
        "error": None
    }
