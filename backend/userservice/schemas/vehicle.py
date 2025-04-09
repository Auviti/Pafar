from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from enum import Enum

from datetime import datetime

# Pydantic schema for VehicleType
class VehicleTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class VehicleTypeCreate(VehicleTypeBase):
    pass

class VehicleTypeResponse(VehicleTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  


# Pydantic schema for Vehicle
class VehicleBase(BaseModel):
    license_number: str
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None

class VehicleCreate(VehicleBase):
    driver_id: UUID
    vehicle_type_id: UUID

class VehicleResponse(VehicleBase):
    id: UUID
    driver_id: UUID
    vehicle_type_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  
