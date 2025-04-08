from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from .user import UserRole,UserBase,UserUpdate

class VehicleTypeBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=100)

class VehicleTypeCreate(VehicleTypeBase):
    pass  # You can add specific validations for creation here if needed.

class VehicleTypeOut(VehicleTypeBase):
    id: UUID

    class Config:
        from_attributes = True  


# Driver Pydantic Models
class DriverCreate(UserBase):
    rating: Optional[float] = 5.0  # Default to 5.0
    role: UserRole.Driver  # Role of the user (Buyer, Seller, etc.)
    password: str  # User's password for authentication

    pass

class DriverUpdate(UserUpdate):
    rating: Optional[float] = 5.0
    pass

class DriverView(DriverCreate):
    
    class Config:
        from_attributes = True  

class DriverOut(DriverBase):
    id: UUID
    vehicle_id: Optional[UUID]  # Optional, because the driver may not have a vehicle.

    class Config:
        from_attributes = True  


class VehicleBase(BaseModel):
    license_number: str = Field(..., max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int]
    color: Optional[str] = Field(None, max_length=50)

class VehicleCreate(VehicleBase):
    vehicle_type_id: UUID  # This is required when creating a vehicle.
    driver_id: UUID  # This is required when creating a vehicle.

class VehicleOut(VehicleBase):
    id: UUID
    vehicle_type: str  # We can include the vehicle type name in the response
    driver: Optional[DriverOut]  # To return the associated driver in the response.

    class Config:
        from_attributes = True  
