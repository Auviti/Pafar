from sqlalchemy import Integer, String, ForeignKey, Enum, DateTime, JSON
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
    default = uuid4
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())

    
# Enum for Ride Status
class RideStatus(enum.Enum):
    ASSIGNED = "Assigned"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELED = "Canceled"

# Ride Status Model
class RideStatus(Base):
    __tablename__ = "ride_status"

    # Ride Status ID (UUID as the primary key)
    id: Mapped[UUID] = mapped_column(UUIDType, primary_key=True, default=default)
    booking_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id"), nullable=False)  # Foreign key referencing Booking (UUID)
    ride_status: Mapped[RideStatus] = mapped_column(Enum(RideStatus), nullable=False)  # Ride status (Assigned, Ongoing, Completed, Canceled)
    status_update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Time of status update
    
    # Storing location as a JSON object (latitude, longitude, and address)
    location: Mapped[dict] = mapped_column(JSON, nullable=True)  # Location (can store JSON object like {latitude: float, longitude: float, address: str})

    # Relationships
    booking = relationship("Booking", back_populates="ride_statuses")

    def __repr__(self):
        return f"<RideStatus(id={self.id}, booking_id={self.booking_id}, status={self.ride_status}, time={self.status_update_time})>"
