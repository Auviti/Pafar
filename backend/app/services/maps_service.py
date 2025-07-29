"""
Maps service for handling location and route operations.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.fleet import Terminal, Route
from app.utils.maps import get_maps_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class MapsService:
    """Service for maps-related operations."""
    
    def __init__(self):
        """Initialize maps service."""
        pass
    
    def _get_maps_service(self):
        """Get the maps service instance."""
        maps_service = get_maps_service()
        if not maps_service:
            logger.warning("Google Maps service not available - API key not configured")
        return maps_service
    
    async def geocode_terminal(self, db: AsyncSession, terminal_id: str) -> Optional[Dict[str, Any]]:
        """
        Geocode a terminal's address and update its coordinates.
        
        Args:
            db: Database session
            terminal_id: Terminal ID to geocode
            
        Returns:
            Geocoding result or None if failed
        """
        maps_service = self._get_maps_service()
        if not maps_service:
            logger.error("Google Maps service not available")
            return None
        
        try:
            # Get terminal from database
            result = await db.execute(
                select(Terminal).where(Terminal.id == terminal_id)
            )
            terminal = result.scalar_one_or_none()
            
            if not terminal:
                logger.error(f"Terminal not found: {terminal_id}")
                return None
            
            # Create address string for geocoding
            address_parts = [terminal.name]
            if terminal.address:
                address_parts.append(terminal.address)
            if terminal.city:
                address_parts.append(terminal.city)
            
            address = ", ".join(address_parts)
            
            # Geocode the address
            geocode_result = maps_service.geocode_address(address)
            
            if geocode_result:
                # Update terminal coordinates
                terminal.latitude = geocode_result['latitude']
                terminal.longitude = geocode_result['longitude']
                
                await db.commit()
                await db.refresh(terminal)
                
                logger.info(f"Updated coordinates for terminal {terminal_id}")
                
                return {
                    'terminal_id': terminal_id,
                    'geocode_result': geocode_result,
                    'updated_coordinates': {
                        'latitude': terminal.latitude,
                        'longitude': terminal.longitude
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding terminal {terminal_id}: {e}")
            await db.rollback()
            return None
    
    async def calculate_route_distance(
        self, 
        db: AsyncSession, 
        route_id: str,
        update_route: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate distance and duration for a route.
        
        Args:
            db: Database session
            route_id: Route ID to calculate
            update_route: Whether to update the route in database
            
        Returns:
            Route calculation result or None if failed
        """
        maps_service = self._get_maps_service()
        if not maps_service:
            logger.error("Google Maps service not available")
            return None
        
        try:
            # Get route with terminals
            result = await db.execute(
                select(Route)
                .join(Terminal, Route.origin_terminal_id == Terminal.id)
                .join(Terminal, Route.destination_terminal_id == Terminal.id)
                .where(Route.id == route_id)
            )
            route = result.scalar_one_or_none()
            
            if not route:
                logger.error(f"Route not found: {route_id}")
                return None
            
            # Get origin and destination terminals
            origin_result = await db.execute(
                select(Terminal).where(Terminal.id == route.origin_terminal_id)
            )
            origin_terminal = origin_result.scalar_one_or_none()
            
            destination_result = await db.execute(
                select(Terminal).where(Terminal.id == route.destination_terminal_id)
            )
            destination_terminal = destination_result.scalar_one_or_none()
            
            if not origin_terminal or not destination_terminal:
                logger.error(f"Terminals not found for route {route_id}")
                return None
            
            # Check if terminals have coordinates
            if (not origin_terminal.latitude or not origin_terminal.longitude or
                not destination_terminal.latitude or not destination_terminal.longitude):
                logger.error(f"Terminal coordinates missing for route {route_id}")
                return None
            
            # Calculate route
            origin_coords = (origin_terminal.latitude, origin_terminal.longitude)
            destination_coords = (destination_terminal.latitude, destination_terminal.longitude)
            
            route_result = maps_service.calculate_route(
                origin=origin_coords,
                destination=destination_coords
            )
            
            if route_result and update_route:
                # Update route with calculated values
                route.distance_km = route_result['distance']['value'] / 1000  # Convert to km
                route.estimated_duration_minutes = route_result['duration']['value'] / 60  # Convert to minutes
                
                await db.commit()
                await db.refresh(route)
                
                logger.info(f"Updated route {route_id} with calculated distance and duration")
            
            return {
                'route_id': route_id,
                'origin_terminal': {
                    'id': str(origin_terminal.id),
                    'name': origin_terminal.name,
                    'coordinates': origin_coords
                },
                'destination_terminal': {
                    'id': str(destination_terminal.id),
                    'name': destination_terminal.name,
                    'coordinates': destination_coords
                },
                'route_calculation': route_result
            }
            
        except Exception as e:
            logger.error(f"Error calculating route distance for {route_id}: {e}")
            await db.rollback()
            return None
    
    async def search_terminals(
        self, 
        query: str,
        location: Optional[Tuple[float, float]] = None,
        radius: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Search for terminals using Google Places API.
        
        Args:
            query: Search query
            location: Optional location bias
            radius: Search radius in meters
            
        Returns:
            List of terminal search results
        """
        maps_service = self._get_maps_service()
        if not maps_service:
            logger.error("Google Maps service not available")
            return []
        
        try:
            # Search for bus stations and transport hubs
            places = maps_service.search_places(
                query=query,
                location=location,
                radius=radius,
                place_type="bus_station"
            )
            
            # Also search for general transit stations
            transit_places = maps_service.search_places(
                query=query,
                location=location,
                radius=radius,
                place_type="transit_station"
            )
            
            # Combine and deduplicate results
            all_places = places + transit_places
            unique_places = {}
            
            for place in all_places:
                place_id = place['place_id']
                if place_id not in unique_places:
                    unique_places[place_id] = place
            
            return list(unique_places.values())
            
        except Exception as e:
            logger.error(f"Error searching terminals for query '{query}': {e}")
            return []
    
    async def get_terminal_autocomplete(
        self, 
        input_text: str,
        location: Optional[Tuple[float, float]] = None,
        radius: int = 50000
    ) -> List[Dict[str, Any]]:
        """
        Get autocomplete suggestions for terminal search.
        
        Args:
            input_text: Input text for autocomplete
            location: Optional location bias
            radius: Search radius in meters
            
        Returns:
            List of autocomplete suggestions
        """
        maps_service = self._get_maps_service()
        if not maps_service:
            logger.error("Google Maps service not available")
            return []
        
        try:
            suggestions = maps_service.get_place_autocomplete(
                input_text=input_text,
                location=location,
                radius=radius,
                place_types=["bus_station", "transit_station", "establishment"]
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting autocomplete for '{input_text}': {e}")
            return []
    
    async def calculate_trip_eta(
        self,
        db: AsyncSession,
        trip_id: str,
        current_location: Tuple[float, float],
        departure_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate ETA for a trip based on current location.
        
        Args:
            db: Database session
            trip_id: Trip ID
            current_location: Current bus location (latitude, longitude)
            departure_time: Optional departure time
            
        Returns:
            ETA calculation result or None if failed
        """
        maps_service = self._get_maps_service()
        if not maps_service:
            logger.error("Google Maps service not available")
            return None
        
        try:
            # Get trip with route and destination terminal
            from app.models.fleet import Trip
            
            result = await db.execute(
                select(Trip)
                .join(Route, Trip.route_id == Route.id)
                .join(Terminal, Route.destination_terminal_id == Terminal.id)
                .where(Trip.id == trip_id)
            )
            trip = result.scalar_one_or_none()
            
            if not trip:
                logger.error(f"Trip not found: {trip_id}")
                return None
            
            # Get destination terminal
            destination_result = await db.execute(
                select(Terminal).where(Terminal.id == trip.route.destination_terminal_id)
            )
            destination_terminal = destination_result.scalar_one_or_none()
            
            if not destination_terminal or not destination_terminal.latitude or not destination_terminal.longitude:
                logger.error(f"Destination terminal coordinates missing for trip {trip_id}")
                return None
            
            destination_coords = (destination_terminal.latitude, destination_terminal.longitude)
            
            # Calculate ETA
            eta_result = maps_service.calculate_eta(
                origin=current_location,
                destination=destination_coords,
                departure_time=departure_time
            )
            
            if eta_result:
                return {
                    'trip_id': trip_id,
                    'current_location': current_location,
                    'destination': {
                        'terminal_id': str(destination_terminal.id),
                        'name': destination_terminal.name,
                        'coordinates': destination_coords
                    },
                    'eta': eta_result
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating ETA for trip {trip_id}: {e}")
            return None
    
    async def get_route_polyline(
        self,
        db: AsyncSession,
        route_id: str
    ) -> Optional[str]:
        """
        Get encoded polyline for a route.
        
        Args:
            db: Database session
            route_id: Route ID
            
        Returns:
            Encoded polyline string or None if failed
        """
        maps_service = self._get_maps_service()
        if not maps_service:
            logger.error("Google Maps service not available")
            return None
        
        try:
            route_calculation = await self.calculate_route_distance(
                db=db,
                route_id=route_id,
                update_route=False
            )
            
            if route_calculation and route_calculation.get('route_calculation'):
                return route_calculation['route_calculation'].get('polyline')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting polyline for route {route_id}: {e}")
            return None


# Global instance
maps_service_instance = MapsService()