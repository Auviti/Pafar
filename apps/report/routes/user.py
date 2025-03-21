from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from apps.products.schemas.product import ProductCreate, ProductResponse, ProductUpdate  # Import product schemas (adjust the import paths if necessary)
from apps.reports.services.user import segment_customers,get_customer_lifetime_value,get_customer_lifetime_valueget_users_by_demographics,get_users_by_address,get_users_by_date,get_new_customers_count,get_repeat_customer_percentage,get_average_order_value
from core.database import get_db1  # Assume get_db provides AsyncSession

router = APIRouter()

@router.get("/users/by-demographics", response_model=List[User])  # Assuming User is a Pydantic model for response
async def get_users_by_demographics(
    age: Optional[int] = None,
    gender: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db1)
):
    try:
        users = await get_users_by_demographics(db, age, gender, skip, limit)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/by-address", response_model=List[User])
async def get_users_by_address(
    street: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    post_code: Optional[str] = None,
    kind: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db1)
):
    try:
        users = await get_users_by_address(db, street, city, state, country, post_code, kind, skip, limit)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/by-date", response_model=List[User])
async def get_users_by_date(
    created_at: Optional[str] = None,
    db: AsyncSession = Depends(get_db1)
):
    try:
        users = await get_users_by_date(db, created_at)
        return users
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/new-customers/count", response_model=int)
async def get_new_customers_count(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db1)
):
    try:
        new_customers_count = await get_new_customers_count(db, start_date, end_date)
        return new_customers_count
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repeat-customer/percentage", response_model=float)
async def get_repeat_customer_percentage(db: AsyncSession = Depends(get_db1)):
    try:
        repeat_percentage = await get_repeat_customer_percentage(db)
        return repeat_percentage
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/average-order-value", response_model=float)
async def get_average_order_value(db: AsyncSession = Depends(get_db1)):
    try:
        average_order_value = await get_average_order_value(db)
        return average_order_value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer-lifetime-value", response_model=float)
async def get_customer_lifetime_value(db: AsyncSession = Depends(get_db1)):
    try:
        customer_lifetime_value = await get_customer_lifetime_value(db)
        return customer_lifetime_value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer-segmentation", response_model=dict)
async def segment_customers(db: AsyncSession = Depends(get_db1)):
    try:
        customer_segments = await segment_customers(db)
        return customer_segments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

