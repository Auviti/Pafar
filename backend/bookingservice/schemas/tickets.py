from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


# Enum for Ticket Status
class TicketStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ASSIGNED = "ASSIGNED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

class TicketClass(str, Enum):
    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST_CLASS = "FIRST_CLASS"

class TicketType(str, Enum):
    ROUND = "ROUND"
    ONE_WAY = "ONE_WAY"
    MULTICITY = "MULTICITY"

# Pydantic Schema for Ticket
class Ticket(BaseModel):
    name: Optional[str] = None
    status: TicketStatus
    ticket_class: TicketClass
    ticket_type: TicketType
    vehicle_id: str
    trip_fare: float
    startlocation: str
    currentlocation: str
    endlocation: str
    starts_at: str
    ends_at: str
    passengers: int
    suitcase: float = 0.0
    handluggage: float = 0.0
    otherluggage: float = 0.0

    class Config:
        from_attributes = True

class TicketCreate(Ticket):
    pass

class TicketUpdate(Ticket):
    pass

class TicketFilter(BaseModel):
    id: Optional[UUID] = None
    name: Optional[str] = None
    status: Optional[TicketStatus] = None
    ticket_class: Optional[TicketClass] = None
    ticket_type: Optional[TicketType] = None
    vehicle_id: Optional[str] = None
    trip_fare: Optional[float] = None
    startlocation: Optional[str] = None
    currentlocation: Optional[str] = None
    endlocation: Optional[str] = None
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    suitcase: Optional[float] = None
    handluggage: Optional[float] = None
    otherluggage: Optional[float] = None
    passengers: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TicketResponse(Ticket):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def duration(self):
        """Calculate duration of the ticket (end - start)"""
        if self.starts_at and self.ends_at:
            return (self.ends_at - self.starts_at).total_seconds()
        return None

    @property
    def total_fare(self):
        """Calculate the total fare, considering luggage prices"""
        luggage_fare = 0.02 * (self.suitcase + self.handluggage + self.otherluggage)
        return self.trip_fare + luggage_fare
