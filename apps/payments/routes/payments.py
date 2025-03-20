from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.models.payment import PaymentCreate, PaymentRead, PaymentStatus
from sqlalchemy.ext.asyncio import AsyncSession
from app.payment.services.payments import create_payment, get_payment_by_id, get_payments_by_order, update_payment_status, refund_payment
from core.database import get_db1  # Assume get_db provides AsyncSession


router = APIRouter()

# Route to create a new payment
@router.post("/payments/", response_model=PaymentRead)
async def create_payment_route(payment: PaymentCreate, db: AsyncSession = Depends(get_d1b)):
    created_payment = await create_payment(
        db=db,
        order_id=payment.order_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        payment_status=payment.payment_status,
        payment_gateway=payment.payment_gateway,
        transaction_id=payment.transaction_id,
        currency=payment.currency,
        billing_address=payment.billing_address,
        discount_code=payment.discount_code,
        ip_address=payment.ip_address
    )
    return created_payment

# Route to get a payment by its ID
@router.get("/payments/{payment_id}", response_model=PaymentRead)
async def get_payment_route(payment_id: UUID, db: AsyncSession = Depends(get_db1)):
    return await get_payment_by_id(db=db, payment_id=payment_id)

# Route to get payments by order ID
@router.get("/payments/order/{order_id}", response_model=list[PaymentRead])
async def get_payments_by_order_route(order_id: UUID, db: AsyncSession = Depends(get_db1)):
    return await get_payments_by_order(db=db, order_id=order_id)

# Route to update the payment status
@router.put("/payments/{payment_id}/status", response_model=PaymentRead)
async def update_payment_status_route(payment_id: UUID, payment_status: PaymentStatus, db: AsyncSession = Depends(get_db1)):
    return await update_payment_status(db=db, payment_id=payment_id, payment_status=payment_status)

# Route to refund a payment
@router.put("/payments/{payment_id}/refund", response_model=PaymentRead)
async def refund_payment_route(payment_id: UUID, refunded_amount: float, db: AsyncSession = Depends(get_db1)):
    return await refund_payment(db=db, payment_id=payment_id, refunded_amount=refunded_amount)
