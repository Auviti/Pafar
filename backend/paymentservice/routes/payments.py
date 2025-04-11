from fastapi import APIRouter, Depends
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from core.utils.response import Response
from core.database import get_db1
from schemas.payments import PaymentMethodCreate, PaymentMethodOut, PaymentCreate, PaymentOut
from services.payments import PaymentMethodService, PaymentService
from models.payments import PaymentStatus

router = APIRouter()


# ───── Payment Method Endpoints ──────────────────────────────────────────

@router.post("/payment_methods/")
async def create_payment_method(payment_method: PaymentMethodCreate, db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentMethodService(db)
        result = await service.create_payment_method(payment_method)
        return Response(data=result, message="Payment method created", code=201)
    except Exception as e:
        return Response(message="Failed to create payment method", code=500)

@router.get("/payment_methods/")
async def get_payment_methods(db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentMethodService(db)
        result = await service.get_payment_methods()
        return Response(data=result, message="Payment methods retrieved")
    except Exception as e:
        return Response(message="Failed to fetch payment methods", code=500)

@router.get("/payment_methods/{payment_method_id}")
async def get_payment_method(payment_method_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentMethodService(db)
        result = await service.get_payment_method_by_id(payment_method_id)
        if not result:
            return Response(message="Payment method not found", code=404)
        return Response(data=result, message="Payment method retrieved")
    except Exception as e:
        return Response(message="Failed to fetch payment method", code=500)


# ───── Payment Endpoints ─────────────────────────────────────────────────

@router.post("/payments/{idempotency_key}")
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentService(db)
        result = await service.create_payment(payment,idempotency_key)
        return Response(data=result, message="Payment created", code=201)
    except Exception as e:
        return Response(message="Failed to create payment", code=500)

@router.get("/payments/")
async def get_payments(db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentService(db)
        result = await service.get_payments()
        return Response(data=result, message="Payments retrieved")
    except Exception as e:
        return Response(message="Failed to fetch payments", code=500)

@router.get("/payments/{payment_id}")
async def get_payment(payment_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentService(db)
        result = await service.get_payment_by_id(payment_id)
        if not result:
            return Response(message="Payment not found", code=404)
        return Response(data=result, message="Payment retrieved")
    except Exception as e:
        return Response(message="Failed to fetch payment", code=500)

@router.put("/payments/{payment_id}/status")
async def update_payment_status(payment_id: UUID, status: PaymentStatus, db: AsyncSession = Depends(get_db1)):
    try:
        service = PaymentService(db)
        result = await service.update_payment_status(payment_id, status)
        if not result:
            return Response(message="Payment not found or update failed", code=404)
        return Response(data=result, message="Payment status updated")
    except Exception as e:
        return Response(message="Failed to update payment status", code=500)
