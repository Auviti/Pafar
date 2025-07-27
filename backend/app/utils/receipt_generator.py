"""
E-receipt generation utilities for payment confirmations.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from jinja2 import Template

from app.schemas.payment import PaymentReceiptData

logger = logging.getLogger(__name__)


class ReceiptGenerator:
    """Utility class for generating e-receipts."""
    
    # HTML template for e-receipt
    RECEIPT_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Payment Receipt - {{ booking_reference }}</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            .header {
                text-align: center;
                border-bottom: 2px solid #007bff;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .logo {
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
                margin-bottom: 10px;
            }
            .receipt-title {
                font-size: 18px;
                color: #666;
            }
            .section {
                margin-bottom: 25px;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .section-title {
                font-size: 16px;
                font-weight: bold;
                color: #007bff;
                margin-bottom: 10px;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 5px;
            }
            .info-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                padding: 5px 0;
            }
            .info-label {
                font-weight: bold;
                color: #666;
            }
            .info-value {
                color: #333;
            }
            .amount {
                font-size: 20px;
                font-weight: bold;
                color: #28a745;
            }
            .status {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                background-color: #28a745;
                color: white;
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                color: #666;
                font-size: 12px;
            }
            .seats {
                display: inline-block;
                background-color: #007bff;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                margin: 2px;
                font-size: 12px;
            }
            @media print {
                body { margin: 0; }
                .no-print { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">PAFAR TRANSPORT</div>
            <div class="receipt-title">Payment Receipt</div>
        </div>
        
        <div class="section">
            <div class="section-title">Booking Information</div>
            <div class="info-row">
                <span class="info-label">Booking Reference:</span>
                <span class="info-value">{{ booking_reference }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Passenger Name:</span>
                <span class="info-value">{{ passenger_name }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Email:</span>
                <span class="info-value">{{ passenger_email }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="status">Confirmed</span>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Trip Details</div>
            <div class="info-row">
                <span class="info-label">Route:</span>
                <span class="info-value">{{ trip_details.route }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Departure:</span>
                <span class="info-value">{{ trip_details.departure_time | format_datetime }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Bus:</span>
                <span class="info-value">{{ trip_details.bus }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Seats:</span>
                <span class="info-value">
                    {% for seat in trip_details.seats %}
                        <span class="seats">{{ seat }}</span>
                    {% endfor %}
                </span>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Payment Information</div>
            <div class="info-row">
                <span class="info-label">Amount Paid:</span>
                <span class="info-value amount">{{ currency }} {{ amount }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Payment Method:</span>
                <span class="info-value">{{ payment_method | title }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Transaction ID:</span>
                <span class="info-value">{{ transaction_id }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Payment Date:</span>
                <span class="info-value">{{ payment_date | format_datetime }}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>Thank you for choosing Pafar Transport!</p>
            <p>This is an electronic receipt. Please keep it for your records.</p>
            <p>For support, contact us at support@pafar.com or +1-800-PAFAR</p>
            <p>Generated on {{ current_date | format_datetime }}</p>
        </div>
    </body>
    </html>
    """
    
    @classmethod
    def generate_html_receipt(cls, receipt_data: PaymentReceiptData) -> str:
        """
        Generate HTML e-receipt from payment data.
        
        Args:
            receipt_data: Payment receipt data
            
        Returns:
            HTML string for the receipt
        """
        try:
            # Add custom filters for formatting
            def format_datetime(dt):
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return dt.strftime("%B %d, %Y at %I:%M %p")
            
            # Create Jinja2 environment with custom filter
            from jinja2 import Environment
            env = Environment()
            env.filters['format_datetime'] = format_datetime
            template = env.from_string(cls.RECEIPT_TEMPLATE)
            
            # Render the template
            html_content = template.render(
                booking_reference=receipt_data.booking_reference,
                passenger_name=receipt_data.passenger_name,
                passenger_email=receipt_data.passenger_email,
                trip_details=receipt_data.trip_details,
                amount=receipt_data.amount,
                currency=receipt_data.currency,
                payment_method=receipt_data.payment_method,
                transaction_id=receipt_data.transaction_id,
                payment_date=receipt_data.payment_date,
                current_date=datetime.utcnow()
            )
            
            logger.info(f"Generated HTML receipt for booking {receipt_data.booking_reference}")
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML receipt: {str(e)}")
            raise
    
    @classmethod
    def generate_text_receipt(cls, receipt_data: PaymentReceiptData) -> str:
        """
        Generate plain text e-receipt from payment data.
        
        Args:
            receipt_data: Payment receipt data
            
        Returns:
            Plain text string for the receipt
        """
        try:
            # Format datetime
            def format_dt(dt):
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return dt.strftime("%B %d, %Y at %I:%M %p")
            
            # Format seats
            seats_str = ", ".join(map(str, receipt_data.trip_details.get('seats', [])))
            
            text_content = f"""
PAFAR TRANSPORT - PAYMENT RECEIPT
{'=' * 50}

BOOKING INFORMATION
Booking Reference: {receipt_data.booking_reference}
Passenger Name: {receipt_data.passenger_name}
Email: {receipt_data.passenger_email}
Status: CONFIRMED

TRIP DETAILS
Route: {receipt_data.trip_details.get('route', 'N/A')}
Departure: {format_dt(receipt_data.trip_details.get('departure_time', ''))}
Bus: {receipt_data.trip_details.get('bus', 'N/A')}
Seats: {seats_str}

PAYMENT INFORMATION
Amount Paid: {receipt_data.currency} {receipt_data.amount}
Payment Method: {receipt_data.payment_method.title()}
Transaction ID: {receipt_data.transaction_id}
Payment Date: {format_dt(receipt_data.payment_date)}

{'=' * 50}
Thank you for choosing Pafar Transport!

This is an electronic receipt. Please keep it for your records.
For support, contact us at support@pafar.com or +1-800-PAFAR

Generated on {format_dt(datetime.utcnow())}
            """.strip()
            
            logger.info(f"Generated text receipt for booking {receipt_data.booking_reference}")
            return text_content
            
        except Exception as e:
            logger.error(f"Error generating text receipt: {str(e)}")
            raise
    
    @classmethod
    def generate_receipt_summary(cls, receipt_data: PaymentReceiptData) -> Dict[str, Any]:
        """
        Generate a summary dictionary for the receipt.
        
        Args:
            receipt_data: Payment receipt data
            
        Returns:
            Dictionary with receipt summary
        """
        try:
            return {
                "booking_reference": receipt_data.booking_reference,
                "passenger_name": receipt_data.passenger_name,
                "amount": float(receipt_data.amount),
                "currency": receipt_data.currency,
                "payment_method": receipt_data.payment_method,
                "transaction_id": receipt_data.transaction_id,
                "payment_date": receipt_data.payment_date.isoformat(),
                "trip_route": receipt_data.trip_details.get('route'),
                "seats": receipt_data.trip_details.get('seats', []),
                "status": "confirmed"
            }
            
        except Exception as e:
            logger.error(f"Error generating receipt summary: {str(e)}")
            raise