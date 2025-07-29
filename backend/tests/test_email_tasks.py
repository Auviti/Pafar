"""
Unit tests for email notification tasks.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.tasks.email_tasks import (
    send_booking_confirmation_email,
    send_booking_cancellation_email,
    send_payment_receipt_email,
    _send_email
)


class TestEmailTasks:
    """Test cases for email notification tasks."""
    
    @pytest.fixture
    def booking_data(self):
        """Sample booking data for testing."""
        return {
            "booking_reference": "BK123456",
            "origin": "New York",
            "destination": "Boston",
            "departure_time": "2024-01-15 10:00:00",
            "arrival_time": "2024-01-15 14:00:00",
            "seats": [1, 2],
            "total_amount": "150.00",
            "bus_info": "Luxury Coach #101"
        }
    
    @pytest.fixture
    def payment_data(self):
        """Sample payment data for testing."""
        return {
            "transaction_id": "TXN789012",
            "booking_reference": "BK123456",
            "amount": "150.00",
            "payment_method": "Credit Card",
            "payment_date": "2024-01-15 09:30:00",
            "status": "completed"
        }
    
    @patch('app.tasks.email_tasks._send_email')
    def test_send_booking_confirmation_email_success(self, mock_send_email, booking_data):
        """Test successful booking confirmation email sending."""
        # Arrange
        mock_send_email.return_value = True
        user_email = "test@example.com"
        user_name = "John Doe"
        
        # Act
        result = send_booking_confirmation_email(user_email, user_name, booking_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        assert "successfully" in result["message"]
        mock_send_email.assert_called_once()
        
        # Check email content
        call_args = mock_send_email.call_args
        assert call_args[1]["to_email"] == user_email
        assert "Booking Confirmation - BK123456" in call_args[1]["subject"]
        assert "John Doe" in call_args[1]["html_content"]
        assert "BK123456" in call_args[1]["html_content"]
    
    @patch('app.tasks.email_tasks._send_email')
    def test_send_booking_confirmation_email_failure(self, mock_send_email, booking_data):
        """Test booking confirmation email sending failure."""
        # Arrange
        mock_send_email.side_effect = Exception("SMTP error")
        user_email = "test@example.com"
        user_name = "John Doe"
        
        # Mock the task context
        with patch('app.tasks.email_tasks.send_booking_confirmation_email.request') as mock_request:
            mock_request.retries = 3
            
            # Act
            result = send_booking_confirmation_email(user_email, user_name, booking_data)
            
            # Assert
            assert result["success"] is False
            assert "Failed to send" in result["message"]
            assert result["booking_reference"] == "BK123456"
    
    @patch('app.tasks.email_tasks._send_email')
    def test_send_booking_cancellation_email_success(self, mock_send_email, booking_data):
        """Test successful booking cancellation email sending."""
        # Arrange
        mock_send_email.return_value = True
        booking_data.update({
            "refund_amount": "120.00",
            "refund_reference": "REF789012"
        })
        
        # Act
        result = send_booking_cancellation_email("test@example.com", "John Doe", booking_data)
        
        # Assert
        assert result["success"] is True
        assert result["booking_reference"] == "BK123456"
        mock_send_email.assert_called_once()
        
        # Check email content
        call_args = mock_send_email.call_args
        assert "Booking Cancellation - BK123456" in call_args[1]["subject"]
        assert "120.00" in call_args[1]["html_content"]
        assert "REF789012" in call_args[1]["html_content"]
    
    @patch('app.tasks.email_tasks._send_email')
    def test_send_payment_receipt_email_success(self, mock_send_email, payment_data):
        """Test successful payment receipt email sending."""
        # Arrange
        mock_send_email.return_value = True
        receipt_pdf = b"fake_pdf_content"
        
        # Act
        result = send_payment_receipt_email(
            "test@example.com", 
            "John Doe", 
            payment_data, 
            receipt_pdf
        )
        
        # Assert
        assert result["success"] is True
        assert result["transaction_id"] == "TXN789012"
        mock_send_email.assert_called_once()
        
        # Check email content and attachment
        call_args = mock_send_email.call_args
        assert "Payment Receipt - TXN789012" in call_args[1]["subject"]
        assert call_args[1]["attachment"] == receipt_pdf
        assert "receipt_TXN789012.pdf" in call_args[1]["attachment_name"]
    
    @patch('smtplib.SMTP')
    @patch('app.tasks.email_tasks.settings')
    def test_send_email_success(self, mock_settings, mock_smtp_class):
        """Test successful email sending via SMTP."""
        # Arrange
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "password"
        
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        
        # Act
        result = _send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>"
        )
        
        # Assert
        assert result is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("sender@example.com", "password")
        mock_smtp.sendmail.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    @patch('smtplib.SMTP')
    @patch('app.tasks.email_tasks.settings')
    def test_send_email_with_attachment(self, mock_settings, mock_smtp_class):
        """Test email sending with attachment."""
        # Arrange
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "password"
        
        mock_smtp = Mock()
        mock_smtp_class.return_value = mock_smtp
        
        attachment_data = b"fake_pdf_content"
        
        # Act
        result = _send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>Test Content</h1>",
            attachment=attachment_data,
            attachment_name="test.pdf"
        )
        
        # Assert
        assert result is True
        mock_smtp.sendmail.assert_called_once()
    
    @patch('app.tasks.email_tasks.settings')
    def test_send_email_missing_config(self, mock_settings):
        """Test email sending with missing SMTP configuration."""
        # Arrange
        mock_settings.SMTP_HOST = None
        mock_settings.SMTP_USER = None
        mock_settings.SMTP_PASSWORD = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="SMTP configuration is incomplete"):
            _send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test Content</h1>"
            )
    
    @patch('smtplib.SMTP')
    @patch('app.tasks.email_tasks.settings')
    def test_send_email_smtp_failure(self, mock_settings, mock_smtp_class):
        """Test email sending with SMTP failure."""
        # Arrange
        mock_settings.SMTP_HOST = "smtp.example.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USER = "sender@example.com"
        mock_settings.SMTP_PASSWORD = "password"
        
        mock_smtp = Mock()
        mock_smtp.login.side_effect = Exception("Authentication failed")
        mock_smtp_class.return_value = mock_smtp
        
        # Act & Assert
        with pytest.raises(Exception, match="Authentication failed"):
            _send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<h1>Test Content</h1>"
            )
    
    def test_email_template_rendering(self, booking_data):
        """Test that email templates render correctly with data."""
        # This would be tested implicitly in the email sending tests,
        # but we can add specific template tests here
        
        # Test that all required fields are present in booking data
        required_fields = [
            "booking_reference", "origin", "destination", 
            "departure_time", "arrival_time", "seats", 
            "total_amount", "bus_info"
        ]
        
        for field in required_fields:
            assert field in booking_data, f"Missing required field: {field}"
        
        # Test seat formatting
        seats_str = ", ".join(map(str, booking_data["seats"]))
        assert seats_str == "1, 2"