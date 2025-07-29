"""
SMS notification tasks for trip updates and alerts.
"""
import httpx
from typing import Dict, Any, Optional
from celery import current_task
from ..core.celery_app import celery_app
from ..core.config import settings


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_trip_departure_sms(
    self,
    phone_number: str,
    user_name: str,
    trip_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send SMS notification when trip is about to depart.
    
    Args:
        phone_number: User's phone number
        user_name: User's name
        trip_data: Dictionary containing trip details
        
    Returns:
        Dict with success status and message
    """
    try:
        message = (
            f"Hi {user_name}, your trip {trip_data.get('booking_reference')} "
            f"from {trip_data.get('origin')} to {trip_data.get('destination')} "
            f"is departing at {trip_data.get('departure_time')}. "
            f"Please arrive at the terminal 30 minutes early. "
            f"Seat(s): {', '.join(map(str, trip_data.get('seats', [])))}. "
            f"Safe travels! - Pafar Transport"
        )
        
        result = _send_sms(phone_number, message)
        
        return {
            "success": True,
            "message": "Trip departure SMS sent successfully",
            "booking_reference": trip_data.get("booking_reference"),
            "sms_id": result.get("sms_id")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send trip departure SMS: {str(exc)}",
            "booking_reference": trip_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_trip_delay_sms(
    self,
    phone_number: str,
    user_name: str,
    trip_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send SMS notification when trip is delayed.
    
    Args:
        phone_number: User's phone number
        user_name: User's name
        trip_data: Dictionary containing trip and delay details
        
    Returns:
        Dict with success status and message
    """
    try:
        delay_minutes = trip_data.get("delay_minutes", 0)
        new_departure = trip_data.get("new_departure_time")
        
        message = (
            f"Hi {user_name}, your trip {trip_data.get('booking_reference')} "
            f"has been delayed by {delay_minutes} minutes. "
            f"New departure time: {new_departure}. "
            f"We apologize for the inconvenience. "
            f"Track your trip live on our app. - Pafar Transport"
        )
        
        result = _send_sms(phone_number, message)
        
        return {
            "success": True,
            "message": "Trip delay SMS sent successfully",
            "booking_reference": trip_data.get("booking_reference"),
            "sms_id": result.get("sms_id")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send trip delay SMS: {str(exc)}",
            "booking_reference": trip_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_trip_arrival_sms(
    self,
    phone_number: str,
    user_name: str,
    trip_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send SMS notification when trip is arriving at destination.
    
    Args:
        phone_number: User's phone number
        user_name: User's name
        trip_data: Dictionary containing trip details
        
    Returns:
        Dict with success status and message
    """
    try:
        eta_minutes = trip_data.get("eta_minutes", 5)
        
        message = (
            f"Hi {user_name}, your trip {trip_data.get('booking_reference')} "
            f"is arriving at {trip_data.get('destination')} in approximately "
            f"{eta_minutes} minutes. Please prepare for arrival. "
            f"Thank you for choosing Pafar Transport!"
        )
        
        result = _send_sms(phone_number, message)
        
        return {
            "success": True,
            "message": "Trip arrival SMS sent successfully",
            "booking_reference": trip_data.get("booking_reference"),
            "sms_id": result.get("sms_id")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send trip arrival SMS: {str(exc)}",
            "booking_reference": trip_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_sms(
    self,
    phone_number: str,
    user_name: str,
    booking_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send SMS confirmation when booking is completed.
    
    Args:
        phone_number: User's phone number
        user_name: User's name
        booking_data: Dictionary containing booking details
        
    Returns:
        Dict with success status and message
    """
    try:
        message = (
            f"Hi {user_name}, your booking is confirmed! "
            f"Ref: {booking_data.get('booking_reference')} "
            f"Route: {booking_data.get('origin')} → {booking_data.get('destination')} "
            f"Departure: {booking_data.get('departure_time')} "
            f"Seat(s): {', '.join(map(str, booking_data.get('seats', [])))} "
            f"Amount: ${booking_data.get('total_amount')}. "
            f"Check email for details. - Pafar Transport"
        )
        
        result = _send_sms(phone_number, message)
        
        return {
            "success": True,
            "message": "Booking confirmation SMS sent successfully",
            "booking_reference": booking_data.get("booking_reference"),
            "sms_id": result.get("sms_id")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send booking confirmation SMS: {str(exc)}",
            "booking_reference": booking_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_otp_sms(
    self,
    phone_number: str,
    otp_code: str,
    purpose: str = "verification"
) -> Dict[str, Any]:
    """
    Send OTP SMS for verification purposes.
    
    Args:
        phone_number: User's phone number
        otp_code: OTP code to send
        purpose: Purpose of the OTP (verification, password_reset, etc.)
        
    Returns:
        Dict with success status and message
    """
    try:
        purpose_text = {
            "verification": "account verification",
            "password_reset": "password reset",
            "login": "login verification"
        }.get(purpose, "verification")
        
        message = (
            f"Your Pafar Transport {purpose_text} code is: {otp_code}. "
            f"This code will expire in 10 minutes. "
            f"Do not share this code with anyone."
        )
        
        result = _send_sms(phone_number, message)
        
        return {
            "success": True,
            "message": f"OTP SMS sent successfully for {purpose}",
            "sms_id": result.get("sms_id")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send OTP SMS: {str(exc)}"
        }


def _send_sms(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Internal function to send SMS via SMS gateway API.
    
    Args:
        phone_number: Recipient phone number
        message: SMS message content
        
    Returns:
        Dict with SMS gateway response
    """
    if not all([settings.SMS_API_KEY, settings.SMS_API_URL]):
        raise ValueError("SMS configuration is incomplete")
    
    # Clean phone number (remove non-digits except +)
    clean_phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # Prepare SMS payload (this is a generic example - adjust for your SMS provider)
    payload = {
        "api_key": settings.SMS_API_KEY,
        "to": clean_phone,
        "message": message,
        "from": "Pafar"  # Sender ID
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.SMS_API_KEY}"
    }
    
    try:
        import asyncio
        
        async def send_sms_async():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.SMS_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "success": True,
                    "sms_id": result.get("message_id", "unknown"),
                    "status": result.get("status", "sent")
                }
        
        return asyncio.run(send_sms_async())
            
    except httpx.HTTPError as e:
        raise Exception(f"SMS API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to send SMS: {str(e)}")