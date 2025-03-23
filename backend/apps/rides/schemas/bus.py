from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from typing import List
from datetime import datetime
from enum import Enum

class SeatBase(BaseModel):
    seat_number: str
    available: bool = True
    bus_id: UUID
    user_id: Optional[UUID] = None

class SeatCreate(SeatBase):
    pass

class SeatUpdate(SeatBase):
    available: Optional[bool] = None
    user_id: Optional[UUID] = None

class SeatOut(SeatBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models


class BusStatusEnum(str, Enum):
    AVAILABLE = "Available"
    ON_TRIP = "On Trip"
    OUT_OF_SERVICE = "Out of Service"

class BusBase(BaseModel):
    bus_number: str
    capacity: int
    status: BusStatusEnum
    driver_id: UUID

class BusCreate(BusBase):
    pass

class BusUpdate(BusBase):
    bus_number: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[BusStatusEnum] = None
class BusIn(BusBase):
    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models
class BusOut(BusBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    seats: List[SeatOut]  # Relationship to the Seat model

    class Config:
        from_attributes = True  # Enable ORM mapping for SQLAlchemy models
