from datetime import datetime, time
from typing import List, Optional
from pydantic import BaseModel, Field


class BloodBankBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    latitude: float
    longitude: float
    is_open_24hrs: bool = True
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None


class BloodBankCreate(BloodBankBase):
    pass


class BloodBankResponse(BloodBankBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BloodStockUpdate(BaseModel):
    blood_group: str = Field(..., max_length=3)  # e.g., A+, AB-, O+
    units_available: int = Field(0, ge=0)


class BloodStockUpdateBulk(BaseModel):
    stocks: List[BloodStockUpdate]


class BloodStockResponse(BaseModel):
    id: int
    blood_bank_id: int
    blood_group: str
    units_available: int
    last_updated: datetime

    class Config:
        from_attributes = True


class BloodStockFullResponse(BloodStockResponse):
    blood_bank: BloodBankResponse

    class Config:
        from_attributes = True
