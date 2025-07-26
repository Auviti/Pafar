"""
Fleet management models for terminals, routes, buses, and trips.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, DECIMAL, Text, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class TripStatus(str, enum.Enum):
    """Trip status enumeration."""
    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class Terminal(Base):
    """Terminal model for bus stations."""
    
    __tablename__ = "terminals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    origin_routes = relationship("Route", back_populates="origin_terminal", foreign_keys="Route.origin_terminal_id")
    destination_routes = relationship("Route", back_populates="destination_terminal", foreign_keys="Route.destination_terminal_id")
    
    def __repr__(self) -> str:
        return f"<Terminal(id={self.id}, name={self.name}, city={self.city})>"


class Route(Base):
    """Route model connecting two terminals."""
    
    __tablename__ = "routes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_terminal_id = Column(UUID(as_uuid=True), ForeignKey("terminals.id"), nullable=False)
    destination_terminal_id = Column(UUID(as_uuid=True), ForeignKey("terminals.id"), nullable=False)
    distance_km = Column(DECIMAL(8, 2), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    base_fare = Column(DECIMAL(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    origin_terminal = relationship("Terminal", back_populates="origin_routes", foreign_keys=[origin_terminal_id])
    destination_terminal = relationship("Terminal", back_populates="destination_routes", foreign_keys=[destination_terminal_id])
    trips = relationship("Trip", back_populates="route")
    
    def __repr__(self) -> str:
        return f"<Route(id={self.id}, origin={self.origin_terminal_id}, destination={self.destination_terminal_id})>"


class Bus(Base):
    """Bus model for fleet management."""
    
    __tablename__ = "buses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_plate = Column(String(20), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=True)
    capacity = Column(Integer, nullable=False)
    amenities = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    trips = relationship("Trip", back_populates="bus")
    
    def __repr__(self) -> str:
        return f"<Bus(id={self.id}, license_plate={self.license_plate}, capacity={self.capacity})>"


class Trip(Base):
    """Trip model for scheduled bus journeys."""
    
    __tablename__ = "trips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.SCHEDULED, nullable=False)
    fare = Column(DECIMAL(10, 2), nullable=False)
    available_seats = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    route = relationship("Route", back_populates="trips")
    bus = relationship("Bus", back_populates="trips")
    driver = relationship("User", back_populates="driven_trips", foreign_keys=[driver_id])
    bookings = relationship("Booking", back_populates="trip")
    locations = relationship("TripLocation", back_populates="trip")
    
    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, route={self.route_id}, departure={self.departure_time})>"