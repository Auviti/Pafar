from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column
from datetime import datetime
from core.database import Base, CHAR_LENGTH
import uuid
import enum
import sys

# Database type detection for UUID
if 'postgresql' in sys.argv:
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid.uuid4
else:
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid.uuid4())

# Enum for Bus Status (e.g., available, on trip, out of service)
class BusStatus(enum.Enum):
    AVAILABLE = "Available"
    ON_TRIP = "On Trip"
    OUT_OF_SERVICE = "Out of Service"


# Seat Model
class Seat(Base):
    __tablename__ = 'seats'
    
    # Auto-generating a unique seat ID using UUID
    id: mapped_column[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Seat ID
    seat_number: mapped_column[str] = mapped_column(String(10), nullable=False)  # Example: '1A', '2B', etc.
    available: mapped_column[bool] = mapped_column(Boolean, default=True)  # Availability of the seat
    bus_id: mapped_column[UUID] = mapped_column(ForeignKey('buses.id'), nullable=False)  # Foreign key to the bus
    user_id: mapped_column[UUID] = mapped_column(ForeignKey('users.id'), nullable=True)  # Foreign key to user (if seat is booked)
    
    # Relationship to the Bus and User (One-to-many)
    bus: mapped_column['Bus'] = relationship('Bus', back_populates='seats', lazy='dynamic')
    user: mapped_column['User'] = relationship('User', back_populates="seats", lazy='dynamic')

    def __init__(self, seat_number: str, bus_id: UUID, available: bool = True):
        self.seat_number = seat_number
        self.bus_id = bus_id
        self.available = available

    def __repr__(self):
        return f"Seat(seat_number={self.seat_number}, available={self.available}, bus_id={self.bus_id})"


# Bus Model
class Bus(Base):
    __tablename__ = "buses"

    # Bus ID (UUID as the primary key)
    id: mapped_column[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bus_number: mapped_column[str] = mapped_column(String(CHAR_LENGTH), nullable=False, unique=True)  # Bus number (e.g., "B123")
    capacity: mapped_column[int] = mapped_column(Integer, nullable=False)  # Passenger capacity
    status: mapped_column[BusStatus] = mapped_column(Enum(BusStatus), nullable=False, default=BusStatus.AVAILABLE)  # Bus status (Available, On Trip, Out of Service)
    driver_id: mapped_column[UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)  # Foreign key referencing Driver (UUID)
    
    # Timestamps
    created_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    driver = relationship("Driver", back_populates="buses")
    seats = relationship("Seat", back_populates="bus")

    def __repr__(self):
        return f"<Bus(id={self.id}, bus_number={self.bus_number}, capacity={self.capacity}, status={self.status})>"