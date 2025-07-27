"""
Unit tests for WebSocket functionality.
"""
import pytest
import pytest_asyncio
import uuid
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from app.main import app
from app.api.v1.websocket import ConnectionManager, manager
from app.models.fleet import Trip, TripStatus
from app.models.user import User


class TestConnectionManager:
    """Test cases for WebSocket ConnectionManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConnectionManager()
        self.mock_websocket = MagicMock(spec=WebSocket)
        self.mock_websocket.send_text = AsyncMock()
        self.trip_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.driver_id = str(uuid.uuid4())
    
    @pytest.mark.asyncio
    async def test_connect_passenger(self):
        """Test passenger connection to trip updates."""
        self.mock_websocket.accept = AsyncMock()
        
        await self.manager.connect_passenger(
            self.mock_websocket, 
            self.trip_id, 
            self.user_id
        )
        
        # Verify websocket was accepted
        self.mock_websocket.accept.assert_called_once()
        
        # Verify connections are stored
        assert self.trip_id in self.manager.trip_connections
        assert self.mock_websocket in self.manager.trip_connections[self.trip_id]
        assert self.user_id in self.manager.user_connections
        assert self.manager.user_connections[self.user_id] == self.mock_websocket
    
    @pytest.mark.asyncio
    async def test_connect_driver(self):
        """Test driver connection."""
        self.mock_websocket.accept = AsyncMock()
        
        await self.manager.connect_driver(self.mock_websocket, self.driver_id)
        
        # Verify websocket was accepted
        self.mock_websocket.accept.assert_called_once()
        
        # Verify driver connection is stored
        assert self.driver_id in self.manager.driver_connections
        assert self.manager.driver_connections[self.driver_id] == self.mock_websocket
    
    def test_disconnect_passenger(self):
        """Test passenger disconnection."""
        # First connect the passenger
        self.manager.trip_connections[self.trip_id] = {self.mock_websocket}
        self.manager.user_connections[self.user_id] = self.mock_websocket
        
        # Then disconnect
        self.manager.disconnect_passenger(
            self.mock_websocket, 
            self.trip_id, 
            self.user_id
        )
        
        # Verify connections are removed
        assert self.trip_id not in self.manager.trip_connections
        assert self.user_id not in self.manager.user_connections
    
    def test_disconnect_driver(self):
        """Test driver disconnection."""
        # First connect the driver
        self.manager.driver_connections[self.driver_id] = self.mock_websocket
        
        # Then disconnect
        self.manager.disconnect_driver(self.mock_websocket, self.driver_id)
        
        # Verify connection is removed
        assert self.driver_id not in self.manager.driver_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_to_trip(self):
        """Test broadcasting message to all passengers on a trip."""
        # Set up multiple websockets for the trip
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        
        self.manager.trip_connections[self.trip_id] = {mock_ws1, mock_ws2}
        
        message = {"type": "location_update", "data": {"lat": 40.7589, "lng": -73.9851}}
        
        await self.manager.broadcast_to_trip(self.trip_id, message)
        
        # Verify message was sent to all websockets
        expected_message = json.dumps(message)
        mock_ws1.send_text.assert_called_once_with(expected_message)
        mock_ws2.send_text.assert_called_once_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_trip_handles_disconnected_websockets(self):
        """Test that broadcasting handles disconnected websockets gracefully."""
        # Set up websockets, one that will fail
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        
        self.manager.trip_connections[self.trip_id] = {mock_ws1, mock_ws2}
        
        message = {"type": "location_update", "data": {"lat": 40.7589, "lng": -73.9851}}
        
        await self.manager.broadcast_to_trip(self.trip_id, message)
        
        # Verify working websocket received message
        mock_ws1.send_text.assert_called_once()
        
        # Verify failed websocket was removed from connections
        assert mock_ws2 not in self.manager.trip_connections[self.trip_id]
    
    @pytest.mark.asyncio
    async def test_send_to_driver(self):
        """Test sending message to specific driver."""
        self.manager.driver_connections[self.driver_id] = self.mock_websocket
        
        message = {"type": "trip_assignment", "data": {"trip_id": self.trip_id}}
        
        await self.manager.send_to_driver(self.driver_id, message)
        
        expected_message = json.dumps(message)
        self.mock_websocket.send_text.assert_called_once_with(expected_message)
    
    @pytest.mark.asyncio
    async def test_send_to_driver_handles_disconnected_websocket(self):
        """Test sending to driver handles disconnected websocket."""
        self.mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        self.manager.driver_connections[self.driver_id] = self.mock_websocket
        
        message = {"type": "trip_assignment", "data": {"trip_id": self.trip_id}}
        
        await self.manager.send_to_driver(self.driver_id, message)
        
        # Verify driver connection was removed after failure
        assert self.driver_id not in self.manager.driver_connections
    
    @pytest.mark.asyncio
    async def test_send_to_user(self):
        """Test sending message to specific user."""
        self.manager.user_connections[self.user_id] = self.mock_websocket
        
        message = {"type": "booking_confirmation", "data": {"booking_id": str(uuid.uuid4())}}
        
        await self.manager.send_to_user(self.user_id, message)
        
        expected_message = json.dumps(message)
        self.mock_websocket.send_text.assert_called_once_with(expected_message)


class TestWebSocketEndpoints:
    """Test cases for WebSocket endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_valid(self):
        """Test token validation with valid token."""
        from app.api.v1.websocket import get_current_user_from_token
        
        mock_payload = {"sub": str(uuid.uuid4()), "role": "passenger"}
        
        with patch('app.api.v1.websocket.decode_access_token', return_value=mock_payload):
            result = await get_current_user_from_token("valid_token")
            
            assert result == mock_payload
    
    @pytest.mark.asyncio
    async def test_get_current_user_from_token_invalid(self):
        """Test token validation with invalid token."""
        from app.api.v1.websocket import get_current_user_from_token
        
        with patch('app.api.v1.websocket.decode_access_token', side_effect=Exception("Invalid token")):
            result = await get_current_user_from_token("invalid_token")
            
            assert result is None


class TestWebSocketHandlers:
    """Test cases for WebSocket message handlers."""
    
    @pytest.mark.asyncio
    async def test_handle_driver_location_update(self):
        """Test handling driver location update."""
        from app.api.v1.websocket import handle_driver_location_update, manager
        from app.services.tracking_service import TrackingService
        
        # Mock tracking service
        mock_tracking_service = MagicMock(spec=TrackingService)
        mock_location = MagicMock()
        mock_location.trip_id = uuid.uuid4()
        mock_location.latitude = 40.7589
        mock_location.longitude = -73.9851
        mock_location.speed = 45.5
        mock_location.heading = 180.0
        mock_location.recorded_at.isoformat.return_value = "2024-01-01T12:00:00"
        
        mock_tracking_service.update_trip_location = AsyncMock(return_value=mock_location)
        
        message = {
            "type": "location_update",
            "data": {
                "trip_id": str(mock_location.trip_id),
                "latitude": 40.7589,
                "longitude": -73.9851,
                "speed": 45.5,
                "heading": 180.0
            }
        }
        
        driver_id = str(uuid.uuid4())
        
        # Mock the broadcast method
        with patch.object(manager, 'broadcast_to_trip', new_callable=AsyncMock) as mock_broadcast:
            await handle_driver_location_update(message, mock_tracking_service, driver_id)
            
            # Verify tracking service was called
            mock_tracking_service.update_trip_location.assert_called_once_with(
                trip_id=mock_location.trip_id,
                latitude=40.7589,
                longitude=-73.9851,
                speed=45.5,
                heading=180.0
            )
            
            # Verify broadcast was called
            mock_broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_driver_location_update_missing_data(self):
        """Test handling driver location update with missing data."""
        from app.api.v1.websocket import handle_driver_location_update
        from app.services.tracking_service import TrackingService
        
        mock_tracking_service = MagicMock(spec=TrackingService)
        
        message = {
            "type": "location_update",
            "data": {
                "trip_id": str(uuid.uuid4()),
                # Missing latitude and longitude
            }
        }
        
        driver_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="Missing required location data"):
            await handle_driver_location_update(message, mock_tracking_service, driver_id)
    
    @pytest.mark.asyncio
    async def test_handle_driver_status_update(self):
        """Test handling driver status update."""
        from app.api.v1.websocket import handle_driver_status_update, manager
        from app.services.tracking_service import TrackingService
        
        # Mock tracking service
        mock_tracking_service = MagicMock(spec=TrackingService)
        mock_trip = MagicMock()
        mock_trip.id = uuid.uuid4()
        mock_trip.status.value = "in_transit"
        
        mock_tracking_service.update_trip_status = AsyncMock(return_value=mock_trip)
        
        message = {
            "type": "status_update",
            "data": {
                "trip_id": str(mock_trip.id),
                "status": "in_transit"
            }
        }
        
        driver_id = str(uuid.uuid4())
        
        # Mock the broadcast method
        with patch.object(manager, 'broadcast_to_trip', new_callable=AsyncMock) as mock_broadcast:
            with patch('app.api.v1.websocket.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = "2024-01-01T12:00:00"
                
                await handle_driver_status_update(message, mock_tracking_service, driver_id)
                
                # Verify tracking service was called
                mock_tracking_service.update_trip_status.assert_called_once()
                
                # Verify broadcast was called
                mock_broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_driver_status_update_missing_data(self):
        """Test handling driver status update with missing data."""
        from app.api.v1.websocket import handle_driver_status_update
        from app.services.tracking_service import TrackingService
        
        mock_tracking_service = MagicMock(spec=TrackingService)
        
        message = {
            "type": "status_update",
            "data": {
                "trip_id": str(uuid.uuid4()),
                # Missing status
            }
        }
        
        driver_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="Missing required status data"):
            await handle_driver_status_update(message, mock_tracking_service, driver_id)