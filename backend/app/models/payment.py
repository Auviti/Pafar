"""
Payment model for transaction tracking and processing.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CASH = "cash"


class PaymentGateway(str, enum.Enum):
    """Payment gateway enumeration."""
    STRIPE = "stripe"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    MANUAL = "manual"


class Payment(Base):
    """Payment model for transaction tracking."""
    
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    payment_gateway = Column(Enum(PaymentGateway), nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, booking={self.booking_id}, amount={self.amount}, status={self.status})>"