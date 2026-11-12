from datetime import datetime, time
from typing import List
from sqlalchemy import String, Float, Integer, Boolean, DateTime, Time, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class BloodBank(Base):
    """
    SQLAlchemy model representing the 'blood_banks' table.
    Stores blood bank metadata, location, contact, and operational hours.
    """
    __tablename__ = "blood_banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_open_24hrs: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    opening_time: Mapped[time] = mapped_column(Time, nullable=True)
    closing_time: Mapped[time] = mapped_column(Time, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    stocks: Mapped[List["BloodStock"]] = relationship("BloodStock", back_populates="blood_bank", cascade="all, delete-orphan")


class BloodStock(Base):
    """
    SQLAlchemy model representing the 'blood_stock' table.
    Stores units available for standard blood groups (A+, A-, B+, B-, O+, O-, AB+, AB-) in each blood bank.
    """
    __tablename__ = "blood_stock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blood_bank_id: Mapped[int] = mapped_column(ForeignKey("blood_banks.id", ondelete="CASCADE"), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(3), nullable=False)  # e.g., A+, AB-, O+
    units_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    blood_bank: Mapped["BloodBank"] = relationship("BloodBank", back_populates="stocks")

    # Enforce unique blood group record per blood bank
    __table_args__ = (
        UniqueConstraint("blood_bank_id", "blood_group", name="uq_blood_bank_blood_group"),
    )
