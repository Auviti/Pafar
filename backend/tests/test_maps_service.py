"""
Unit tests for maps service.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from app.services.maps_service import MapsService
from app.models.fleet import Terminal, Route
from app.models.fleet import Trip


class TestMapsService:
    """Test cases for MapsService."""
    
    @pytest.fixture
    def maps_service(self):
        """Create maps service instance."""
        return MapsService()
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def sample_terminal(self):
        """Sample terminal for testing."""
        terminal = Mock(spec=Terminal)
        terminal.id = "terminal-123"
        terminal.name = "Central Bus Station"
        terminal.address = "123 Main St"
        terminal.city = "New York"
        terminal.latitude = None
        terminal.longitude = None
        return terminal
    
    @pytest.fixture
    def sample_route(self):
        """Sample route for testing."""
        route = Mock(spec=Route)
        route.id = "route-123"
        route.origin_terminal_id = "terminal-origin"
        route.destination_terminal_id = "terminal-dest"
        route.distance_km = None
        route.estimated_duration_minutes = None
        return route
    
    @pytest.fixture
    def sample_trip(self):
        """Sample trip for testing."""
        trip = Mock(spec=Trip)
        trip.id = "trip-123"
        trip.route_id = "route-123"
        trip.route = Mock()
        trip.route.destination_terminal_id = "terminal-dest"
        return trip
    
    @pytest.fixture
    def mock_geocode_result(self):
        """Mock geocoding result."""
        return {
            'formatted_address': '123 Main St, New York, NY 10001, USA',
            'latitude': 40.7128,
            'longitude': -74.0060,
            'place_id': 'ChIJOwg_06VPwokRYv534QaPC8g',
            'address_components': [],
            'geometry': {}
        }
    
    @pytest.fixture
    def mock_route_result(self):
        """Mock route calculation result."""
        return {
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
            'start_address': 'Origin Terminal',
            'end_address': 'Destination Terminal',
            'start_location': {'lat': 40.7128, 'lng': -74.0060},
            'end_location': {'lat': 40.7589, 'lng': -73.9851},
            'polyline': 'encoded_polyline_string',
            'bounds': {},
            'steps': []
        }
    
    @pytest.mark.asyncio
    async def test_geocode_terminal_success(
        self, 
        maps_service, 
        mock_db, 
        sample_terminal, 
        mock_geocode_result
    ):
        """Test successful terminal geocoding."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_terminal
        mock_db.execute.return_value = mock_result
        
        # Mock maps service
        mock_maps = Mock()
        mock_maps.geocode_address.return_value = mock_geocode_result
        with patch.object(maps_service, '_get_maps_service', return_value=mock_maps):
            
            result = await maps_service.geocode_terminal(mock_db, "terminal-123")
            
            assert result is not None
            assert result['terminal_id'] == "terminal-123"
            assert result['geocode_result'] == mock_geocode_result
            assert result['updated_coordinates']['latitude'] == 40.7128
            assert result['updated_coordinates']['longitude'] == -74.0060
            
            # Verify terminal was updated
            assert sample_terminal.latitude == 40.7128
            assert sample_terminal.longitude == -74.0060
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_geocode_terminal_not_found(self, maps_service, mock_db):
        """Test geocoding when terminal not found."""
        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await maps_service.geocode_terminal(mock_db, "nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_geocode_terminal_maps_service_unavailable(self, maps_service, mock_db, sample_terminal):
        """Test geocoding when maps service is unavailable."""
        with patch.object(maps_service, '_get_maps_service', return_value=None):
            result = await maps_service.geocode_terminal(mock_db, "terminal-123")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_calculate_route_distance_success(
        self, 
        maps_service, 
        mock_db, 
        sample_route, 
        mock_route_result
    ):
        """Test successful route distance calculation."""
        # Mock route query
        mock_route_result_db = Mock()
        mock_route_result_db.scalar_one_or_none.return_value = sample_route
        
        # Mock terminal queries
        origin_terminal = Mock(spec=Terminal)
        origin_terminal.id = "terminal-origin"
        origin_terminal.name = "Origin Terminal"
        origin_terminal.latitude = 40.7128
        origin_terminal.longitude = -74.0060
        
        dest_terminal = Mock(spec=Terminal)
        dest_terminal.id = "terminal-dest"
        dest_terminal.name = "Destination Terminal"
        dest_terminal.latitude = 40.7589
        dest_terminal.longitude = -73.9851
        
        mock_origin_result = Mock()
        mock_origin_result.scalar_one_or_none.return_value = origin_terminal
        
        mock_dest_result = Mock()
        mock_dest_result.scalar_one_or_none.return_value = dest_terminal
        
        mock_db.execute.side_effect = [
            mock_route_result_db,
            mock_origin_result,
            mock_dest_result
        ]
        
        # Mock maps service
        mock_maps = Mock()
        mock_maps.calculate_route.return_value = mock_route_result
        with patch.object(maps_service, '_get_maps_service', return_value=mock_maps):
            
            result = await maps_service.calculate_route_distance(
                mock_db, "route-123", update_route=True
            )
            
            assert result is not None
            assert result['route_id'] == "route-123"
            assert result['origin_terminal']['name'] == "Origin Terminal"
            assert result['destination_terminal']['name'] == "Destination Terminal"
            assert result['route_calculation'] == mock_route_result
            
            # Verify route was updated
            assert sample_route.distance_km == 10.5  # 10500 meters / 1000
            assert sample_route.estimated_duration_minutes == 25  # 1500 seconds / 60
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_route_distance_missing_coordinates(
        self, 
        maps_service, 
        mock_db, 
        sample_route
    ):
        """Test route calculation with missing terminal coordinates."""
        # Mock route query
        mock_route_result_db = Mock()
        mock_route_result_db.scalar_one_or_none.return_value = sample_route
        
        # Mock terminal with missing coordinates
        origin_terminal = Mock(spec=Terminal)
        origin_terminal.latitude = None
        origin_terminal.longitude = None
        
        dest_terminal = Mock(spec=Terminal)
        dest_terminal.latitude = 40.7589
        dest_terminal.longitude = -73.9851
        
        mock_origin_result = Mock()
        mock_origin_result.scalar_one_or_none.return_value = origin_terminal
        
        mock_dest_result = Mock()
        mock_dest_result.scalar_one_or_none.return_value = dest_terminal
        
        mock_db.execute.side_effect = [
            mock_route_result_db,
            mock_origin_result,
            mock_dest_result
        ]
        
        result = await maps_service.calculate_route_distance(mock_db, "route-123")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_search_terminals(self, maps_service):
        """Test terminal search functionality."""
        mock_places = [
            {
                'place_id': 'place1',
                'name': 'Central Station',
                'formatted_address': '123 Main St',
                'location': {'lat': 40.7128, 'lng': -74.0060},
                'rating': 4.5,
                'types': ['bus_station'],
                'business_status': 'OPERATIONAL',
                'photos': []
            }
        ]
        
        mock_maps = Mock()
        mock_maps.search_places.return_value = mock_places
        with patch.object(maps_service, '_get_maps_service', return_value=mock_maps):
            
            results = await maps_service.search_terminals(
                query="Central Station",
                location=(40.7128, -74.0060),
                radius=10000
            )
            
            assert len(results) == 1
            assert results[0]['name'] == 'Central Station'
            assert results[0]['place_id'] == 'place1'
    
    @pytest.mark.asyncio
    async def test_get_terminal_autocomplete(self, maps_service):
        """Test terminal autocomplete functionality."""
        mock_suggestions = [
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
        
        mock_maps = Mock()
        mock_maps.get_place_autocomplete.return_value = mock_suggestions
        with patch.object(maps_service, '_get_maps_service', return_value=mock_maps):
            
            results = await maps_service.get_terminal_autocomplete(
                input_text="Central",
                location=(40.7128, -74.0060)
            )
            
            assert len(results) == 1
            assert results[0]['description'] == 'Central Bus Station, New York'
    
    @pytest.mark.asyncio
    async def test_calculate_trip_eta_success(self, maps_service, mock_db, sample_trip):
        """Test successful ETA calculation for a trip."""
        # Mock trip query
        mock_trip_result = Mock()
        mock_trip_result.scalar_one_or_none.return_value = sample_trip
        
        # Mock destination terminal
        dest_terminal = Mock(spec=Terminal)
        dest_terminal.id = "terminal-dest"
        dest_terminal.name = "Destination Terminal"
        dest_terminal.latitude = 40.7589
        dest_terminal.longitude = -73.9851
        
        mock_dest_result = Mock()
        mock_dest_result.scalar_one_or_none.return_value = dest_terminal
        
        mock_db.execute.side_effect = [mock_trip_result, mock_dest_result]
        
        mock_eta_result = {
            'distance': {'text': '5.2 km', 'value': 5200},
            'duration': {'text': '12 mins', 'value': 720},
            'duration_in_traffic': {'text': '15 mins', 'value': 900},
            'departure_time': '2024-01-01T10:00:00',
            'arrival_time': '2024-01-01T10:15:00',
            'traffic_delay_seconds': 180
        }
        
        mock_maps = Mock()
        mock_maps.calculate_eta.return_value = mock_eta_result
        with patch.object(maps_service, '_get_maps_service', return_value=mock_maps):
            
            result = await maps_service.calculate_trip_eta(
                db=mock_db,
                trip_id="trip-123",
                current_location=(40.7128, -74.0060)
            )
            
            assert result is not None
            assert result['trip_id'] == "trip-123"
            assert result['current_location'] == (40.7128, -74.0060)
            assert result['destination']['name'] == "Destination Terminal"
            assert result['eta'] == mock_eta_result
    
    @pytest.mark.asyncio
    async def test_get_route_polyline(self, maps_service, mock_db):
        """Test getting route polyline."""
        # Mock the maps service to be available
        with patch.object(maps_service, '_get_maps_service', return_value=Mock()):
            with patch.object(
                maps_service, 
                'calculate_route_distance'
            ) as mock_calculate:
                mock_calculate.return_value = {
                    'route_calculation': {
                        'polyline': 'encoded_polyline_string'
                    }
                }
                
                result = await maps_service.get_route_polyline(mock_db, "route-123")
                
                assert result == 'encoded_polyline_string'
                mock_calculate.assert_called_once_with(
                    db=mock_db,
                    route_id="route-123",
                    update_route=False
                )
    
    @pytest.mark.asyncio
    async def test_maps_service_unavailable_scenarios(self, maps_service, mock_db):
        """Test all methods when maps service is unavailable."""
        with patch.object(maps_service, '_get_maps_service', return_value=None):
            # Test all methods return appropriate values when service unavailable
            assert await maps_service.geocode_terminal(mock_db, "terminal-123") is None
            assert await maps_service.calculate_route_distance(mock_db, "route-123") is None
            assert await maps_service.search_terminals("query") == []
            assert await maps_service.get_terminal_autocomplete("input") == []
            assert await maps_service.calculate_trip_eta(mock_db, "trip-123", (0, 0)) is None
            assert await maps_service.get_route_polyline(mock_db, "route-123") is None