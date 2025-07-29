"""
Email notification tasks for booking confirmations and updates.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, List
from jinja2 import Template
from celery import current_task
from ..core.celery_app import celery_app
from ..core.config import settings


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_confirmation_email(
    self,
    user_email: str,
    user_name: str,
    booking_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send booking confirmation email to user.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        booking_data: Dictionary containing booking details
        
    Returns:
        Dict with success status and message
    """
    try:
        # Email template for booking confirmation
        template_content = """
        <html>
        <body>
            <h2>Booking Confirmation - {{ booking_reference }}</h2>
            <p>Dear {{ user_name }},</p>
            
            <p>Your booking has been confirmed! Here are your trip details:</p>
            
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>Trip Information</h3>
                <p><strong>Booking Reference:</strong> {{ booking_reference }}</p>
                <p><strong>Route:</strong> {{ origin }} → {{ destination }}</p>
                <p><strong>Departure:</strong> {{ departure_time }}</p>
                <p><strong>Arrival:</strong> {{ arrival_time }}</p>
                <p><strong>Seat Numbers:</strong> {{ seats }}</p>
                <p><strong>Total Amount:</strong> ${{ total_amount }}</p>
                <p><strong>Bus:</strong> {{ bus_info }}</p>
            </div>
            
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>Important Information</h3>
                <ul>
                    <li>Please arrive at the terminal 30 minutes before departure</li>
                    <li>Bring a valid ID for verification</li>
                    <li>Your booking reference is required for boarding</li>
                    <li>You can track your trip in real-time using our app</li>
                </ul>
            </div>
            
            <p>Thank you for choosing Pafar Transport!</p>
            <p>Safe travels!</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This is an automated message. Please do not reply to this email.
                For support, contact us at support@pafar.com
            </p>
        </body>
        </html>
        """
        
        template = Template(template_content)
        html_content = template.render(
            user_name=user_name,
            booking_reference=booking_data.get("booking_reference"),
            origin=booking_data.get("origin"),
            destination=booking_data.get("destination"),
            departure_time=booking_data.get("departure_time"),
            arrival_time=booking_data.get("arrival_time"),
            seats=", ".join(map(str, booking_data.get("seats", []))),
            total_amount=booking_data.get("total_amount"),
            bus_info=booking_data.get("bus_info")
        )
        
        # Send email
        result = _send_email(
            to_email=user_email,
            subject=f"Booking Confirmation - {booking_data.get('booking_reference')}",
            html_content=html_content
        )
        
        return {
            "success": True,
            "message": "Booking confirmation email sent successfully",
            "booking_reference": booking_data.get("booking_reference")
        }
        
    except Exception as exc:
        # Retry on failure
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send booking confirmation email: {str(exc)}",
            "booking_reference": booking_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_booking_cancellation_email(
    self,
    user_email: str,
    user_name: str,
    booking_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send booking cancellation email to user.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        booking_data: Dictionary containing booking details
        
    Returns:
        Dict with success status and message
    """
    try:
        template_content = """
        <html>
        <body>
            <h2>Booking Cancellation - {{ booking_reference }}</h2>
            <p>Dear {{ user_name }},</p>
            
            <p>Your booking has been cancelled as requested.</p>
            
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>Cancelled Trip Details</h3>
                <p><strong>Booking Reference:</strong> {{ booking_reference }}</p>
                <p><strong>Route:</strong> {{ origin }} → {{ destination }}</p>
                <p><strong>Departure:</strong> {{ departure_time }}</p>
                <p><strong>Seat Numbers:</strong> {{ seats }}</p>
                <p><strong>Refund Amount:</strong> ${{ refund_amount }}</p>
            </div>
            
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>Refund Information</h3>
                <p>Your refund of ${{ refund_amount }} will be processed within 3-5 business days 
                   and credited back to your original payment method.</p>
                <p><strong>Refund Reference:</strong> {{ refund_reference }}</p>
            </div>
            
            <p>We're sorry to see you cancel your trip. We hope to serve you again in the future!</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This is an automated message. Please do not reply to this email.
                For support, contact us at support@pafar.com
            </p>
        </body>
        </html>
        """
        
        template = Template(template_content)
        html_content = template.render(
            user_name=user_name,
            booking_reference=booking_data.get("booking_reference"),
            origin=booking_data.get("origin"),
            destination=booking_data.get("destination"),
            departure_time=booking_data.get("departure_time"),
            seats=", ".join(map(str, booking_data.get("seats", []))),
            refund_amount=booking_data.get("refund_amount"),
            refund_reference=booking_data.get("refund_reference")
        )
        
        result = _send_email(
            to_email=user_email,
            subject=f"Booking Cancellation - {booking_data.get('booking_reference')}",
            html_content=html_content
        )
        
        return {
            "success": True,
            "message": "Booking cancellation email sent successfully",
            "booking_reference": booking_data.get("booking_reference")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send booking cancellation email: {str(exc)}",
            "booking_reference": booking_data.get("booking_reference")
        }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_receipt_email(
    self,
    user_email: str,
    user_name: str,
    payment_data: Dict[str, Any],
    receipt_attachment: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Send payment receipt email with PDF attachment.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        payment_data: Dictionary containing payment details
        receipt_attachment: PDF receipt as bytes
        
    Returns:
        Dict with success status and message
    """
    try:
        template_content = """
        <html>
        <body>
            <h2>Payment Receipt - {{ transaction_id }}</h2>
            <p>Dear {{ user_name }},</p>
            
            <p>Thank you for your payment. Your transaction has been processed successfully.</p>
            
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
                <h3>Payment Details</h3>
                <p><strong>Transaction ID:</strong> {{ transaction_id }}</p>
                <p><strong>Booking Reference:</strong> {{ booking_reference }}</p>
                <p><strong>Amount Paid:</strong> ${{ amount }}</p>
                <p><strong>Payment Method:</strong> {{ payment_method }}</p>
                <p><strong>Payment Date:</strong> {{ payment_date }}</p>
                <p><strong>Status:</strong> {{ status }}</p>
            </div>
            
            <p>Please find your detailed receipt attached to this email.</p>
            
            <p>Thank you for choosing Pafar Transport!</p>
            
            <hr>
            <p style="font-size: 12px; color: #666;">
                This is an automated message. Please do not reply to this email.
                For support, contact us at support@pafar.com
            </p>
        </body>
        </html>
        """
        
        template = Template(template_content)
        html_content = template.render(
            user_name=user_name,
            transaction_id=payment_data.get("transaction_id"),
            booking_reference=payment_data.get("booking_reference"),
            amount=payment_data.get("amount"),
            payment_method=payment_data.get("payment_method"),
            payment_date=payment_data.get("payment_date"),
            status=payment_data.get("status")
        )
        
        result = _send_email(
            to_email=user_email,
            subject=f"Payment Receipt - {payment_data.get('transaction_id')}",
            html_content=html_content,
            attachment=receipt_attachment,
            attachment_name=f"receipt_{payment_data.get('transaction_id')}.pdf"
        )
        
        return {
            "success": True,
            "message": "Payment receipt email sent successfully",
            "transaction_id": payment_data.get("transaction_id")
        }
        
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "message": f"Failed to send payment receipt email: {str(exc)}",
            "transaction_id": payment_data.get("transaction_id")
        }


def _send_email(
    to_email: str,
    subject: str,
    html_content: str,
    attachment: Optional[bytes] = None,
    attachment_name: Optional[str] = None
) -> bool:
    """
    Internal function to send email via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email content
        attachment: Optional file attachment as bytes
        attachment_name: Name for the attachment file
        
    Returns:
        True if email sent successfully, False otherwise
    """
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        raise ValueError("SMTP configuration is incomplete")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    
    # Add HTML content
    msg.attach(MIMEText(html_content, 'html'))
    
    # Add attachment if provided
    if attachment and attachment_name:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {attachment_name}'
        )
        msg.attach(part)
    
    # Send email
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_USER, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise