"""
Pydantic schemas for payment operations.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator
from app.models.payment import PaymentStatus, PaymentMethod, PaymentGateway


class PaymentMethodTokenCreate(BaseModel):
    """Schema for creating a payment method token."""
    card_number: str = Field(..., min_length=13, max_length=19)
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int = Field(..., ge=2024)
    cvc: str = Field(..., min_length=3, max_length=4)
    cardholder_name: str = Field(..., min_length=2, max_length=100)
    
    @validator('card_number')
    def validate_card_number(cls, v):
        # Remove spaces and validate format
        card_number = v.replace(' ', '').replace('-', '')
        if not card_number.isdigit():
            raise ValueError('Card number must contain only digits')
        return card_number
    
    @validator('cvc')
    def validate_cvc(cls, v):
        if not v.isdigit():
            raise ValueError('CVC must contain only digits')
        return v


class PaymentMethodToken(BaseModel):
    """Schema for payment method token response."""
    token_id: str
    last_four: str
    brand: str
    exp_month: int
    exp_year: int
    created_at: datetime


class PaymentIntentCreate(BaseModel):
    """Schema for creating a payment intent."""
    booking_id: UUID
    payment_method_token: Optional[str] = None
    save_payment_method: bool = False
    return_url: Optional[str] = None


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response."""
    payment_intent_id: str
    client_secret: str
    amount: Decimal
    currency: str
    status: str
    requires_action: bool = False
    next_action: Optional[Dict[str, Any]] = None


class PaymentConfirmation(BaseModel):
    """Schema for payment confirmation."""
    payment_intent_id: str
    payment_method_id: Optional[str] = None


class PaymentCreate(BaseModel):
    """Schema for creating a payment record."""
    booking_id: UUID
    amount: Decimal
    currency: str = "USD"
    payment_method: PaymentMethod
    payment_gateway: PaymentGateway
    gateway_transaction_id: Optional[str] = None


class PaymentUpdate(BaseModel):
    """Schema for updating payment status."""
    status: PaymentStatus
    gateway_transaction_id: Optional[str] = None
    processed_at: Optional[datetime] = None


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: UUID
    booking_id: UUID
    amount: Decimal
    currency: str
    payment_method: Optional[PaymentMethod] = None
    payment_gateway: Optional[PaymentGateway] = None
    gateway_transaction_id: Optional[str] = None
    status: PaymentStatus
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PaymentReceiptData(BaseModel):
    """Schema for payment receipt data."""
    payment_id: UUID
    booking_reference: str
    passenger_name: str
    passenger_email: str
    trip_details: Dict[str, Any]
    amount: Decimal
    currency: str
    payment_method: str
    transaction_id: str
    payment_date: datetime


class PaymentWebhookEvent(BaseModel):
    """Schema for payment webhook events."""
    event_type: str
    payment_intent_id: str
    status: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentRetryRequest(BaseModel):
    """Schema for payment retry request."""
    payment_id: UUID
    payment_method_token: Optional[str] = None


class SavedPaymentMethod(BaseModel):
    """Schema for saved payment method."""
    id: str
    last_four: str
    brand: str
    exp_month: int
    exp_year: int
    is_default: bool = False
    created_at: datetime


class PaymentMethodList(BaseModel):
    """Schema for payment method list response."""
    payment_methods: list[SavedPaymentMethod]
    total: int