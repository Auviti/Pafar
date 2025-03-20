from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime
from app.payments.models.payments import Payment, PaymentMethod, PaymentStatus
from app.products.models.currency import Currency
from app.products.models.order import Order
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Service to create a new payment
async def create_payment(db: AsyncSession, order_id: UUID, amount: float, payment_method: PaymentMethod, payment_status: PaymentStatus,
                         payment_gateway: str, transaction_id: str, currency: str, billing_address: str,
                         discount_code: str, ip_address: str) -> Payment:
    try:
        # Create the payment instance
        payment = Payment(
            order_id=order_id,
            amount=amount,
            payment_method=payment_method,
            payment_status=payment_status,
            payment_gateway=payment_gateway,
            transaction_id=transaction_id,
            currency=currency,
            billing_address=billing_address,
            discount_code=discount_code,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )

        # Add payment to the database
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment
    except SQLAlchemyError as e:
        # Handle the error if something goes wrong
        raise HTTPException(status_code=400, detail=str(e))

# Service to get a payment by its ID
async def get_payment_by_id(db: AsyncSession, payment_id: UUID) -> Payment:
    try:
        result = await db.execute(select(Payment).filter(Payment.id == payment_id))
        payment = result.scalars().first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return payment
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get all payments for a specific order
async def get_payments_by_order(db: AsyncSession, order_id: UUID) -> list[Payment]:
    try:
        result = await db.execute(select(Payment).filter(Payment.order_id == order_id))
        payments = result.scalars().all()
        return payments
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to update payment status
async def update_payment_status(db: AsyncSession, payment_id: UUID, payment_status: PaymentStatus) -> Payment:
    try:
        payment = await get_payment_by_id(db, payment_id)
        payment.payment_status = payment_status
        await db.commit()
        await db.refresh(payment)
        return payment
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to refund a payment
async def refund_payment(db: AsyncSession, payment_id: UUID, refunded_amount: float) -> Payment:
    try:
        payment = await get_payment_by_id(db, payment_id)
        if payment.is_refunded:
            raise HTTPException(status_code=400, detail="Payment already refunded")
        
        # Update the refunded amount and mark as refunded
        payment.refunded_amount = refunded_amount
        payment.is_refunded = True
        payment.payment_status = PaymentStatus.REFUNDED
        await db.commit()
        await db.refresh(payment)
        return payment
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
