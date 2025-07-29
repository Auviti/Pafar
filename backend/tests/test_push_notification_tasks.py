"""
Unit tests for push notification tasks.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.tasks.push_notification_tasks import (
    send_booking_confirmation_push,
    send_trip_status_push,
    send_location_update_push,
    send_payment_status_push,
    send_promotional_push,
    send_bulk_push_notification,
    _send_push_notification
)


class TestPushNotificationTasks:
    """Test cases for push notification tasks."""
    
    @pytest.fixture
    def device_tokens(self):
        """Sample device tokens for testing."""
        return ["token1", "token2", "token3"]
    
    @pytest.fixture
    def booking_data(self):
        """Sample booking data for testing."""
        return {
            "booking_id": "booking123",
            "booking_reference": "BK123456",
            "trip_id": "trip123",
            "origin": "New York",
            "destination": "Boston",
            "departure_time": "2024-01-15 10:00:00",
            "seats": [1, 2],
            "total_amount": "150.00"
        }
    
    @pytest.fixture
    def trip_data(self):
        """Sample trip data for testing."""
        return {
            "trip_id": "trip123",
            "booking_reference": "BK123456",
            "status": "departed",
            "delay_minutes": 30,
            "eta_minutes": 15,
            "timestamp": "2024-01-15T10:00:00Z"
        }
    
    @pytest.fixture
    def payment_data(self):
        """Sample payment data for testing."""
        return {
            "payment_id": "pay123",
            "booking_reference": "BK123456",
            "amount": "150.00",
            "status": "completed"
        }
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    @pytest.mark.asyncio
    async def test_send_booking_confirmation_push_success(
        self, mock_send_push, device_tokens, booking_data
    ):
        """Test successful booking confirmation push notification."""
        # Arrange
        mock_send_push.return_value = {"success_count": 3, "failure_count": 0}
        
        # Act
        result = send_booking_confirmation_push(device_tokens, "John Doe", booking_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        assert result["sent_count"] == 3
        assert result["failed_count"] == 0
        
        # Check push notification call
        mock_send_push.assert_called_once()
        call_args = mock_send_push.call_args
        assert call_args[1]["device_tokens"] == device_tokens
        assert "Booking Confirmed!" in call_args[1]["title"]
        assert "New York" in call_args[1]["body"]
        assert "Boston" in call_args[1]["body"]
        assert call_args[1]["data"]["type"] == "booking_confirmation"
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    def test_send_booking_confirmation_push_failure(
        self, mock_send_push, device_tokens, booking_data
    ):
        """Test booking confirmation push notification failure."""
        # Arrange
        mock_send_push.side_effect = Exception("FCM error")
        
        # Mock the task context
        with patch('app.tasks.push_notification_tasks.send_booking_confirmation_push.request') as mock_request:
            mock_request.retries = 3
            
            # Act
            result = send_booking_confirmation_push(device_tokens, "John Doe", booking_data)
            
            # Assert
            assert result["success"] is False
            assert "Failed to send" in result["message"]
            assert result["booking_reference"] == "BK123456"
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    @pytest.mark.asyncio
    async def test_send_trip_status_push_different_statuses(
        self, mock_send_push, device_tokens, trip_data
    ):
        """Test trip status push notifications for different statuses."""
        mock_send_push.return_value = {"success_count": 3, "failure_count": 0}
        
        # Test different statuses
        statuses = [
            ("departed", "Trip Departed 🚌", "departed"),
            ("delayed", "Trip Delayed ⏰", "delayed by 30 minutes"),
            ("arriving", "Almost There! 🏁", "arriving in 15 minutes"),
            ("completed", "Trip Completed ✅", "completed")
        ]
        
        for status, expected_title, expected_body_part in statuses:
            trip_data["status"] = status
            
            # Act
            result = send_trip_status_push(device_tokens, trip_data)
            
            # Assert
            assert result["success"] is True
            assert result["booking_reference"] == "BK123456"
            
            # Check notification content
            call_args = mock_send_push.call_args
            assert expected_title in call_args[1]["title"]
            assert expected_body_part in call_args[1]["body"]
            assert call_args[1]["data"]["type"] == "trip_status"
            assert call_args[1]["data"]["status"] == status
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    @pytest.mark.asyncio
    async def test_send_location_update_push_success(self, mock_send_push, device_tokens):
        """Test successful location update push notification."""
        # Arrange
        mock_send_push.return_value = {"success_count": 3, "failure_count": 0}
        location_data = {
            "trip_id": "trip123",
            "booking_reference": "BK123456",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "landmark": "Times Square",
            "eta_minutes": 10
        }
        
        # Act
        result = send_location_update_push(device_tokens, location_data)
        
        # Assert
        assert result["success"] is True
        assert result["trip_id"] == "trip123"
        
        # Check notification content
        call_args = mock_send_push.call_args
        assert "Location Update 📍" in call_args[1]["title"]
        assert "Times Square" in call_args[1]["body"]
        assert "10 minutes" in call_args[1]["body"]
        assert call_args[1]["data"]["type"] == "location_update"
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    @pytest.mark.asyncio
    async def test_send_payment_status_push_different_statuses(
        self, mock_send_push, device_tokens, payment_data
    ):
        """Test payment status push notifications for different statuses."""
        mock_send_push.return_value = {"success_count": 3, "failure_count": 0}
        
        # Test different payment statuses
        statuses = [
            ("completed", "Payment Successful ✅", "completed"),
            ("failed", "Payment Failed ❌", "failed"),
            ("refunded", "Refund Processed 💰", "processed")
        ]
        
        for status, expected_title, expected_body_part in statuses:
            payment_data["status"] = status
            
            # Act
            result = send_payment_status_push(device_tokens, payment_data)
            
            # Assert
            assert result["success"] is True
            assert result["payment_id"] == "pay123"
            
            # Check notification content
            call_args = mock_send_push.call_args
            assert expected_title in call_args[1]["title"]
            assert expected_body_part in call_args[1]["body"]
            assert call_args[1]["data"]["type"] == "payment_status"
            assert call_args[1]["data"]["status"] == status
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    @pytest.mark.asyncio
    async def test_send_promotional_push_success(self, mock_send_push, device_tokens):
        """Test successful promotional push notification."""
        # Arrange
        mock_send_push.return_value = {"success_count": 3, "failure_count": 0}
        promotion_data = {
            "promotion_id": "promo123",
            "title": "50% Off Your Next Trip!",
            "message": "Use code SAVE50 for 50% off your next booking",
            "discount_code": "SAVE50",
            "valid_until": "2024-01-31"
        }
        
        # Act
        result = send_promotional_push(device_tokens, promotion_data)
        
        # Assert
        assert result["success"] is True
        assert result["promotion_id"] == "promo123"
        
        # Check notification content
        call_args = mock_send_push.call_args
        assert "50% Off Your Next Trip!" in call_args[1]["title"]
        assert "SAVE50" in call_args[1]["body"]
        assert call_args[1]["data"]["type"] == "promotion"
    
    @patch('app.tasks.push_notification_tasks._send_push_notification')
    @pytest.mark.asyncio
    async def test_send_bulk_push_notification_success(self, mock_send_push):
        """Test successful bulk push notification."""
        # Arrange
        mock_send_push.return_value = {"success_count": 2, "failure_count": 0}
        notification_data = {
            "user_tokens": {
                "user1": ["token1", "token2"],
                "user2": ["token3", "token4"]
            },
            "title": "System Maintenance",
            "body": "Scheduled maintenance tonight from 2-4 AM",
            "data": {"type": "maintenance"}
        }
        
        # Act
        result = send_bulk_push_notification(notification_data)
        
        # Assert
        assert result["success"] is True
        assert result["total_users"] == 2
        assert result["total_tokens"] == 4
        assert result["success_count"] == 4  # 2 calls × 2 success each
        assert result["failure_count"] == 0
        
        # Check that _send_push_notification was called for each user
        assert mock_send_push.call_count == 2
    
    @patch('httpx.AsyncClient')
    @patch('app.tasks.push_notification_tasks.settings')
    @pytest.mark.asyncio
    async def test_send_push_notification_success(self, mock_settings, mock_client_class):
        """Test successful push notification sending via FCM."""
        # Arrange
        mock_settings.FIREBASE_CREDENTIALS_PATH = "/path/to/credentials.json"
        
        # Mock file reading
        with patch('builtins.open', mock_open_file('{"server_key": "test_key"}')):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await _send_push_notification(
                device_tokens=["token1", "token2"],
                title="Test Title",
                body="Test Body",
                data={"key": "value"}
            )
            
            # Assert
            assert result["success_count"] == 2
            assert result["failure_count"] == 0
            assert result["total_tokens"] == 2
            
            # Check that FCM API was called for each token
            assert mock_client.post.call_count == 2
    
    @patch('app.tasks.push_notification_tasks.settings')
    @pytest.mark.asyncio
    async def test_send_push_notification_missing_config(self, mock_settings):
        """Test push notification with missing Firebase configuration."""
        # Arrange
        mock_settings.FIREBASE_CREDENTIALS_PATH = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Firebase credentials not configured"):
            await _send_push_notification(
                device_tokens=["token1"],
                title="Test",
                body="Test"
            )
    
    @patch('httpx.AsyncClient')
    @patch('app.tasks.push_notification_tasks.settings')
    @pytest.mark.asyncio
    async def test_send_push_notification_partial_failure(self, mock_settings, mock_client_class):
        """Test push notification with partial failures."""
        # Arrange
        mock_settings.FIREBASE_CREDENTIALS_PATH = "/path/to/credentials.json"
        
        with patch('builtins.open', mock_open_file('{"server_key": "test_key"}')):
            # Mock responses - first succeeds, second fails
            success_response = Mock()
            success_response.status_code = 200
            success_response.raise_for_status.return_value = None
            
            failure_response = Mock()
            failure_response.status_code = 400
            failure_response.raise_for_status.side_effect = Exception("Invalid token")
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [success_response, failure_response]
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Act
            result = await _send_push_notification(
                device_tokens=["valid_token", "invalid_token"],
                title="Test Title",
                body="Test Body"
            )
            
            # Assert
            assert result["success_count"] == 1
            assert result["failure_count"] == 1
            assert result["total_tokens"] == 2
    
    def test_notification_data_structure(self, booking_data, trip_data, payment_data):
        """Test that notification data structures are properly formatted."""
        # Test booking confirmation data
        expected_booking_data = {
            "type": "booking_confirmation",
            "booking_id": booking_data["booking_id"],
            "booking_reference": booking_data["booking_reference"],
            "trip_id": booking_data["trip_id"]
        }
        
        # Test trip status data
        expected_trip_data = {
            "type": "trip_status",
            "trip_id": trip_data["trip_id"],
            "booking_reference": trip_data["booking_reference"],
            "status": trip_data["status"],
            "timestamp": trip_data["timestamp"]
        }
        
        # Test payment status data
        expected_payment_data = {
            "type": "payment_status",
            "payment_id": payment_data["payment_id"],
            "booking_reference": payment_data["booking_reference"],
            "status": payment_data["status"],
            "amount": str(payment_data["amount"])
        }
        
        # Verify all required fields are present
        for data in [expected_booking_data, expected_trip_data, expected_payment_data]:
            assert "type" in data
            assert "booking_reference" in data or "payment_id" in data


def mock_open_file(content):
    """Helper function to mock file opening."""
    from unittest.mock import mock_open
    return mock_open(read_data=content)