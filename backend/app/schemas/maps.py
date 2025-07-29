"""
Pydantic schemas for maps API endpoints.
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LocationPoint(BaseModel):
    """Location point with latitude and longitude."""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")


class AddressComponent(BaseModel):
    """Address component from Google Maps."""
    long_name: str
    short_name: str
    types: List[str]


class GeocodeResult(BaseModel):
    """Geocoding result from Google Maps."""
    formatted_address: str
    latitude: float
    longitude: float
    place_id: str
    address_components: List[AddressComponent]


class GeocodeResponse(BaseModel):
    """Response for terminal geocoding."""
    terminal_id: str
    geocode_result: GeocodeResult
    updated_coordinates: LocationPoint


class DistanceInfo(BaseModel):
    """Distance information."""
    text: str = Field(..., description="Human-readable distance")
    value: int = Field(..., description="Distance in meters")


class DurationInfo(BaseModel):
    """Duration information."""
    text: str = Field(..., description="Human-readable duration")
    value: int = Field(..., description="Duration in seconds")


class RouteCalculation(BaseModel):
    """Route calculation result."""
    distance: DistanceInfo
    duration: DurationInfo
    duration_in_traffic: DurationInfo
    start_address: str
    end_address: str
    start_location: LocationPoint
    end_location: LocationPoint
    polyline: str = Field(..., description="Encoded polyline")


class TerminalInfo(BaseModel):
    """Terminal information."""
    id: str
    name: str
    coordinates: LocationPoint


class RouteCalculationResponse(BaseModel):
    """Response for route calculation."""
    route_id: str
    origin_terminal: TerminalInfo
    destination_terminal: TerminalInfo
    route_calculation: RouteCalculation


class TerminalSearchResponse(BaseModel):
    """Response for terminal search."""
    place_id: str
    name: str
    formatted_address: str
    location: LocationPoint
    rating: Optional[float] = None
    types: List[str]
    business_status: Optional[str] = None


class StructuredFormatting(BaseModel):
    """Structured formatting for autocomplete."""
    main_text: str
    secondary_text: Optional[str] = None


class AutocompleteResponse(BaseModel):
    """Response for autocomplete suggestions."""
    place_id: str
    description: str
    structured_formatting: Optional[StructuredFormatting] = None
    types: List[str]


class ETAInfo(BaseModel):
    """ETA calculation information."""
    distance: DistanceInfo
    duration: DurationInfo
    duration_in_traffic: DurationInfo
    departure_time: str = Field(..., description="ISO format departure time")
    arrival_time: str = Field(..., description="ISO format arrival time")
    traffic_delay_seconds: int = Field(..., description="Traffic delay in seconds")


class ETAResponse(BaseModel):
    """Response for ETA calculation."""
    trip_id: str
    current_location: LocationPoint
    destination: TerminalInfo
    eta: ETAInfo


class PolylineResponse(BaseModel):
    """Response for route polyline."""
    route_id: str
    polyline: str = Field(..., description="Encoded polyline string")


# Request schemas for complex operations
class GeocodeRequest(BaseModel):
    """Request for geocoding an address."""
    address: str = Field(..., description="Address to geocode")


class RouteRequest(BaseModel):
    """Request for route calculation."""
    origin: LocationPoint
    destination: LocationPoint
    waypoints: Optional[List[LocationPoint]] = None
    departure_time: Optional[datetime] = None


class ETARequest(BaseModel):
    """Request for ETA calculation."""
    current_location: LocationPoint
    departure_time: Optional[datetime] = None