from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Float, JSON, UUID
from core.database import Base, CHAR_LENGTH
from sqlalchemy.orm import mapped_column, relationship
from datetime import datetime
import enum
import sys
from apps.products.models.currency import Currency
from apps.products.models.category import UUIDType,mappeditem,default

# # Database type detection
# if 'postgresql' in sys.argv:
#     # Use native UUID for PostgreSQL
#     UUIDType = UUID(as_uuid=True)
#     mappeditem = UUID
#     default = uuid4
# else:
#     # Use string representation for other databases
#     UUIDType = String(36)
#     mappeditem = str
#     default = lambda: str(uuid4())

# Enum for Payment Methods
class PaymentMethod(enum.Enum):
    CREDIT_CARD = "Credit Card"
    PAYPAL = "PayPal"
    BANK_TRANSFER = "Bank Transfer"
    CASH_ON_DELIVERY = "Cash on Delivery"
    GIFT_CARD = "Gift Card"

# Enum for Payment Status
class PaymentStatus(enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"
    REFUNDED = "Refunded"
    CANCELLED = "Cancelled"

class Payment(Base):
    __tablename__ = 'payments'

    # Using mapped_column instead of Column for attributes
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    amount: Mapped[Float] = mapped_column(Float, nullable=False)  # Total amount paid
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)  # Payment method (credit card, PayPal, etc.)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False)  # Payment status (pending, completed, etc.)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Date and time of the payment
    payment_gateway: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # Payment gateway used (PayPal, Stripe, etc.)
    transaction_id: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, nullable=False)  # Unique transaction ID from payment provider
    currency: Mapped[str] = mapped_column(ForeignKey("currency.symbol"), nullable=False)  # ForeignKey referencing user (UUID)
    billing_address: Mapped[str] = mapped_column(String(CHAR_LENGTH))  # Billing address (optional, could be JSON or separate table)
    discount_code: Mapped[str] = mapped_column(String(CHAR_LENGTH))  # Discount applied (if any)
    refunded_amount: Mapped[Float] = mapped_column(Float, default=0.0)  # Refunds, if any, applied to the payment
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)  # Flag if the payment was refunded
    ip_address: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # IP address of the customer (IPv4/IPv6)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # When the product was created
    
    # Relationship to Order (assuming the Order model exists)
    order: relationship("Order", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, amount={self.amount}, status={self.payment_status}, date={self.payment_date}, ip={self.ip_address})>"

# # Assuming you have an Order model that has a relationship with payments:
# class Order(Base):
#     __tablename__ = 'orders'

#     id: int = mapped_column(Integer, primary_key=True)  # Order ID
#     user_id: int = mapped_column(Integer, ForeignKey('users.id'), nullable=False)  # Link to User
#     total_amount: float = mapped_column(Float, nullable=False)  # Total amount for the order
#     status: str = mapped_column(String(50), nullable=False)  # Status of the order (pending, completed, etc.)
#     created_at: datetime = mapped_column(DateTime, default=datetime.utcnow)  # Date and time the order was created

#     # Relationship to Payment (One Order can have multiple payments)
#     payments: relationship('Payment', back_populates='order')

#     def __repr__(self):
#         return f"<Order(id={self.id}, user_id={self.user_id}, total_amount={self.total_amount}, status={self.status})>"

