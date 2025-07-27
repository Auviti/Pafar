"""
API endpoints for real-time trip tracking and location management.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.tracking_service import TrackingService
from app.models.fleet import TripStatus
from app.models.user import User
from datetime import datetime

router = APIRouter()


# Pydantic schemas
class LocationUpdateRequest(BaseModel):
    """Request schema for location updates."""
    trip_id: uuid.UUID
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    heading: Optional[float] = Field(None, ge=0, le=360, description="Heading in degrees")


class LocationResponse(BaseModel):
    """Response schema for location data."""
    trip_id: uuid.UUID
    latitude: float
    longitude: float
    speed: Optional[float]
    heading: Optional[float]
    recorded_at: datetime


class TripStatusUpdateRequest(BaseModel):
    """Request schema for trip status updates."""
    trip_id: uuid.UUID
    status: TripStatus


class TripStatusResponse(BaseModel):
    """Response schema for trip status."""
    trip_id: uuid.UUID
    status: TripStatus
    updated_at: datetime


class TripTrackingResponse(BaseModel):
    """Response schema for trip tracking information."""
    trip_id: uuid.UUID
    current_location: Optional[LocationResponse]
    status: TripStatus
    passenger_count: int
    last_updated: Optional[datetime]


@router.post("/location", response_model=LocationResponse)
async def update_trip_location(
    location_data: LocationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update trip location (Driver only).
    
    Allows drivers to update the real-time location of their assigned trip.
    """
    if current_user.role != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can update trip locations"
        )
    
    tracking_service = TrackingService(db)
    
    try:
        location = await tracking_service.update_trip_location(
            trip_id=location_data.trip_id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            speed=location_data.speed,
            heading=location_data.heading
        )
        
        return LocationResponse(
            trip_id=location.trip_id,
            latitude=float(location.latitude),
            longitude=float(location.longitude),
            speed=float(location.speed) if location.speed else None,
            heading=float(location.heading) if location.heading else None,
            recorded_at=location.recorded_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location"
        )


@router.get("/trip/{trip_id}/location", response_model=Optional[LocationResponse])
async def get_trip_location(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current location of a trip.
    
    Returns the latest GPS coordinates for the specified trip.
    """
    tracking_service = TrackingService(db)
    
    try:
        location_data = await tracking_service.get_trip_location(trip_id)
        
        if not location_data:
            return None
        
        return LocationResponse(
            trip_id=uuid.UUID(location_data["trip_id"]),
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
            speed=location_data["speed"],
            heading=location_data["heading"],
            recorded_at=datetime.fromisoformat(location_data["recorded_at"])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve location"
        )


@router.get("/trip/{trip_id}/location/history", response_model=List[LocationResponse])
async def get_trip_location_history(
    trip_id: uuid.UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get location history for a trip.
    
    Returns historical GPS coordinates for the specified trip.
    """
    if limit > 1000:
        limit = 1000  # Prevent excessive data requests
    
    tracking_service = TrackingService(db)
    
    try:
        locations = await tracking_service.get_trip_location_history(trip_id, limit)
        
        return [
            LocationResponse(
                trip_id=uuid.UUID(loc["trip_id"]),
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                speed=loc["speed"],
                heading=loc["heading"],
                recorded_at=datetime.fromisoformat(loc["recorded_at"])
            )
            for loc in locations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve location history"
        )


@router.post("/trip/status", response_model=TripStatusResponse)
async def update_trip_status(
    status_data: TripStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update trip status (Driver only).
    
    Allows drivers to update the status of their assigned trip.
    """
    if current_user.role != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can update trip status"
        )
    
    tracking_service = TrackingService(db)
    
    try:
        trip = await tracking_service.update_trip_status(
            trip_id=status_data.trip_id,
            status=status_data.status,
            driver_id=current_user.id
        )
        
        return TripStatusResponse(
            trip_id=trip.id,
            status=trip.status,
            updated_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update trip status"
        )


@router.get("/trip/{trip_id}/tracking", response_model=TripTrackingResponse)
async def get_trip_tracking_info(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive tracking information for a trip.
    
    Returns current location, status, and passenger count.
    """
    tracking_service = TrackingService(db)
    
    try:
        # Get current location
        location_data = await tracking_service.get_trip_location(trip_id)
        current_location = None
        
        if location_data:
            current_location = LocationResponse(
                trip_id=uuid.UUID(location_data["trip_id"]),
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                speed=location_data["speed"],
                heading=location_data["heading"],
                recorded_at=datetime.fromisoformat(location_data["recorded_at"])
            )
        
        # Get passenger count
        passengers = await tracking_service.get_passengers_for_trip(trip_id)
        passenger_count = len(passengers)
        
        # Get trip status from database
        from sqlalchemy import select
        from app.models.fleet import Trip
        
        query = select(Trip).where(Trip.id == trip_id)
        result = await db.execute(query)
        trip = result.scalar_one_or_none()
        
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trip not found"
            )
        
        return TripTrackingResponse(
            trip_id=trip.id,
            current_location=current_location,
            status=trip.status,
            passenger_count=passenger_count,
            last_updated=current_location.recorded_at if current_location else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tracking information"
        )


@router.get("/driver/trips/active", response_model=List[dict])
async def get_driver_active_trips(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active trips for the current driver.
    
    Returns all trips that are scheduled, boarding, or in transit.
    """
    if current_user.role != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can access this endpoint"
        )
    
    tracking_service = TrackingService(db)
    
    try:
        trips = await tracking_service.get_active_trips_for_driver(current_user.id)
        
        return [
            {
                "trip_id": str(trip.id),
                "route_id": str(trip.route_id),
                "bus_id": str(trip.bus_id),
                "departure_time": trip.departure_time.isoformat(),
                "arrival_time": trip.arrival_time.isoformat() if trip.arrival_time else None,
                "status": trip.status.value,
                "fare": float(trip.fare),
                "available_seats": trip.available_seats
            }
            for trip in trips
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active trips"
        )


@router.get("/trip/{trip_id}/passengers", response_model=List[uuid.UUID])
async def get_trip_passengers(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get passenger list for a trip (Driver and Admin only).
    
    Returns list of user IDs for passengers on the specified trip.
    """
    if current_user.role not in ["driver", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers and admins can access passenger information"
        )
    
    tracking_service = TrackingService(db)
    
    try:
        passengers = await tracking_service.get_passengers_for_trip(trip_id)
        return passengers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve passenger list"
        )