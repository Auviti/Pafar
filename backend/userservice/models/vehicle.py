from sqlalchemy import Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core.database import Base, CHAR_LENGTH
from datetime import datetime
import uuid
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from .user import User
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

# VehicleType Model (This is the new class)
class VehicleType(Base):
    __tablename__ = "vehicle_types"

    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    name: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False, unique=True)  # Type name, e.g., Car, Van, Truck
    description: Mapped[str] = mapped_column(Text, nullable=True)  # Optional description

    # Relationship back to Vehicle
    vehicles: Mapped["Vehicle"] = relationship("Vehicle", back_populates="vehicle_type")

    def __repr__(self):
        return f"<VehicleType(id={self.id}, name={self.name}, description={self.description})>"

# Vehicle Model
class Vehicle(Base):
    __tablename__ = "vehicles"  # Plural table name is typically preferred

    # Vehicle ID (UUID as the primary key)
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    driver_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    vehicle_type_id: Mapped[UUID] = mapped_column(ForeignKey("vehicle_types.id"), nullable=False)  # Foreign key to VehicleType
    license_number: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)
    model: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    color: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)

    # Relationship to VehicleType
    vehicle_type: Mapped["VehicleType"] = relationship("VehicleType", back_populates="vehicles")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, license_number={self.license_number}, model={self.model})>"
