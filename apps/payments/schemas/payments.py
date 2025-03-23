from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from enum import Enum

class PaymentTypeEnum(str, Enum):
    CASH = "Cash"
    PAYNOW = "Paynow"
    EWALLET = "EWallet"
    CRYPTO = "Crypto"

class PaymentMethodBase(BaseModel):
    name: str
    description: Optional[str] = None  # Optional field for description
    payment_type:PaymentTypeEnum

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodOut(PaymentMethodBase):
    id: UUID  # This field will be used for the response output

    class Config:
        from_attributes = True  # Allows interaction with SQLAlchemy models to auto-map fields # Ensure the ORM model can be serialized


class PaymentStatusEnum(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"
    REFUNDED = "Refunded"
    CANCELLED = "Cancelled"

class PaymentBase(BaseModel):
    booking_id: UUID
    reason: str
    amount: float
    payment_method_id: UUID
    payment_status: PaymentStatusEnum
    payment_gateway: str
    transaction_id: str
    currency: str  # You might need to adjust this based on how your `Currency` model is structured
    billing_address: Optional[str] = None
    discount_code: Optional[str] = None
    refunded_amount: float = 0.0
    is_refunded: bool = False
    ip_address: str

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase):
    id: UUID
    payment_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True  # Allows interaction with SQLAlchemy models to auto-map fields # Ensure the ORM model can be serialized


