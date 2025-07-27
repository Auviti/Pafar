"""
Real-time tracking service for GPS location updates and trip status management.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from app.models.tracking import TripLocation
from app.models.fleet import Trip, TripStatus, Terminal
from app.models.booking import Booking
from app.core.redis import redis_client
import json
import math


class TrackingService:
    """Service for managing real-time trip tracking and location updates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def update_trip_location(
        self,
        trip_id: uuid.UUID,
        latitude: float,
        longitude: float,
        speed: Optional[float] = None,
        heading: Optional[float] = None
    ) -> TripLocation:
        """Update trip location with GPS coordinates."""
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180 degrees")
        
        # Validate speed and heading if provided
        if speed is not None and speed < 0:
            raise ValueError("Speed cannot be negative")
        if heading is not None and not (0 <= heading <= 360):
            raise ValueError("Heading must be between 0 and 360 degrees")
        
        # Check if trip exists and is active
        trip_query = select(Trip).where(Trip.id == trip_id)
        result = await self.db.execute(trip_query)
        trip = result.scalar_one_or_none()
        
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")
        
        if trip.status not in [TripStatus.BOARDING, TripStatus.IN_TRANSIT]:
            raise ValueError(f"Cannot update location for trip with status {trip.status}")
        
        # Create new location record
        location = TripLocation(
            trip_id=trip_id,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude)),
            speed=Decimal(str(speed)) if speed is not None else None,
            heading=Decimal(str(heading)) if heading is not None else None,
            recorded_at=datetime.utcnow()
        )
        
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        
        # Cache latest location in Redis for quick access
        location_data = {
            "trip_id": str(trip_id),
            "latitude": float(location.latitude),
            "longitude": float(location.longitude),
            "speed": float(location.speed) if location.speed else None,
            "heading": float(location.heading) if location.heading else None,
            "recorded_at": location.recorded_at.isoformat()
        }
        
        await redis_client.setex(
            f"trip_location:{trip_id}",
            300,  # 5 minutes TTL
            json.dumps(location_data)
        )
        
        # Check for geofencing (terminal arrival)
        await self._check_terminal_arrival(trip, latitude, longitude)
        
        return location
    
    async def get_trip_location(self, trip_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get latest location for a trip."""
        # Try Redis cache first
        cached_location = await redis_client.get(f"trip_location:{trip_id}")
        if cached_location:
            return json.loads(cached_location)
        
        # Fallback to database
        query = select(TripLocation).where(
            TripLocation.trip_id == trip_id
        ).order_by(desc(TripLocation.recorded_at)).limit(1)
        
        result = await self.db.execute(query)
        location = result.scalar_one_or_none()
        
        if location:
            return {
                "trip_id": str(location.trip_id),
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "speed": float(location.speed) if location.speed else None,
                "heading": float(location.heading) if location.heading else None,
                "recorded_at": location.recorded_at.isoformat()
            }
        
        return None
    
    async def get_trip_location_history(
        self,
        trip_id: uuid.UUID,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get location history for a trip."""
        query = select(TripLocation).where(
            TripLocation.trip_id == trip_id
        ).order_by(desc(TripLocation.recorded_at)).limit(limit)
        
        result = await self.db.execute(query)
        locations = result.scalars().all()
        
        return [
            {
                "trip_id": str(location.trip_id),
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "speed": float(location.speed) if location.speed else None,
                "heading": float(location.heading) if location.heading else None,
                "recorded_at": location.recorded_at.isoformat()
            }
            for location in locations
        ]
    
    async def update_trip_status(
        self,
        trip_id: uuid.UUID,
        status: TripStatus,
        driver_id: Optional[uuid.UUID] = None
    ) -> Trip:
        """Update trip status and notify passengers."""
        query = select(Trip).options(
            selectinload(Trip.bookings).selectinload(Booking.user)
        ).where(Trip.id == trip_id)
        
        result = await self.db.execute(query)
        trip = result.scalar_one_or_none()
        
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")
        
        # Validate driver authorization if provided
        if driver_id and trip.driver_id != driver_id:
            raise ValueError("Only the assigned driver can update trip status")
        
        # Update trip status
        old_status = trip.status
        trip.status = status
        
        # Set arrival time if trip is completed
        if status == TripStatus.COMPLETED and not trip.arrival_time:
            trip.arrival_time = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(trip)
        
        # Cache trip status update
        status_data = {
            "trip_id": str(trip_id),
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat(),
            "old_status": old_status.value
        }
        
        await redis_client.setex(
            f"trip_status:{trip_id}",
            3600,  # 1 hour TTL
            json.dumps(status_data)
        )
        
        return trip
    
    async def get_active_trips_for_driver(self, driver_id: uuid.UUID) -> List[Trip]:
        """Get active trips for a driver."""
        query = select(Trip).where(
            and_(
                Trip.driver_id == driver_id,
                Trip.status.in_([TripStatus.SCHEDULED, TripStatus.BOARDING, TripStatus.IN_TRANSIT])
            )
        ).order_by(Trip.departure_time)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_passengers_for_trip(self, trip_id: uuid.UUID) -> List[uuid.UUID]:
        """Get list of passenger user IDs for a trip."""
        query = select(Booking.user_id).where(
            and_(
                Booking.trip_id == trip_id,
                Booking.status.in_(["confirmed", "completed"])
            )
        )
        
        result = await self.db.execute(query)
        return [user_id for user_id in result.scalars().all()]
    
    async def _check_terminal_arrival(
        self,
        trip: Trip,
        latitude: float,
        longitude: float
    ) -> None:
        """Check if bus has arrived at destination terminal using geofencing."""
        # Load route with terminals
        await self.db.refresh(trip, ["route"])
        await self.db.refresh(trip.route, ["destination_terminal"])
        
        destination = trip.route.destination_terminal
        if not destination.latitude or not destination.longitude:
            return  # Cannot check without terminal coordinates
        
        # Calculate distance to destination terminal
        distance = self._calculate_distance(
            latitude, longitude,
            float(destination.latitude), float(destination.longitude)
        )
        
        # If within 100 meters of terminal and trip is in transit
        if distance <= 0.1 and trip.status == TripStatus.IN_TRANSIT:
            # Update trip status to arrived
            trip.status = TripStatus.ARRIVED
            await self.db.commit()
            
            # Cache arrival notification
            arrival_data = {
                "trip_id": str(trip.id),
                "terminal_name": destination.name,
                "arrived_at": datetime.utcnow().isoformat()
            }
            
            await redis_client.setex(
                f"trip_arrival:{trip.id}",
                1800,  # 30 minutes TTL
                json.dumps(arrival_data)
            )
    
    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates in kilometers using Haversine formula."""
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r