from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from core.database import get_db1
from core.utils.response import Response
from schemas.currency import CurrencyCreate, CurrencyUpdate, CurrencyOut
from services.currency import CurrencyService

router = APIRouter()


@router.post("/currencies/")
async def create_currency_route(data: CurrencyCreate, db: AsyncSession = Depends(get_db1)):
    try:
        service = CurrencyService(db)
        result = await service.create_currency(data)
        return Response(data=result, message="Currency created successfully", code=201)
    except Exception as e:
        return Response(message="Failed to create currency", code=500)


@router.get("/currencies/")
async def get_all_currencies_route(db: AsyncSession = Depends(get_db1)):
    try:
        service = CurrencyService(db)
        result = await service.get_all_currencies()
        return Response(data=result, message="Currencies retrieved successfully")
    except Exception:
        return Response(message="Failed to fetch currencies", code=500)


@router.get("/currencies/{currency_id}")
async def get_currency_by_id_route(currency_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        service = CurrencyService(db)
        result = await service.get_currency_by_id(currency_id)
        return Response(data=result, message="Currency retrieved successfully")
    except HTTPException as e:
        return Response(message=e.detail, code=e.status_code)
    except Exception:
        return Response(message="Failed to fetch currency", code=500)


@router.put("/currencies/{currency_id}")
async def update_currency_route(currency_id: UUID, data: CurrencyUpdate, db: AsyncSession = Depends(get_db1)):
    try:
        service = CurrencyService(db)
        result = await service.update_currency(currency_id, data)
        return Response(data=result, message="Currency updated successfully")
    except HTTPException as e:
        return Response(message=e.detail, code=e.status_code)
    except Exception:
        return Response(message="Failed to update currency", code=500)


@router.delete("/currencies/{currency_id}")
async def delete_currency_route(currency_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        service = CurrencyService(db)
        success = await service.delete_currency(currency_id)
        if success:
            return Response(message="Currency deleted successfully")
        return Response(message="Failed to delete currency", code=500)
    except HTTPException as e:
        return Response(message=e.detail, code=e.status_code)
    except Exception:
        return Response(message="Failed to delete currency", code=500)
