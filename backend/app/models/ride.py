"""
Ride model for managing ride requests and tracking.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text, DECIMAL, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


class RideStatus(str, Enum):
    """Ride status enumeration."""
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Location(Base):
    """Location model for storing pickup and destination locations."""
    
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Ride(Base):
    """Ride model for managing ride requests and tracking."""
    
    __tablename__ = "rides"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    pickup_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    destination_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=False)
    
    status = Column(SQLEnum(RideStatus), nullable=False, default=RideStatus.REQUESTED)
    estimated_fare = Column(DECIMAL(10, 2), nullable=False)
    actual_fare = Column(DECIMAL(10, 2), nullable=True)
    estimated_duration = Column(Integer, nullable=False)  # minutes
    actual_duration = Column(Integer, nullable=True)  # minutes
    distance = Column(Float, nullable=False)  # kilometers
    
    # Timestamps
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Relationships
    customer = relationship("User", foreign_keys=[customer_id])
    driver = relationship("User", foreign_keys=[driver_id])
    pickup_location = relationship("Location", foreign_keys=[pickup_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    
    def __repr__(self):
        return f"<Ride(id={self.id}, status={self.status}, customer_id={self.customer_id})>"


class DriverLocation(Base):
    """Driver location model for real-time tracking."""
    
    __tablename__ = "driver_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    heading = Column(Float, nullable=True)  # degrees
    speed = Column(Float, nullable=True)  # km/h
    is_available = Column(Boolean, default=True, nullable=False)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    driver = relationship("User")
    
    def __repr__(self):
        return f"<DriverLocation(driver_id={self.driver_id}, lat={self.latitude}, lng={self.longitude})>"