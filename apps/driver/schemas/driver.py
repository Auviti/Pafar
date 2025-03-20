from pydantic import BaseModel
from typing import Optional
import uuid

# Driver Pydantic Models
class DriverCreate(BaseModel):
    user_id: uuid.UUID  # Foreign key to User
    rating: Optional[float] = 5.0  # Default to 5.0

    class Config:
        from_attributes = True  


class DriverRead(DriverCreate):
    id: uuid.UUID
    created_at: str  # DateTime as string for simplicity
    updated_at: str  # DateTime as string for simplicity

    class Config:
        from_attributes = True  


# Vehicle Pydantic Models
class VehicleCreate(BaseModel):
    vehicle_type: str
    license_number: str
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True  


class VehicleRead(VehicleCreate):
    id: uuid.UUID
    driver_id: uuid.UUID  # Link to the Driver

    class Config:
        from_attributes = True  
