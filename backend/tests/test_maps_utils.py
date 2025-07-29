"""
Unit tests for Google Maps utility.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from googlemaps.exceptions import ApiError, Timeout, TransportError

from app.utils.maps import GoogleMapsService


class TestGoogleMapsService:
    """Test cases for GoogleMapsService."""
    
    @pytest.fixture
    def mock_googlemaps_client(self):
        """Mock Google Maps client."""
        with patch('app.utils.maps.googlemaps.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def maps_service(self, mock_googlemaps_client):
        """Create GoogleMapsService instance with mocked client."""
        with patch('app.utils.maps.settings') as mock_settings:
            mock_settings.GOOGLE_MAPS_API_KEY = "test_api_key"
            service = GoogleMapsService()
            service.client = mock_googlemaps_client
            return service
    
    @pytest.fixture
    def sample_geocode_response(self):
        """Sample geocoding response from Google Maps API."""
        return [
            {
                'formatted_address': '123 Main St, New York, NY 10001, USA',
                'geometry': {
                    'location': {
                        'lat': 40.7128,
                        'lng': -74.0060
                    }
                },
                'place_id': 'ChIJOwg_06VPwokRYv534QaPC8g',
                'address_components': [
                    {
                        'long_name': '123',
                        'short_name': '123',
                        'types': ['street_number']
                    }
                ]
            }
        ]
    
    @pytest.fixture
    def sample_directions_response(self):
        """Sample directions response from Google Maps API."""
        return [
            {
                'legs': [
                    {
                        'distance': {
                            'text': '10.5 km',
                            'value': 10500
                        },
                        'duration': {
                            'text': '25 mins',
                            'value': 1500
                        },
                        'duration_in_traffic': {
                            'text': '30 mins',
                            'value': 1800
                        },
                        'start_address': 'Origin Address',
                        'end_address': 'Destination Address',
                        'start_location': {'lat': 40.7128, 'lng': -74.0060},
                        'end_location': {'lat': 40.7589, 'lng': -73.9851},
                        'steps': []
                    }
                ],
                'overview_polyline': {
                    'points': 'encoded_polyline_string'
                },
                'bounds': {
                    'northeast': {'lat': 40.7589, 'lng': -73.9851},
                    'southwest': {'lat': 40.7128, 'lng': -74.0060}
                }
            }
        ]
    
    def test_init_with_api_key(self):
        """Test initialization with valid API key."""
        with patch('app.utils.maps.settings') as mock_settings:
            mock_settings.GOOGLE_MAPS_API_KEY = "test_api_key"
            with patch('app.utils.maps.googlemaps.Client') as mock_client:
                service = GoogleMapsService()
                mock_client.assert_called_once_with(key="test_api_key")
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch('app.utils.maps.settings') as mock_settings:
            mock_settings.GOOGLE_MAPS_API_KEY = None
            with pytest.raises(ValueError, match="Google Maps API key is required"):
                GoogleMapsService()
    
    def test_geocode_address_success(self, maps_service, sample_geocode_response):
        """Test successful address geocoding."""
        maps_service.client.geocode.return_value = sample_geocode_response
        
        result = maps_service.geocode_address("123 Main St, New York")
        
        assert result is not None
        assert result['formatted_address'] == '123 Main St, New York, NY 10001, USA'
        assert result['latitude'] == 40.7128
        assert result['longitude'] == -74.0060
        assert result['place_id'] == 'ChIJOwg_06VPwokRYv534QaPC8g'
        
        maps_service.client.geocode.assert_called_once_with("123 Main St, New York")
    
    def test_geocode_address_no_results(self, maps_service):
        """Test geocoding with no results."""
        maps_service.client.geocode.return_value = []
        
        result = maps_service.geocode_address("Nonexistent Address")
        
        assert result is None
    
    def test_geocode_address_api_error(self, maps_service):
        """Test geocoding with API error."""
        maps_service.client.geocode.side_effect = ApiError("API Error")
        
        result = maps_service.geocode_address("123 Main St")
        
        assert result is None
    
    def test_geocode_address_timeout(self, maps_service):
        """Test geocoding with timeout error."""
        maps_service.client.geocode.side_effect = Timeout("Timeout")
        
        result = maps_service.geocode_address("123 Main St")
        
        assert result is None
    
    def test_reverse_geocode_success(self, maps_service):
        """Test successful reverse geocoding."""
        reverse_response = [
            {
                'formatted_address': '123 Main St, New York, NY 10001, USA',
                'place_id': 'ChIJOwg_06VPwokRYv534QaPC8g',
                'address_components': [],
                'geometry': {}
            }
        ]
        maps_service.client.reverse_geocode.return_value = reverse_response
        
        result = maps_service.reverse_geocode(40.7128, -74.0060)
        
        assert result is not None
        assert result['formatted_address'] == '123 Main St, New York, NY 10001, USA'
        assert result['place_id'] == 'ChIJOwg_06VPwokRYv534QaPC8g'
        
        maps_service.client.reverse_geocode.assert_called_once_with((40.7128, -74.0060))
    
    def test_calculate_route_success(self, maps_service, sample_directions_response):
        """Test successful route calculation."""
        maps_service.client.directions.return_value = sample_directions_response
        
        origin = (40.7128, -74.0060)
        destination = (40.7589, -73.9851)
        
        result = maps_service.calculate_route(origin, destination)
        
        assert result is not None
        assert result['distance']['text'] == '10.5 km'
        assert result['distance']['value'] == 10500
        assert result['duration']['text'] == '25 mins'
        assert result['duration']['value'] == 1500
        assert result['polyline'] == 'encoded_polyline_string'
        
        maps_service.client.directions.assert_called_once()
        call_args = maps_service.client.directions.call_args
        assert call_args[1]['origin'] == "40.7128,-74.006"
        assert call_args[1]['destination'] == "40.7589,-73.9851"
        assert call_args[1]['mode'] == "driving"
    
    def test_calculate_route_with_waypoints(self, maps_service, sample_directions_response):
        """Test route calculation with waypoints."""
        maps_service.client.directions.return_value = sample_directions_response
        
        origin = (40.7128, -74.0060)
        destination = (40.7589, -73.9851)
        waypoints = [(40.7500, -74.0000)]
        
        result = maps_service.calculate_route(
            origin, destination, waypoints=waypoints
        )
        
        assert result is not None
        
        call_args = maps_service.client.directions.call_args
        assert call_args[1]['waypoints'] == ["40.75,-74.0"]
    
    def test_calculate_route_no_results(self, maps_service):
        """Test route calculation with no results."""
        maps_service.client.directions.return_value = []
        
        result = maps_service.calculate_route((0, 0), (1, 1))
        
        assert result is None
    
    def test_search_places_success(self, maps_service):
        """Test successful place search."""
        places_response = {
            'results': [
                {
                    'place_id': 'place1',
                    'name': 'Central Station',
                    'formatted_address': '123 Main St',
                    'geometry': {
                        'location': {'lat': 40.7128, 'lng': -74.0060}
                    },
                    'rating': 4.5,
                    'types': ['bus_station'],
                    'business_status': 'OPERATIONAL',
                    'photos': []
                }
            ]
        }
        maps_service.client.places.return_value = places_response
        
        results = maps_service.search_places(
            query="Central Station",
            location=(40.7128, -74.0060),
            radius=10000
        )
        
        assert len(results) == 1
        assert results[0]['name'] == 'Central Station'
        assert results[0]['place_id'] == 'place1'
        assert results[0]['rating'] == 4.5
        
        maps_service.client.places.assert_called_once()
        call_args = maps_service.client.places.call_args[1]
        assert call_args['query'] == "Central Station"
        assert call_args['location'] == "40.7128,-74.006"
        assert call_args['radius'] == 10000
    
    def test_get_place_autocomplete_success(self, maps_service):
        """Test successful place autocomplete."""
        autocomplete_response = [
            {
                'place_id': 'place1',
                'description': 'Central Bus Station, New York',
                'structured_formatting': {
                    'main_text': 'Central Bus Station',
                    'secondary_text': 'New York'
                },
                'types': ['bus_station'],
                'terms': [],
                'matched_substrings': []
            }
        ]
        maps_service.client.places_autocomplete.return_value = autocomplete_response
        
        results = maps_service.get_place_autocomplete(
            input_text="Central",
            location=(40.7128, -74.0060)
        )
        
        assert len(results) == 1
        assert results[0]['description'] == 'Central Bus Station, New York'
        assert results[0]['place_id'] == 'place1'
        
        maps_service.client.places_autocomplete.assert_called_once()
    
    def test_calculate_eta_success(self, maps_service):
        """Test successful ETA calculation."""
        eta_response = {
            'rows': [
                {
                    'elements': [
                        {
                            'status': 'OK',
                            'distance': {
                                'text': '5.2 km',
                                'value': 5200
                            },
                            'duration': {
                                'text': '12 mins',
                                'value': 720
                            },
                            'duration_in_traffic': {
                                'text': '15 mins',
                                'value': 900
                            }
                        }
                    ]
                }
            ]
        }
        maps_service.client.distance_matrix.return_value = eta_response
        
        origin = (40.7128, -74.0060)
        destination = (40.7589, -73.9851)
        departure_time = datetime(2024, 1, 1, 10, 0, 0)
        
        result = maps_service.calculate_eta(
            origin, destination, departure_time
        )
        
        assert result is not None
        assert result['distance']['text'] == '5.2 km'
        assert result['duration_in_traffic']['value'] == 900
        assert result['traffic_delay_seconds'] == 180  # 900 - 720
        assert 'departure_time' in result
        assert 'arrival_time' in result
        
        maps_service.client.distance_matrix.assert_called_once()
    
    def test_calculate_eta_element_not_ok(self, maps_service):
        """Test ETA calculation with non-OK status."""
        eta_response = {
            'rows': [
                {
                    'elements': [
                        {
                            'status': 'NOT_FOUND'
                        }
                    ]
                }
            ]
        }
        maps_service.client.distance_matrix.return_value = eta_response
        
        result = maps_service.calculate_eta((0, 0), (1, 1))
        
        assert result is None
    
    def test_get_place_details_success(self, maps_service):
        """Test successful place details retrieval."""
        place_details_response = {
            'result': {
                'place_id': 'place1',
                'name': 'Central Station',
                'formatted_address': '123 Main St',
                'geometry': {
                    'location': {'lat': 40.7128, 'lng': -74.0060}
                },
                'types': ['bus_station'],
                'rating': 4.5,
                'formatted_phone_number': '+1 555-123-4567',
                'website': 'https://example.com',
                'opening_hours': {},
                'photos': []
            }
        }
        maps_service.client.place.return_value = place_details_response
        
        result = maps_service.get_place_details('place1')
        
        assert result is not None
        assert result['name'] == 'Central Station'
        assert result['place_id'] == 'place1'
        assert result['rating'] == 4.5
        assert result['phone_number'] == '+1 555-123-4567'
        
        maps_service.client.place.assert_called_once_with(
            place_id='place1',
            fields=[
                'name', 'formatted_address', 'geometry', 'place_id',
                'types', 'rating', 'formatted_phone_number', 'website',
                'opening_hours', 'photos'
            ]
        )
    
    def test_get_place_details_no_result(self, maps_service):
        """Test place details with no result."""
        maps_service.client.place.return_value = {}
        
        result = maps_service.get_place_details('nonexistent')
        
        assert result is None
    
    def test_error_handling_transport_error(self, maps_service):
        """Test handling of transport errors."""
        maps_service.client.geocode.side_effect = TransportError("Network error")
        
        result = maps_service.geocode_address("123 Main St")
        
        assert result is None
    
    def test_error_handling_unexpected_error(self, maps_service):
        """Test handling of unexpected errors."""
        maps_service.client.geocode.side_effect = Exception("Unexpected error")
        
        result = maps_service.geocode_address("123 Main St")
        
        assert result is None