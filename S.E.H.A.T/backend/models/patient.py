from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base

class Patient(Base):
    """
    SQLAlchemy model representing the 'patients' table.
    Tracks patient contact profile history and detected/preferred interaction language.
    """
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    language_preference: Mapped[str] = mapped_column(String(5), default="en", nullable=False)  # "en" or "hi"
    last_search_doctor_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class WhatsAppMessageLog(Base):
    """
    SQLAlchemy model representing the 'whatsapp_message_logs' table.
    Used for recording message timestamps to enforce rate limiting.
    """
    __tablename__ = "whatsapp_message_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_phone: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

