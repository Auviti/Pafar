from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import uuid4

# Import the booking service and models
from services.bookings import BookingService
from core.database import get_db1  # Assuming you have a `get_db1` function for database session dependency
from models.bookings import DailyBookings, WeeklyBookings, MonthlyBookings, QuarterlyBookings, YearlyBookings
from schemas.bookings import (
    DailyBookingCreateUpdate, 
    WeeklyBookingCreateUpdate,
    MonthlyBookingCreateUpdate,
    QuarterlyBookingCreateUpdate,
    YearlyBookingCreateUpdate
)

from pydantic import BaseModel
from core.utils.response import Response

# Define the router for booking routes
router = APIRouter()

# Create or Update Daily Booking
@router.post("/daily", response_model=DailyBookingCreateUpdate)
async def create_or_update_daily_booking(
    daily_booking: DailyBookingCreateUpdate, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    booking_data = daily_booking.dict()
    booking = await service.create_or_update_daily_booking(booking_data)
    return Response(data=booking.to_dict(), success=True, message="Daily booking created or updated", code=200)


# Create or Update Weekly Booking
@router.post("/weekly", response_model=WeeklyBookingCreateUpdate)
async def create_or_update_weekly_booking(
    weekly_booking: WeeklyBookingCreateUpdate, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    booking_data = weekly_booking.dict()
    booking = await service.create_or_update_weekly_booking(booking_data)
    return Response(data=booking.to_dict(), success=True, message="Weekly booking created or updated", code=200)


# Create or Update Monthly Booking
@router.post("/monthly", response_model=MonthlyBookingCreateUpdate)
async def create_or_update_monthly_booking(
    monthly_booking: MonthlyBookingCreateUpdate, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    booking_data = monthly_booking.dict()
    booking = await service.create_or_update_monthly_booking(booking_data)
    return Response(data=booking.to_dict(), success=True, message="Monthly booking created or updated", code=200)


# Create or Update Quarterly Booking
@router.post("/quarterly", response_model=QuarterlyBookingCreateUpdate)
async def create_or_update_quarterly_booking(
    quarterly_booking: QuarterlyBookingCreateUpdate, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    booking_data = quarterly_booking.dict()
    booking = await service.create_or_update_quarterly_booking(booking_data)
    return Response(data=booking.to_dict(), success=True, message="Quarterly booking created or updated", code=200)


# Create or Update Yearly Booking
@router.post("/yearly", response_model=YearlyBookingCreateUpdate)
async def create_or_update_yearly_booking(
    yearly_booking: YearlyBookingCreateUpdate, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    booking_data = yearly_booking.dict()
    booking = await service.create_or_update_yearly_booking(booking_data)
    return Response(data=booking.to_dict(), success=True, message="Yearly booking created or updated", code=200)


# Get Single Booking by ID (for all types)
@router.get("/{booking_type}/{booking_id}", response_model=dict)
async def get_booking(
    booking_type: str, booking_id: str, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    booking = await service.get(booking_id, booking_type)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return Response(data=booking.to_dict(), success=True, message=f"{booking_type.capitalize()} booking found", code=200)


# Get All Bookings of a specific type
@router.get("/{booking_type}/all", response_model=list)
async def get_all_bookings(
    booking_type: str, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    bookings = await service.get_all(booking_type)
    return Response(data=[booking.to_dict() for booking in bookings], success=True, message=f"All {booking_type} bookings fetched", code=200)


# Update Booking by ID (for all types)
@router.put("/{booking_type}/{booking_id}", response_model=dict)
async def update_booking(
    booking_type: str,
    booking_id: str,
    booking_data: dict,
    db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    updated_booking = await service.update(booking_id, booking_data, booking_type)
    if not updated_booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return Response(data=updated_booking.to_dict(), success=True, message=f"{booking_type.capitalize()} booking updated", code=200)


# Delete Booking by ID (for all types)
@router.delete("/{booking_type}/{booking_id}", response_model=dict)
async def delete_booking(
    booking_type: str, booking_id: str, db: AsyncSession = Depends(get_db1)
):
    service = BookingService(db)
    is_deleted = await service.delete(booking_id, booking_type)
    if not is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return Response(data=None, success=True, message=f"{booking_type.capitalize()} booking deleted successfully.", code=200)
