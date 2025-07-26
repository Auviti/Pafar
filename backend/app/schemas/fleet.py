"""
Pydantic schemas for fleet management operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.models.fleet import TripStatus


# Terminal schemas
class TerminalBase(BaseModel):
    """Base terminal schema."""
    name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    is_active: bool = True


class TerminalCreate(TerminalBase):
    """Schema for creating a terminal."""
    pass


class TerminalUpdate(BaseModel):
    """Schema for updating a terminal."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    is_active: Optional[bool] = None


class Terminal(TerminalBase):
    """Schema for terminal response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Route schemas
class RouteBase(BaseModel):
    """Base route schema."""
    origin_terminal_id: UUID
    destination_terminal_id: UUID
    distance_km: Optional[Decimal] = Field(None, gt=0)
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    base_fare: Decimal = Field(..., gt=0)
    is_active: bool = True

    @validator('destination_terminal_id')
    def validate_different_terminals(cls, v, values):
        if 'origin_terminal_id' in values and v == values['origin_terminal_id']:
            raise ValueError('Origin and destination terminals must be different')
        return v


class RouteCreate(RouteBase):
    """Schema for creating a route."""
    pass


class RouteUpdate(BaseModel):
    """Schema for updating a route."""
    origin_terminal_id: Optional[UUID] = None
    destination_terminal_id: Optional[UUID] = None
    distance_km: Optional[Decimal] = Field(None, gt=0)
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    base_fare: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None

    @validator('destination_terminal_id')
    def validate_different_terminals(cls, v, values):
        if 'origin_terminal_id' in values and v and values['origin_terminal_id'] and v == values['origin_terminal_id']:
            raise ValueError('Origin and destination terminals must be different')
        return v


class Route(RouteBase):
    """Schema for route response."""
    id: UUID
    created_at: datetime
    origin_terminal: Optional[Terminal] = None
    destination_terminal: Optional[Terminal] = None

    class Config:
        from_attributes = True


# Bus schemas
class BusBase(BaseModel):
    """Base bus schema."""
    license_plate: str = Field(..., min_length=1, max_length=20)
    model: Optional[str] = Field(None, max_length=100)
    capacity: int = Field(..., gt=0, le=100)
    amenities: Optional[dict] = None
    is_active: bool = True


class BusCreate(BusBase):
    """Schema for creating a bus."""
    pass


class BusUpdate(BaseModel):
    """Schema for updating a bus."""
    license_plate: Optional[str] = Field(None, min_length=1, max_length=20)
    model: Optional[str] = Field(None, max_length=100)
    capacity: Optional[int] = Field(None, gt=0, le=100)
    amenities: Optional[dict] = None
    is_active: Optional[bool] = None


class Bus(BusBase):
    """Schema for bus response."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# Trip schemas
class TripBase(BaseModel):
    """Base trip schema."""
    route_id: UUID
    bus_id: UUID
    driver_id: UUID
    departure_time: datetime
    arrival_time: Optional[datetime] = None
    status: TripStatus = TripStatus.SCHEDULED
    fare: Decimal = Field(..., gt=0)
    available_seats: Optional[int] = Field(None, ge=0)

    @validator('arrival_time')
    def validate_arrival_after_departure(cls, v, values):
        if v and 'departure_time' in values and v <= values['departure_time']:
            raise ValueError('Arrival time must be after departure time')
        return v


class TripCreate(TripBase):
    """Schema for creating a trip."""
    pass


class TripUpdate(BaseModel):
    """Schema for updating a trip."""
    route_id: Optional[UUID] = None
    bus_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    status: Optional[TripStatus] = None
    fare: Optional[Decimal] = Field(None, gt=0)
    available_seats: Optional[int] = Field(None, ge=0)

    @validator('arrival_time')
    def validate_arrival_after_departure(cls, v, values):
        if v and 'departure_time' in values and values['departure_time'] and v <= values['departure_time']:
            raise ValueError('Arrival time must be after departure time')
        return v


class Trip(TripBase):
    """Schema for trip response."""
    id: UUID
    created_at: datetime
    route: Optional[Route] = None
    bus: Optional[Bus] = None

    class Config:
        from_attributes = True


# List response schemas
class TerminalList(BaseModel):
    """Schema for terminal list response."""
    terminals: List[Terminal]
    total: int
    page: int
    size: int


class RouteList(BaseModel):
    """Schema for route list response."""
    routes: List[Route]
    total: int
    page: int
    size: int


class BusList(BaseModel):
    """Schema for bus list response."""
    buses: List[Bus]
    total: int
    page: int
    size: int


class TripList(BaseModel):
    """Schema for trip list response."""
    trips: List[Trip]
    total: int
    page: int
    size: int