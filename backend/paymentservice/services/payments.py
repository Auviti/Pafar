from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
import json
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi import HTTPException
from typing import List
from models.currency import Currency
from models.payments import PaymentMethod, Payment, PaymentStatus
from schemas.payments import PaymentMethodCreate, PaymentMethodOut, PaymentCreate, PaymentOut


# Service for PaymentMethod
class PaymentMethodService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_method(self, payment_method: PaymentMethodCreate) -> PaymentMethodOut:
        """Create a new payment method."""
        try:
            db_payment_method = PaymentMethod(
                name=payment_method.name,
                description=payment_method.description,
                payment_type=payment_method.payment_type
            )
            self.db.add(db_payment_method)
            await self.db.commit()
            await self.db.refresh(db_payment_method)
            return PaymentMethodOut.from_orm(db_payment_method)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_payment_methods(self) -> List[PaymentMethodOut]:
        """Fetch all payment methods."""
        try:
            result = await self.db.execute(select(PaymentMethod))
            payment_methods = result.scalars().all()
            return [PaymentMethodOut.from_orm(pm) for pm in payment_methods]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_payment_method_by_id(self, payment_method_id: UUID) -> PaymentMethodOut:
        """Fetch a payment method by ID."""
        try:
            result = await self.db.execute(select(PaymentMethod).filter(PaymentMethod.id == payment_method_id))
            payment_method = result.scalar_one_or_none()
            if not payment_method:
                raise HTTPException(status_code=404, detail=f"PaymentMethod with ID {payment_method_id} not found")
            return PaymentMethodOut.from_orm(payment_method)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))


# Service for Payment
class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
   
    async def create_payment(self, payment: PaymentCreate, idempotency_key: str):
        """Create a new payment."""
        # Check if the idempotency key already exists in the database
        existing_key = await self.db.execute(select(IdempotencyKey).filter_by(id=idempotency_key))
        existing_key = existing_key.scalar_one_or_none()

        if existing_key:
            # If the idempotency key exists, return the previously stored response
            return json.loads(existing_key.response)
        try:
            db_payment = Payment(
                booking_id=payment.booking_id,
                reason=payment.reason,
                amount=payment.amount,
                payment_method_id=payment.payment_method_id,
                payment_status=payment.payment_status,
                payment_gateway=payment.payment_gateway,
                transaction_id=payment.transaction_id,
                currency=payment.currency,
                billing_address=payment.billing_address,
                discount_code=payment.discount_code,
                refunded_amount=payment.refunded_amount,
                is_refunded=payment.is_refunded,
                ip_address=payment.ip_address
            )
            self.db.add(db_payment)
            await self.db.commit()
            await self.db.refresh(db_payment)
            # Process the payment (simulated)
            # For example, here you might call an external payment gateway to process the payment.
            payment_status = PaymentStatus.COMPLETED  # Assume the payment was successful

            # Update the payment status
            db_payment.payment_status = payment_status
            await self.db.commit()

            # Store the idempotency key with the response
            idempotency_record = IdempotencyKey(
                id=idempotency_key,
                response=json.dumps(PaymentMethodOut.from_orm(db_payment).dict())
            )
            self.db.add(idempotency_record)
            await self.db.commit()

            return PaymentOut.from_orm(db_payment)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_payments(self) -> List[PaymentOut]:
        """Fetch all payments."""
        try:
            result = await self.db.execute(select(Payment))
            payments = result.scalars().all()
            return [PaymentOut.from_orm(payment) for payment in payments]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_payment_by_id(self, payment_id: UUID) -> PaymentOut:
        """Fetch a payment by ID."""
        try:
            result = await self.db.execute(select(Payment).filter(Payment.id == payment_id))
            payment = result.scalar_one_or_none()
            if not payment:
                raise HTTPException(status_code=404, detail=f"Payment with ID {payment_id} not found")
            return PaymentOut.from_orm(payment)
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def update_payment_status(self, payment_id: UUID, status: PaymentStatus) -> PaymentOut:
        """Update the status of a payment."""
        try:
            result = await self.db.execute(select(Payment).filter(Payment.id == payment_id))
            payment = result.scalar_one_or_none()
            if not payment:
                raise HTTPException(status_code=404, detail=f"Payment with ID {payment_id} not found")

            payment.payment_status = status
            await self.db.commit()
            await self.db.refresh(payment)
            return PaymentOut.from_orm(payment)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
