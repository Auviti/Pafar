from pydantic import BaseModel
from typing import Optional
import uuid
from .user import UserRole,UserBase,UserUpdate

# Driver Pydantic Models
class DriverCreate(UserBase):
    rating: Optional[float] = 5.0  # Default to 5.0
    role: UserRole.Driver  # Role of the user (Buyer, Seller, etc.)
    password: str  # User's password for authentication

    pass

class DriverUpdate(UserUpdate):
    pass

class DriverView(DriverCreate):
    
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
