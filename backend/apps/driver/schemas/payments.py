from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import Optional

# Enum for Payment Methods
class PaymentMethodEnum(str, Enum):
    CREDIT_CARD = "Credit Card"
    PAYPAL = "PayPal"
    BANK_TRANSFER = "Bank Transfer"
    CASH_ON_DELIVERY = "Cash on Delivery"
    GIFT_CARD = "Gift Card"

# Enum for Payment Status
class PaymentStatusEnum(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"
    REFUNDED = "Refunded"
    CANCELLED = "Cancelled"

# Pydantic model for Payment
class PaymentBase(BaseModel):
    order_id: UUID
    amount: float
    payment_method: PaymentMethodEnum
    payment_status: PaymentStatusEnum
    payment_gateway: str
    transaction_id: str
    currency: str
    billing_address: Optional[str] = None
    discount_code: Optional[str] = None
    refunded_amount: float = 0.0
    is_refunded: bool = False
    ip_address: str
    created_at: Optional[datetime] = None  # Automatically set if not provided

    class Config:
        from_attributes = True  # Allows interaction with SQLAlchemy models to auto-map fields  # Tells Pydantic to treat ORM models (like SQLAlchemy models) as dictionaries

# Schema for creating a new Payment
class PaymentCreate(PaymentBase):
    pass

# Schema for reading Payment data (with an id)
class PaymentRead(PaymentBase):
    id: UUID

    class Config:
        from_attributes = True  # Allows interaction with SQLAlchemy models to auto-map fields # Ensure the ORM model can be serialized
