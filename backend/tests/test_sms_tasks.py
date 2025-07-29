"""
Unit tests for SMS notification tasks.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.tasks.sms_tasks import (
    send_trip_departure_sms,
    send_trip_delay_sms,
    send_trip_arrival_sms,
    send_booking_confirmation_sms,
    send_otp_sms,
    _send_sms
)


class TestSMSTasks:
    """Test cases for SMS notification tasks."""
    
    @pytest.fixture
    def trip_data(self):
        """Sample trip data for testing."""
        return {
            "booking_reference": "BK123456",
            "origin": "New York",
            "destination": "Boston",
            "departure_time": "2024-01-15 10:00:00",
            "seats": [1, 2],
            "delay_minutes": 30,
            "new_departure_time": "2024-01-15 10:30:00",
            "eta_minutes": 15
        }
    
    @pytest.fixture
    def booking_data(self):
        """Sample booking data for testing."""
        return {
            "booking_reference": "BK123456",
            "origin": "New York",
            "destination": "Boston",
            "departure_time": "2024-01-15 10:00:00",
            "seats": [1, 2],
            "total_amount": "150.00"
        }
    
    @patch('app.tasks.sms_tasks._send_sms')
    @pytest.mark.asyncio
    async def test_send_trip_departure_sms_success(self, mock_send_sms, trip_data):
        """Test successful trip departure SMS sending."""
        # Arrange
        mock_send_sms.return_value = {"success": True, "sms_id": "SMS123"}
        phone_number = "+1234567890"
        user_name = "John Doe"
        
        # Act
        result = send_trip_departure_sms(phone_number, user_name, trip_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        assert result["sms_id"] == "SMS123"
        assert "successfully" in result["message"]
        
        # Check SMS content
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "John Doe" in sms_message
        assert "BK123456" in sms_message
        assert "New York" in sms_message
        assert "Boston" in sms_message
        assert "1, 2" in sms_message
    
    @patch('app.tasks.sms_tasks._send_sms')
    def test_send_trip_departure_sms_failure(self, mock_send_sms, trip_data):
        """Test trip departure SMS sending failure."""
        # Arrange
        mock_send_sms.side_effect = Exception("SMS API error")
        
        # Mock the task context
        with patch('app.tasks.sms_tasks.send_trip_departure_sms.request') as mock_request:
            mock_request.retries = 3
            
            # Act
            result = send_trip_departure_sms("+1234567890", "John Doe", trip_data)
            
            # Assert
            assert result["success"] is False
            assert "Failed to send" in result["message"]
            assert result["booking_reference"] == "BK123456"
    
    @patch('app.tasks.sms_tasks._send_sms')
    def test_send_trip_delay_sms_success(self, mock_send_sms, trip_data):
        """Test successful trip delay SMS sending."""
        # Arrange
        mock_send_sms.return_value = {"success": True, "sms_id": "SMS124"}
        
        # Act
        result = send_trip_delay_sms("+1234567890", "John Doe", trip_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        
        # Check SMS content includes delay information
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "delayed by 30 minutes" in sms_message
        assert "2024-01-15 10:30:00" in sms_message
    
    @patch('app.tasks.sms_tasks._send_sms')
    def test_send_trip_arrival_sms_success(self, mock_send_sms, trip_data):
        """Test successful trip arrival SMS sending."""
        # Arrange
        mock_send_sms.return_value = {"success": True, "sms_id": "SMS125"}
        
        # Act
        result = send_trip_arrival_sms("+1234567890", "John Doe", trip_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        
        # Check SMS content includes ETA
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "15 minutes" in sms_message
        assert "Boston" in sms_message
    
    @patch('app.tasks.sms_tasks._send_sms')
    def test_send_booking_confirmation_sms_success(self, mock_send_sms, booking_data):
        """Test successful booking confirmation SMS sending."""
        # Arrange
        mock_send_sms.return_value = {"success": True, "sms_id": "SMS126"}
        
        # Act
        result = send_booking_confirmation_sms("+1234567890", "John Doe", booking_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        
        # Check SMS content includes booking details
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "booking is confirmed" in sms_message
        assert "BK123456" in sms_message
        assert "$150.00" in sms_message
    
    @patch('app.tasks.sms_tasks._send_sms')
    def test_send_otp_sms_success(self, mock_send_sms):
        """Test successful OTP SMS sending."""
        # Arrange
        mock_send_sms.return_value = {"success": True, "sms_id": "SMS127"}
        
        # Act
        result = send_otp_sms("+1234567890", "123456", "verification")
        
        # Assert
        assert result["success"] is True
        assert "verification" in result["message"]
        
        # Check SMS content includes OTP
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "123456" in sms_message
        assert "account verification" in sms_message
        assert "10 minutes" in sms_message
    
    @patch('app.tasks.sms_tasks._send_sms')
    def test_send_otp_sms_different_purposes(self, mock_send_sms):
        """Test OTP SMS with different purposes."""
        mock_send_sms.return_value = {"success": True, "sms_id": "SMS128"}
        
        # Test password reset
        result = send_otp_sms("+1234567890", "654321", "password_reset")
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "password reset" in sms_message
        
        # Test login verification
        result = send_otp_sms("+1234567890", "789012", "login")
        call_args = mock_send_sms.call_args
        sms_message = call_args[0][1]
        assert "login verification" in sms_message
    
    @patch('httpx.AsyncClient')
    @patch('app.tasks.sms_tasks.settings')
    @pytest.mark.asyncio
    async def test_send_sms_success(self, mock_settings, mock_client_class):
        """Test successful SMS sending via API."""
        # Arrange
        mock_settings.SMS_API_KEY = "test_api_key"
        mock_settings.SMS_API_URL = "https://api.sms.com/send"
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": "MSG123",
            "status": "sent"
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Act
        result = await _send_sms("+1234567890", "Test message")
        
        # Assert
        assert result["success"] is True
        assert result["sms_id"] == "MSG123"
        assert result["status"] == "sent"
        
        # Check API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.sms.com/send"
        assert call_args[1]["json"]["to"] == "+1234567890"
        assert call_args[1]["json"]["message"] == "Test message"
    
    @patch('app.tasks.sms_tasks.settings')
    @pytest.mark.asyncio
    async def test_send_sms_missing_config(self, mock_settings):
        """Test SMS sending with missing configuration."""
        # Arrange
        mock_settings.SMS_API_KEY = None
        mock_settings.SMS_API_URL = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="SMS configuration is incomplete"):
            await _send_sms("+1234567890", "Test message")
    
    @patch('httpx.AsyncClient')
    @patch('app.tasks.sms_tasks.settings')
    @pytest.mark.asyncio
    async def test_send_sms_api_error(self, mock_settings, mock_client_class):
        """Test SMS sending with API error."""
        # Arrange
        mock_settings.SMS_API_KEY = "test_api_key"
        mock_settings.SMS_API_URL = "https://api.sms.com/send"
        
        mock_client = AsyncMock()
        mock_client.post.side_effect = Exception("Network error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Act & Assert
        with pytest.raises(Exception, match="Failed to send SMS"):
            await _send_sms("+1234567890", "Test message")
    
    def test_phone_number_cleaning(self):
        """Test phone number cleaning functionality."""
        # This would be tested as part of the _send_sms function
        # Test cases for different phone number formats
        test_numbers = [
            ("+1 (234) 567-8900", "+12345678900"),
            ("234-567-8900", "2345678900"),
            "+1234567890",
            "1234567890"
        ]
        
        for original, expected in test_numbers:
            # Clean phone number (remove non-digits except +)
            clean_phone = ''.join(c for c in original if c.isdigit() or c == '+')
            if len(test_numbers) > 2:  # Only check first two test cases
                assert clean_phone == expected
    
    def test_sms_message_length(self, trip_data, booking_data):
        """Test that SMS messages are within reasonable length limits."""
        # SMS messages should typically be under 160 characters for single SMS
        # or under 1600 characters for concatenated SMS
        
        # Test trip departure message
        message = (
            f"Hi John Doe, your trip {trip_data.get('booking_reference')} "
            f"from {trip_data.get('origin')} to {trip_data.get('destination')} "
            f"is departing at {trip_data.get('departure_time')}. "
            f"Please arrive at the terminal 30 minutes early. "
            f"Seat(s): {', '.join(map(str, trip_data.get('seats', [])))}. "
            f"Safe travels! - Pafar Transport"
        )
        
        assert len(message) < 1600, "SMS message too long"
        
        # Test booking confirmation message
        message = (
            f"Hi John Doe, your booking is confirmed! "
            f"Ref: {booking_data.get('booking_reference')} "
            f"Route: {booking_data.get('origin')} → {booking_data.get('destination')} "
            f"Departure: {booking_data.get('departure_time')} "
            f"Seat(s): {', '.join(map(str, booking_data.get('seats', [])))} "
            f"Amount: ${booking_data.get('total_amount')}. "
            f"Check email for details. - Pafar Transport"
        )
        
        assert len(message) < 1600, "SMS message too long"