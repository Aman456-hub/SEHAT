from backend.models.chemist import Chemist
from backend.models.doctor import Doctor
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class QueueToken(Base):
    """
    SQLAlchemy model representing the 'queue_tokens' table.
    Manages active doctor queues with patient credentials, token sequencing, status state-machine, and estimated wait times.
    """
    __tablename__ = "queue_tokens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_phone: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    patient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    token_number: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="waiting", nullable=False)  # waiting, called, seen, cancelled
    estimated_wait_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    booked_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    called_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    doctor: Mapped["Doctor"] = relationship("Doctor")

class PrescriptionLog(Base):
    """
    SQLAlchemy model representing the 'prescription_logs' table.
    Stores metadata on OCR processing of prescription images, extracted drug JSON lists, and translation explanation results.
    """
    __tablename__ = "prescription_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_phone: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    # Stored as JSON object matching the OCR prompt output format
    extracted_medicines: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    matched_chemist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chemists.id", ondelete="SET NULL"), nullable=True)
    hindi_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    matched_chemist: Mapped[Optional["Chemist"]] = relationship("Chemist")
