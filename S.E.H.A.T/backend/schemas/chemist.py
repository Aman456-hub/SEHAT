from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ChemistBase(BaseModel):
    name: str = Field(..., max_length=100)
    shop_name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    address: str = Field(..., max_length=255)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    is_open: bool = True

class ChemistCreate(ChemistBase):
    pass

class ChemistResponse(ChemistBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MedicineResponse(BaseModel):
    id: int
    generic_name: str
    brand_names: List[str]
    category: str
    schedule: str
    standard_dosages: List[str]

    class Config:
        from_attributes = True

class StockToggle(BaseModel):
    medicine_id: int
    is_available: bool

class StockUpdateBulk(BaseModel):
    stocks: List[StockToggle]

class ChemistStockResponse(BaseModel):
    id: int
    chemist_id: int
    medicine_id: int
    is_available: bool
    last_updated: datetime
    medicine: Optional[MedicineResponse] = None

    class Config:
        from_attributes = True
