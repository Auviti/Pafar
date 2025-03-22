from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Float, JSON, UUID
from core.database import Base, CHAR_LENGTH
from sqlalchemy.orm import mapped_column, relationship
from datetime import datetime
import enum
import sys
from apps.payments.models.currency import Currency

# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())

class PaymentMethod(Base):
    __tablename__ = 'payment_methods'

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)  # Optional description of the payment method

    # Relationship back to Payment model
    payments: Mapped["Payment"] = relationship("Payment", back_populates="payment_method")

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, name={self.name}, description={self.description})>"


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
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id"), nullable=False)  # Link to booking
    reason: Mapped[str] = mapped_column(String(255), nullable=False)  # Reason for payment
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Total amount paid
    payment_method_id: Mapped[UUID] = mapped_column(ForeignKey("payment_methods.id"), nullable=False)  # Foreign key to PaymentMethod model
    payment_status: Mapped[str] = mapped_column(Enum(PaymentStatus), nullable=False)  # Payment status (pending, completed, etc.)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Date and time of the payment
    payment_gateway: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # Payment gateway used (PayPal, Stripe, etc.)
    transaction_id: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, nullable=False)  # Unique transaction ID from payment provider
    currency: Mapped[str] = mapped_column(ForeignKey("currency.symbol"), nullable=False)  # ForeignKey referencing Currency model
    billing_address: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Billing address (optional, could be JSON or separate table)
    discount_code: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Discount applied (if any)
    refunded_amount: Mapped[float] = mapped_column(Float, default=0.0)  # Refunds, if any, applied to the payment
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False)  # Flag if the payment was refunded
    ip_address: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=False)  # IP address of the customer (IPv4/IPv6)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # When the payment was created

    # Relationships
    booking: relationship("Booking", back_populates="payments")
    currency_info: relationship("Currency", back_populates="payments")  # Assuming you have Currency model and this relationship defined
    payment_method: relationship("PaymentMethod", back_populates="payments")  # Relationship to the PaymentMethod model

    def __repr__(self):
        return f"<Payment(id={self.id}, booking_id={self.booking_id}, amount={self.amount}, status={self.payment_status}, date={self.payment_date}, ip={self.ip_address})>"
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

