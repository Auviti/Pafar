from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database import Base, CHAR_LENGTH
from sqlalchemy.orm import mapped_column
from datetime import datetime
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
# Driver Model
class Driver(Base):
    __tablename__ = "driver"

    # Driver ID (UUID as the primary key)
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)  # ForeignKey referencing user (UUID)
    rating: Mapped[Float] = mapped_column(Float, nullable=False, default=5.0)  # Rating between 1 and 5
    # Optional timestamp for tracking address creation/updates
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Optional timestamp
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Auto update timestamp

    # One-to-One relationship with Vehicle
    vehicle = relationship("Vehicle", back_populates="driver", uselist=False)

    def __repr__(self):
        return f"<Driver(id={self.id}, name={self.name}, phone_number={self.phone_number}, rating={self.rating})>"

# Vehicle Model
class Vehicle(Base):
    __tablename__ = "vehicle"

    # Vehicle ID (UUID as the primary key)
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    driver_id: Mapped[UUID] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., Car, Van, Truck, etc.
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    color: Mapped[str] = mapped_column(String(50), nullable=True)

    # Back reference to Driver
    driver = relationship("Driver", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, license_number={self.license_number}, model={self.model})>"
