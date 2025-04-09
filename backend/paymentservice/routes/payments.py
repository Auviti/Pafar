from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db1  # Assume get_db provides AsyncSession
from app.payments.schemas.payments import PaymentMethodCreate, PaymentMethodOut, PaymentCreate, PaymentOut
from app.payments.services.payments import PaymentMethodService, PaymentService
from app.payments.models.payments import PaymentStatus

router = APIRouter()

# Routes for PaymentMethod
@router.post("/payment_methods/", response_model=PaymentMethodOut)
async def create_payment_method(payment_method: PaymentMethodCreate, db: AsyncSession = Depends(get_db1)):
    """Create a new payment method."""
    service = PaymentMethodService(db)
    return await service.create_payment_method(payment_method)

@router.get("/payment_methods/", response_model=List[PaymentMethodOut])
async def get_payment_methods(db: AsyncSession = Depends(get_db1)):
    """Get all payment methods."""
    service = PaymentMethodService(db)
    return await service.get_payment_methods()

@router.get("/payment_methods/{payment_method_id}", response_model=PaymentMethodOut)
async def get_payment_method(payment_method_id: UUID, db: AsyncSession = Depends(get_db1)):
    """Get a payment method by ID."""
    service = PaymentMethodService(db)
    return await service.get_payment_method_by_id(payment_method_id)


# Routes for Payment
@router.post("/payments/", response_model=PaymentOut)
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db1)):
    """Create a new payment."""
    service = PaymentService(db)
    return await service.create_payment(payment)

@router.get("/payments/", response_model=List[PaymentOut])
async def get_payments(db: AsyncSession = Depends(get_db1)):
    """Get all payments."""
    service = PaymentService(db)
    return await service.get_payments()

@router.get("/payments/{payment_id}", response_model=PaymentOut)
async def get_payment(payment_id: UUID, db: AsyncSession = Depends(get_db1)):
    """Get a payment by ID."""
    service = PaymentService(db)
    return await service.get_payment_by_id(payment_id)

@router.put("/payments/{payment_id}/status", response_model=PaymentOut)
async def update_payment_status(payment_id: UUID, status: PaymentStatus, db: AsyncSession = Depends(get_db1)):
    """Update the status of a payment."""
    service = PaymentService(db)
    return await service.update_payment_status(payment_id, status)
