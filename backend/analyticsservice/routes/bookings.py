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
    YearlyBookingCreateUpdate,
    Location, BookingsByLocation,BookingLocationTypeEnum
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

# Create Location
@router.post("/locations/", response_model=Response)
async def create_location(name: str, location_type: BookingLocationTypeEnum, db: AsyncSession = Depends(get_db1)):
    service = BookingService(db)
    location = await service.create_location(name, location_type)
    return Response(
        success=True,
        message="Location created successfully.",
        code=200,
        data=location
    )

# Get Location by ID
@router.get("/locations/{location_id}", response_model=Response)
async def get_location(location_id: str, db: AsyncSession = Depends(get_db1)):
    service = BookingService(db)
    location = await service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return Response(
        success=True,
        message="Location found.",
        code=200,
        data=location
    )

# Update Location by ID
@router.put("/locations/{location_id}", response_model=Response)
async def update_location(location_id: str, name: str, location_type: BookingLocationTypeEnum, db: AsyncSession = Depends(get_db1)):
    service = BookingService(db)
    location = await service.update_location(location_id, name, location_type)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return Response(
        success=True,
        message="Location updated successfully.",
        code=200,
        data=location
    )

# Delete Location by ID
@router.delete("/locations/{location_id}", response_model=Response)
async def delete_location(location_id: str, db: AsyncSession = Depends(get_db1)):
    service = BookingService(db)
    success = await service.delete_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return Response(
        success=True,
        message="Location deleted successfully.",
        code=200,
        data=None  # No data returned on delete
    )

# Create Booking by Location
@router.post("/bookings/", response_model=Response)
async def create_booking_by_location(
    location_id: str, location_name: str, location_type: BookingLocationTypeEnum, booking_count: int, db: AsyncSession = Depends(get_db1)
):
    service = BookingsByLocationService(db)
    try:
        booking = await service.create_booking_by_location(location_id, location_name, location_type, booking_count)
        return Response(
            success=True,
            message="Booking created successfully.",
            code=200,
            data=booking.to_dict()  # Assuming `to_dict()` method is available in the model
        )
    except Exception as e:
        return Response(
            success=False,
            message=f"Error creating booking: {str(e)}",
            code=500,
            data=None
        )

# Get Booking by Location ID
@router.get("/bookings/{booking_id}", response_model=Response)
async def get_booking_by_location(booking_id: str, db: AsyncSession = Depends(get_db1)):
    service = BookingsByLocationService(db)
    booking = await service.get_booking_by_location(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Response(
        success=True,
        message="Booking found.",
        code=200,
        data=booking.to_dict()  # Assuming `to_dict()` method is available in the model
    )

# Update Booking by Location
@router.put("/bookings/{booking_id}", response_model=Response)
async def update_booking_by_location(
    booking_id: str, location_name: str, location_type: BookingLocationTypeEnum, booking_count: int, db: AsyncSession = Depends(get_db1)
):
    service = BookingsByLocationService(db)
    booking = await service.update_booking_by_location(booking_id, location_name, location_type, booking_count)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Response(
        success=True,
        message="Booking updated successfully.",
        code=200,
        data=booking.to_dict()  # Assuming `to_dict()` method is available in the model
    )

# Delete Booking by Location
@router.delete("/bookings/{booking_id}", response_model=Response)
async def delete_booking_by_location(booking_id: str, db: AsyncSession = Depends(get_db1)):
    service = BookingsByLocationService(db)
    success = await service.delete_booking_by_location(booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Response(
        success=True,
        message="Booking deleted successfully.",
        code=200,
        data=None  # No data returned on delete
    )

# Get All Bookings by Location ID
@router.get("/bookings/location/{location_id}", response_model=Response)
async def get_all_bookings_by_location(location_id: str, db: AsyncSession = Depends(get_db1)):
    service = BookingsByLocationService(db)
    bookings = await service.get_all_bookings_by_location(location_id)
    if not bookings:
        return Response(
            success=False,
            message="No bookings found for this location.",
            code=404,
            data=[]
        )
    return Response(
        success=True,
        message="Bookings retrieved successfully.",
        code=200,
        data=[booking.to_dict() for booking in bookings]  # Assuming `to_dict()` method is available in the model
    )