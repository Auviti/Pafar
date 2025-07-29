"""
Google Maps API integration for route and location services.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Service for Google Maps API integration."""
    
    def __init__(self):
        """Initialize Google Maps client."""
        if not settings.GOOGLE_MAPS_API_KEY:
            raise ValueError("Google Maps API key is required")
        
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
        logger.info("Google Maps client initialized")
    
    def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Geocode an address to get coordinates and formatted address.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Dictionary with geocoding results or None if not found
        """
        try:
            results = self.client.geocode(address)
            if not results:
                logger.warning(f"No geocoding results found for address: {address}")
                return None
            
            result = results[0]
            location = result['geometry']['location']
            
            return {
                'formatted_address': result['formatted_address'],
                'latitude': location['lat'],
                'longitude': location['lng'],
                'place_id': result['place_id'],
                'address_components': result['address_components'],
                'geometry': result['geometry']
            }
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error geocoding address '{address}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error geocoding address '{address}': {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates to get address information.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with reverse geocoding results or None if not found
        """
        try:
            results = self.client.reverse_geocode((latitude, longitude))
            if not results:
                logger.warning(f"No reverse geocoding results found for coordinates: {latitude}, {longitude}")
                return None
            
            result = results[0]
            
            return {
                'formatted_address': result['formatted_address'],
                'place_id': result['place_id'],
                'address_components': result['address_components'],
                'geometry': result['geometry']
            }
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error reverse geocoding coordinates ({latitude}, {longitude}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reverse geocoding coordinates ({latitude}, {longitude}): {e}")
            return None
    
    def calculate_route(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None,
        departure_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate route between origin and destination with optional waypoints.
        
        Args:
            origin: Origin coordinates (latitude, longitude)
            destination: Destination coordinates (latitude, longitude)
            waypoints: Optional list of waypoint coordinates
            departure_time: Optional departure time for traffic-aware routing
            
        Returns:
            Dictionary with route information or None if route not found
        """
        try:
            # Prepare waypoints if provided
            waypoint_coords = None
            if waypoints:
                waypoint_coords = [f"{lat},{lng}" for lat, lng in waypoints]
            
            # Use departure time for traffic-aware routing
            departure_time_param = departure_time or datetime.now()
            
            results = self.client.directions(
                origin=f"{origin[0]},{origin[1]}",
                destination=f"{destination[0]},{destination[1]}",
                waypoints=waypoint_coords,
                departure_time=departure_time_param,
                traffic_model="best_guess",
                mode="driving"
            )
            
            if not results:
                logger.warning(f"No route found from {origin} to {destination}")
                return None
            
            route = results[0]
            leg = route['legs'][0]
            
            return {
                'distance': {
                    'text': leg['distance']['text'],
                    'value': leg['distance']['value']  # in meters
                },
                'duration': {
                    'text': leg['duration']['text'],
                    'value': leg['duration']['value']  # in seconds
                },
                'duration_in_traffic': leg.get('duration_in_traffic', leg['duration']),
                'start_address': leg['start_address'],
                'end_address': leg['end_address'],
                'start_location': leg['start_location'],
                'end_location': leg['end_location'],
                'polyline': route['overview_polyline']['points'],
                'bounds': route['bounds'],
                'steps': leg['steps']
            }
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error calculating route from {origin} to {destination}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calculating route from {origin} to {destination}: {e}")
            return None
    
    def search_places(
        self, 
        query: str, 
        location: Optional[Tuple[float, float]] = None,
        radius: int = 50000,  # 50km default
        place_type: str = "bus_station"
    ) -> List[Dict[str, Any]]:
        """
        Search for places using text search with optional location bias.
        
        Args:
            query: Search query string
            location: Optional location bias (latitude, longitude)
            radius: Search radius in meters
            place_type: Type of place to search for
            
        Returns:
            List of place results
        """
        try:
            search_params = {
                'query': query,
                'type': place_type
            }
            
            if location:
                search_params['location'] = f"{location[0]},{location[1]}"
                search_params['radius'] = radius
            
            results = self.client.places(**search_params)
            
            places = []
            for place in results.get('results', []):
                places.append({
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'formatted_address': place.get('formatted_address', ''),
                    'location': place['geometry']['location'],
                    'rating': place.get('rating'),
                    'types': place.get('types', []),
                    'business_status': place.get('business_status'),
                    'photos': place.get('photos', [])
                })
            
            return places
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error searching places for query '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching places for query '{query}': {e}")
            return []
    
    def get_place_autocomplete(
        self, 
        input_text: str,
        location: Optional[Tuple[float, float]] = None,
        radius: int = 50000,
        place_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get place autocomplete suggestions.
        
        Args:
            input_text: Input text for autocomplete
            location: Optional location bias (latitude, longitude)
            radius: Search radius in meters
            place_types: List of place types to filter by
            
        Returns:
            List of autocomplete suggestions
        """
        try:
            search_params = {
                'input_text': input_text,
                'session_token': None  # You might want to implement session tokens for billing optimization
            }
            
            if location:
                search_params['location'] = f"{location[0]},{location[1]}"
                search_params['radius'] = radius
            
            if place_types:
                search_params['types'] = place_types
            
            results = self.client.places_autocomplete(**search_params)
            
            suggestions = []
            for prediction in results:
                suggestions.append({
                    'place_id': prediction['place_id'],
                    'description': prediction['description'],
                    'structured_formatting': prediction.get('structured_formatting', {}),
                    'types': prediction.get('types', []),
                    'terms': prediction.get('terms', []),
                    'matched_substrings': prediction.get('matched_substrings', [])
                })
            
            return suggestions
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error getting autocomplete for '{input_text}': {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting autocomplete for '{input_text}': {e}")
            return []
    
    def calculate_eta(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        departure_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate ETA with traffic information.
        
        Args:
            origin: Origin coordinates (latitude, longitude)
            destination: Destination coordinates (latitude, longitude)
            departure_time: Optional departure time, defaults to now
            
        Returns:
            Dictionary with ETA information or None if calculation fails
        """
        try:
            departure_time = departure_time or datetime.now()
            
            # Use Distance Matrix API for more accurate ETA with traffic
            results = self.client.distance_matrix(
                origins=[f"{origin[0]},{origin[1]}"],
                destinations=[f"{destination[0]},{destination[1]}"],
                departure_time=departure_time,
                traffic_model="best_guess",
                mode="driving"
            )
            
            if not results['rows'] or not results['rows'][0]['elements']:
                logger.warning(f"No ETA calculation results for {origin} to {destination}")
                return None
            
            element = results['rows'][0]['elements'][0]
            
            if element['status'] != 'OK':
                logger.warning(f"ETA calculation failed: {element['status']}")
                return None
            
            duration_in_traffic = element.get('duration_in_traffic', element['duration'])
            
            # Calculate arrival time
            arrival_time = departure_time + timedelta(seconds=duration_in_traffic['value'])
            
            return {
                'distance': element['distance'],
                'duration': element['duration'],
                'duration_in_traffic': duration_in_traffic,
                'departure_time': departure_time.isoformat(),
                'arrival_time': arrival_time.isoformat(),
                'traffic_delay_seconds': duration_in_traffic['value'] - element['duration']['value']
            }
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error calculating ETA from {origin} to {destination}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calculating ETA from {origin} to {destination}: {e}")
            return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a place.
        
        Args:
            place_id: Google Places ID
            
        Returns:
            Dictionary with place details or None if not found
        """
        try:
            result = self.client.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'geometry', 'place_id',
                    'types', 'rating', 'formatted_phone_number', 'website',
                    'opening_hours', 'photos'
                ]
            )
            
            if not result or 'result' not in result:
                logger.warning(f"No place details found for place_id: {place_id}")
                return None
            
            place = result['result']
            
            return {
                'place_id': place['place_id'],
                'name': place.get('name'),
                'formatted_address': place.get('formatted_address'),
                'location': place['geometry']['location'],
                'types': place.get('types', []),
                'rating': place.get('rating'),
                'phone_number': place.get('formatted_phone_number'),
                'website': place.get('website'),
                'opening_hours': place.get('opening_hours'),
                'photos': place.get('photos', [])
            }
            
        except (ApiError, Timeout, TransportError) as e:
            logger.error(f"Error getting place details for place_id '{place_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting place details for place_id '{place_id}': {e}")
            return None


# Global instance - initialized lazily
maps_service = None

def get_maps_service():
    """Get or create the global maps service instance."""
    global maps_service
    if maps_service is None and settings.GOOGLE_MAPS_API_KEY:
        try:
            maps_service = GoogleMapsService()
        except ValueError:
            logger.warning("Failed to initialize Google Maps service - invalid API key")
            maps_service = None
    return maps_service