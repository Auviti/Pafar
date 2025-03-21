from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, JSON, Float, CheckConstraint
from sqlalchemy.orm import relationship
from core.database import Base, CHAR_LENGTH
from sqlalchemy.orm import mapped_column
from datetime import datetime
import enum
import uuid
from sqlalchemy.dialects.postgresql import UUID
import sys

# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid.uuid4  # Changed from uuid4 to uuid.uuid4 (correct)
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid.uuid4())

# Enum for Ride Status
class RideStatus(enum.Enum):
    ASSIGNED = "Assigned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

# Ride Model
class Ride(Base):
    __tablename__ = "ride"

    # Ride Status ID (UUID as the primary key)
    id: mapped_column[UUID] = mapped_column(UUIDType, primary_key=True, default=default)
    status: mapped_column[RideStatus] = mapped_column(Enum(RideStatus), nullable=False)  # Ride status (Assigned, Ongoing, Completed, Canceled)
    driver_id: mapped_column[UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)  # Foreign key referencing Driver (UUID)
    trip_fare: mapped_column[Float] = mapped_column(Float, nullable=False)  # Fare amount for the trip
    passengers: mapped_column[Integer] = mapped_column(Integer, default=0)  # Number of passengers

    # Storing location as a JSON object (latitude, longitude, and address)
    startlocation: mapped_column[dict] = mapped_column(JSON, nullable=True)  # Location (can store JSON object like {latitude: float, longitude: float, address: str})
    endlocation: mapped_column[dict] = mapped_column(JSON, nullable=True)  # Location (can store JSON object like {latitude: float, longitude: float, address: str})

    # Timestamps
    starts_at: mapped_column[datetime] = mapped_column(DateTime)  # Start time of the ride
    ends_at: mapped_column[datetime] = mapped_column(DateTime)  # End time of the ride
    
    created_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Created timestamp (UTC)
    updated_at: mapped_column[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Updated timestamp (auto updates)

    suitcase: mapped_column[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for suitcase weight')  # Weight of suitcase
    handluggage: mapped_column[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for hand luggage weight')  # Weight of hand luggage
    otherluggage: mapped_column[Float] = mapped_column(Float, default=0.0, nullable=False, comment='0.02 per unit price for other luggage weight')  # Weight of other luggage

    __table_args__ = (
        CheckConstraint(suitcase >= 0, name="check_suitcase_weight_positive"),
        CheckConstraint(handluggage >= 0, name="check_handluggage_weight_positive"),
        CheckConstraint(otherluggage >= 0, name="check_otherluggage_weight_positive"),
    )

    @property
    def duration(self):
        """Calculate duration of the ride (end - start)"""
        if self.starts_at and self.ends_at:
            return (self.ends_at - self.starts_at).total_seconds()  # Duration in seconds
        return None

    @property
    def total_fare(self):
        """Calculate the total fare, considering luggage prices"""
        luggage_fare = 0.02 * (self.suitcase + self.handluggage + self.otherluggage)
        return self.trip_fare + luggage_fare

    def __repr__(self):
        return f"<Ride(id={self.id}, startlocation={self.startlocation}, endlocation={self.endlocation}, duration={self.duration}, status={self.status}, fare_amount={self.total_fare})>"
