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

# Bus Model
class Bus(Base):
    __tablename__ = "bus"

    # Bus ID (UUID as the primary key)
    id: mapped_column[UUID] = mapped_column(UUIDType, primary_key=True, default=default)
    bus_number: mapped_column[str] = mapped_column(String(CHAR_LENGTH), nullable=False, unique=True)  # Bus number (e.g., "B123")
    capacity: mapped_column[int] = mapped_column(Integer, nullable=False)  # Passenger capacity
    status: mapped_column[BusStatus] = mapped_column(Enum(BusStatus), nullable=False, default=BusStatus.AVAILABLE)  # Bus status (Available, On Trip, Out of Service)
    driver_id: mapped_column[UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)  # Foreign key referencing Driver (UUID)
    route: mapped_column[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Route information (e.g., "Route 1: A -> B -> C")
    
    # Timestamps
    created_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with Driver
    driver = relationship("Driver", back_populates="buses")

    def __repr__(self):
        return f"<Bus(id={self.id}, bus_number={self.bus_number}, capacity={self.capacity}, status={self.status}, route={self.route})>"

