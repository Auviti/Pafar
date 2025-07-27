"""
Test receipt generator functionality.
"""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.utils.receipt_generator import ReceiptGenerator
from app.schemas.payment import PaymentReceiptData


def test_receipt_generator():
    """Test receipt generation functionality."""
    
    # Create sample receipt data
    receipt_data = PaymentReceiptData(
        payment_id=uuid4(),
        booking_reference="BK123456",
        passenger_name="John Doe",
        passenger_email="john@example.com",
        trip_details={
            "departure_time": "2024-01-15T10:00:00",
            "route": "Central Station to North Station",
            "bus": "ABC-123",
            "seats": [1, 2]
        },
        amount=Decimal("50.00"),
        currency="USD",
        payment_method="card",
        transaction_id="pi_test123",
        payment_date=datetime.utcnow()
    )
    
    # Test HTML receipt generation
    html_receipt = ReceiptGenerator.generate_html_receipt(receipt_data)
    assert "PAFAR TRANSPORT" in html_receipt
    assert "BK123456" in html_receipt
    assert "John Doe" in html_receipt
    assert "50.00" in html_receipt
    print("✓ HTML receipt generated successfully")
    
    # Test text receipt generation
    text_receipt = ReceiptGenerator.generate_text_receipt(receipt_data)
    assert "PAFAR TRANSPORT" in text_receipt
    assert "BK123456" in text_receipt
    assert "John Doe" in text_receipt
    assert "50.00" in text_receipt
    print("✓ Text receipt generated successfully")
    
    # Test receipt summary
    summary = ReceiptGenerator.generate_receipt_summary(receipt_data)
    assert summary["booking_reference"] == "BK123456"
    assert summary["passenger_name"] == "John Doe"
    assert summary["amount"] == 50.00
    assert summary["status"] == "confirmed"
    print("✓ Receipt summary generated successfully")
    
    print("\n🎉 Receipt generator test passed!")


if __name__ == "__main__":
    test_receipt_generator()