from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TokenBook(BaseModel):
    doctor_id: int
    patient_phone: str = Field(..., max_length=20)
    patient_name: str = Field(..., max_length=100)

class TokenUpdateStatus(BaseModel):
    status: str = Field(..., description="Must be one of: waiting, called, seen, cancelled")

class TokenResponse(BaseModel):
    id: int
    doctor_id: int
    patient_phone: str
    patient_name: str
    token_number: int
    position: int
    status: str
    estimated_wait_minutes: int
    booked_at: datetime
    called_at: Optional[datetime] = None
    seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True
