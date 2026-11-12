from datetime import datetime
from typing import List
from sqlalchemy import String, Float, Integer, Boolean, DateTime, func, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

class Chemist(Base):
    """
    SQLAlchemy model representing the 'chemists' table.
    Stores chemist contact, shop, location details and opening status.
    """
    __tablename__ = "chemists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    shop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    
    # Relationship to stocks
    stocks: Mapped[List["ChemistStock"]] = relationship("ChemistStock", back_populates="chemist", cascade="all, delete-orphan")

class Medicine(Base):
    """
    SQLAlchemy model representing the 'medicines' table.
    Stores generic and brand names, categories, medical schedule details, and standard dosages.
    """
    __tablename__ = "medicines"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generic_name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    # Stored as JSON array of strings
    brand_names: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    schedule: Mapped[str] = mapped_column(String(20), default="H", nullable=False)  # H, H1, G, etc.
    # Stored as JSON array of strings
    standard_dosages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Relationship to stocks
    stocks: Mapped[List["ChemistStock"]] = relationship("ChemistStock", back_populates="medicine", cascade="all, delete-orphan")

class ChemistStock(Base):
    """
    SQLAlchemy model representing the 'chemist_stock' table.
    Maps stocks of medicines across chemists with last updated timestamp.
    """
    __tablename__ = "chemist_stock"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chemist_id: Mapped[int] = mapped_column(ForeignKey("chemists.id", ondelete="CASCADE"), nullable=False)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    chemist: Mapped["Chemist"] = relationship("Chemist", back_populates="stocks")
    medicine: Mapped["Medicine"] = relationship("Medicine", back_populates="stocks")

    # Enforce unique medicine stock per chemist
    __table_args__ = (
        UniqueConstraint("chemist_id", "medicine_id", name="uq_chemist_medicine_stock"),
    )
