"""
Push notification tasks for mobile app alerts.
"""
import json
from typing import Dict, Any, List, Optional
import httpx
from celery import current_task
from ..core.celery_app import celery_app
from ..core.config import settings


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_push(
    self,
    device_tokens: List[str],
    user_name: str,
    booking_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send push notification for booking confirmation.
    
    Args:
        device_tokens: List of FCM device tokens
        user_name: User's name
        booking_data: Dictionary containing booking details
        
    Returns:
        Dict with success status and message
    """
    try:
        title = "Booking Confirmed! 🎉"
        body = (
            f"Your trip from {booking_data.get('origin')} to "
            f"{booking_data.get('destination')} is confirmed. "
            f"Ref: {booking_data.get('booking_reference')}"
        )
        
        data = {
            "type": "booking_confirmation",
            "booking_id": booking_data.get("booking_id"),
            "booking_reference": booking_data.get("booking_reference"),
            "trip_id": booking_data.get("trip_id")
        }
        
        import asyncio
        result = asyncio.run(_send_push_notification(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data
        ))
        
        return {
            "success": True,
            "message": "Booking confirmation push notification sent",
            "booking_reference": booking_data.get("booking_reference"),
            "sent_count": result.get("success_count", 0),
            "failed_count": result.get("failure_count", 0)
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send booking confirmation push: {str(exc)}",
            "booking_reference": booking_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_trip_status_push(
    self,
    device_tokens: List[str],
    trip_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send push notification for trip status updates.
    
    Args:
        device_tokens: List of FCM device tokens
        trip_data: Dictionary containing trip status details
        
    Returns:
        Dict with success status and message
    """
    try:
        status = trip_data.get("status")
        booking_ref = trip_data.get("booking_reference")
        
        # Customize notification based on status
        if status == "departed":
            title = "Trip Departed 🚌"
            body = f"Your trip {booking_ref} has departed. Track it live!"
            icon = "🚌"
        elif status == "delayed":
            title = "Trip Delayed ⏰"
            body = f"Trip {booking_ref} delayed by {trip_data.get('delay_minutes')} minutes"
            icon = "⏰"
        elif status == "arriving":
            title = "Almost There! 🏁"
            body = f"Trip {booking_ref} arriving in {trip_data.get('eta_minutes')} minutes"
            icon = "🏁"
        elif status == "completed":
            title = "Trip Completed ✅"
            body = f"Trip {booking_ref} completed. Rate your experience!"
            icon = "✅"
        else:
            title = "Trip Update"
            body = f"Status update for trip {booking_ref}"
            icon = "ℹ️"
        
        data = {
            "type": "trip_status",
            "trip_id": trip_data.get("trip_id"),
            "booking_reference": booking_ref,
            "status": status,
            "timestamp": trip_data.get("timestamp")
        }
        
        import asyncio
        result = asyncio.run(_send_push_notification(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data,
            icon=icon
        ))
        
        return {
            "success": True,
            "message": f"Trip status push notification sent for {status}",
            "booking_reference": booking_ref,
            "sent_count": result.get("success_count", 0),
            "failed_count": result.get("failure_count", 0)
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send trip status push: {str(exc)}",
            "booking_reference": trip_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_location_update_push(
    self,
    device_tokens: List[str],
    location_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send push notification for significant location updates.
    
    Args:
        device_tokens: List of FCM device tokens
        location_data: Dictionary containing location details
        
    Returns:
        Dict with success status and message
    """
    try:
        title = "Location Update 📍"
        body = (
            f"Your bus is now near {location_data.get('landmark')}. "
            f"ETA: {location_data.get('eta_minutes')} minutes"
        )
        
        data = {
            "type": "location_update",
            "trip_id": location_data.get("trip_id"),
            "booking_reference": location_data.get("booking_reference"),
            "latitude": str(location_data.get("latitude")),
            "longitude": str(location_data.get("longitude")),
            "eta_minutes": str(location_data.get("eta_minutes"))
        }
        
        import asyncio
        result = asyncio.run(_send_push_notification(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data,
            icon="📍"
        ))
        
        return {
            "success": True,
            "message": "Location update push notification sent",
            "trip_id": location_data.get("trip_id"),
            "sent_count": result.get("success_count", 0),
            "failed_count": result.get("failure_count", 0)
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send location update push: {str(exc)}",
            "trip_id": location_data.get("trip_id")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_status_push(
    self,
    device_tokens: List[str],
    payment_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send push notification for payment status updates.
    
    Args:
        device_tokens: List of FCM device tokens
        payment_data: Dictionary containing payment details
        
    Returns:
        Dict with success status and message
    """
    try:
        status = payment_data.get("status")
        amount = payment_data.get("amount")
        booking_ref = payment_data.get("booking_reference")
        
        if status == "completed":
            title = "Payment Successful ✅"
            body = f"Payment of ${amount} completed for booking {booking_ref}"
            icon = "✅"
        elif status == "failed":
            title = "Payment Failed ❌"
            body = f"Payment of ${amount} failed for booking {booking_ref}. Please try again."
            icon = "❌"
        elif status == "refunded":
            title = "Refund Processed 💰"
            body = f"Refund of ${amount} processed for booking {booking_ref}"
            icon = "💰"
        else:
            title = "Payment Update"
            body = f"Payment status update for booking {booking_ref}"
            icon = "💳"
        
        data = {
            "type": "payment_status",
            "payment_id": payment_data.get("payment_id"),
            "booking_reference": booking_ref,
            "status": status,
            "amount": str(amount)
        }
        
        import asyncio
        result = asyncio.run(_send_push_notification(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data,
            icon=icon
        ))
        
        return {
            "success": True,
            "message": f"Payment status push notification sent for {status}",
            "payment_id": payment_data.get("payment_id"),
            "sent_count": result.get("success_count", 0),
            "failed_count": result.get("failure_count", 0)
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send payment status push: {str(exc)}",
            "payment_id": payment_data.get("payment_id")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_promotional_push(
    self,
    device_tokens: List[str],
    promotion_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send promotional push notifications.
    
    Args:
        device_tokens: List of FCM device tokens
        promotion_data: Dictionary containing promotion details
        
    Returns:
        Dict with success status and message
    """
    try:
        title = promotion_data.get("title", "Special Offer! 🎉")
        body = promotion_data.get("message")
        
        data = {
            "type": "promotion",
            "promotion_id": promotion_data.get("promotion_id"),
            "discount_code": promotion_data.get("discount_code"),
            "valid_until": promotion_data.get("valid_until")
        }
        
        import asyncio
        result = asyncio.run(_send_push_notification(
            device_tokens=device_tokens,
            title=title,
            body=body,
            data=data,
            icon="🎉"
        ))
        
        return {
            "success": True,
            "message": "Promotional push notification sent",
            "promotion_id": promotion_data.get("promotion_id"),
            "sent_count": result.get("success_count", 0),
            "failed_count": result.get("failure_count", 0)
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send promotional push: {str(exc)}",
            "promotion_id": promotion_data.get("promotion_id")
        }


async def _send_push_notification(
    device_tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    icon: Optional[str] = None
) -> Dict[str, Any]:
    """
    Internal function to send push notifications via Firebase FCM.
    
    Args:
        device_tokens: List of FCM device tokens
        title: Notification title
        body: Notification body
        data: Optional data payload
        icon: Optional icon/emoji
        
    Returns:
        Dict with FCM response details
    """
    if not settings.FIREBASE_CREDENTIALS_PATH:
        raise ValueError("Firebase credentials not configured")
    
    # This is a simplified example. In production, you would use the Firebase Admin SDK
    # or make direct HTTP requests to FCM API
    
    fcm_url = "https://fcm.googleapis.com/fcm/send"
    
    # Load Firebase service account key (in production, use proper credential management)
    try:
        with open(settings.FIREBASE_CREDENTIALS_PATH, 'r') as f:
            credentials = json.load(f)
        
        # In a real implementation, you'd use Firebase Admin SDK to get an access token
        # For now, this is a placeholder structure
        
        success_count = 0
        failure_count = 0
        
        # Send to each device token (in production, use batch sending)
        for token in device_tokens:
            payload = {
                "to": token,
                "notification": {
                    "title": title,
                    "body": body,
                    "icon": icon or "default"
                },
                "data": data or {}
            }
            
            headers = {
                "Authorization": f"key={credentials.get('server_key')}",  # Placeholder
                "Content-Type": "application/json"
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        fcm_url,
                        json=payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        failure_count += 1
                        
            except Exception as e:
                failure_count += 1
                print(f"Failed to send push to token {token}: {e}")
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "total_tokens": len(device_tokens)
        }
        
    except Exception as e:
        raise Exception(f"Failed to send push notifications: {str(e)}")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_push_notification(
    self,
    notification_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send bulk push notifications to multiple users.
    
    Args:
        notification_data: Dictionary containing bulk notification details
        
    Returns:
        Dict with success status and statistics
    """
    try:
        user_tokens = notification_data.get("user_tokens", {})  # {user_id: [tokens]}
        title = notification_data.get("title")
        body = notification_data.get("body")
        data = notification_data.get("data", {})
        
        total_users = len(user_tokens)
        total_tokens = sum(len(tokens) for tokens in user_tokens.values())
        success_count = 0
        failure_count = 0
        
        for user_id, tokens in user_tokens.items():
            try:
                result = asyncio.run(_send_push_notification(
                    device_tokens=tokens,
                    title=title,
                    body=body,
                    data=data
                ))
                success_count += result.get("success_count", 0)
                failure_count += result.get("failure_count", 0)
                
            except Exception as e:
                failure_count += len(tokens)
                print(f"Failed to send bulk push to user {user_id}: {e}")
        
        return {
            "success": True,
            "message": "Bulk push notification completed",
            "total_users": total_users,
            "total_tokens": total_tokens,
            "success_count": success_count,
            "failure_count": failure_count
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send bulk push notification: {str(exc)}"
        }