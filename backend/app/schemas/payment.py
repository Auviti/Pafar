"""
Payment Pydantic schemas for request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, validator
from ..models.payment import PaymentStatus


class PaymentBase(BaseModel):
    """Base payment schema."""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class PaymentCreate(PaymentBase):
    """Schema for payment creation."""
    ride_id: UUID
    payment_method_id: str = Field(..., min_length=1, max_length=255)
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate payment amount is reasonable."""
        if v > 10000:  # $10,000 max payment
            raise ValueError('Payment amount cannot exceed $10,000')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        if v.upper() not in valid_currencies:
            raise ValueError(f'Currency must be one of: {", ".join(valid_currencies)}')
        return v.upper()


class PaymentUpdate(BaseModel):
    """Schema for payment updates."""
    status: Optional[PaymentStatus] = None
    stripe_payment_intent_id: Optional[str] = Field(None, max_length=255)


class PaymentResponse(PaymentBase):
    """Schema for payment response."""
    id: UUID
    ride_id: UUID
    user_id: UUID
    payment_method_id: str
    stripe_payment_intent_id: Optional[str] = None
    status: PaymentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentMethodCreate(BaseModel):
    """Schema for creating payment method."""
    type: str = Field(..., pattern="^(card|bank_account)$")
    card_number: Optional[str] = Field(None, min_length=13, max_length=19)
    exp_month: Optional[int] = Field(None, ge=1, le=12)
    exp_year: Optional[int] = Field(None, ge=2024, le=2050)
    cvc: Optional[str] = Field(None, min_length=3, max_length=4)
    
    @validator('card_number')
    def validate_card_number(cls, v):
        """Validate card number format."""
        if v is not None:
            # Remove spaces and dashes
            cleaned = ''.join(c for c in v if c.isdigit())
            if len(cleaned) < 13 or len(cleaned) > 19:
                raise ValueError('Card number must be between 13 and 19 digits')
        return v


class PaymentMethodResponse(BaseModel):
    """Schema for payment method response."""
    id: str
    type: str
    last4: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False
    
    class Config:
        from_attributes = True


class RefundCreate(BaseModel):
    """Schema for refund creation."""
    payment_id: UUID
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    reason: str = Field(..., min_length=5, max_length=500)


class RefundResponse(BaseModel):
    """Schema for refund response."""
    id: str
    payment_id: UUID
    amount: Decimal
    reason: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True