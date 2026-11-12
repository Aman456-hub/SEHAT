from datetime import datetime
from pydantic import BaseModel, Field

class DoctorBase(BaseModel):
    name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20, description="Contact phone number of the doctor")
    clinic_name: str = Field(..., max_length=100)
    address: str = Field(..., max_length=255)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    specialization: str = Field(..., max_length=100)
    avg_consultation_minutes: int = Field(default=15, ge=1)

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdateAvailability(BaseModel):
    is_available: bool

class DoctorResponse(DoctorBase):
    id: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NearbyDoctorResponse(DoctorResponse):
    distance_km: float
    estimated_wait_minutes: int
