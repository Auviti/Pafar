from fastapi import APIRouter, Depends
from schemas.bookings import BookingCreate, BookingResponse, BookingUpdate
from services.bookings import BookingService
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db1
from core.utils.reponse import Response
from uuid import UUID
from models.bookings import BookingStatus  # assuming your status enum is here

router = APIRouter()


@router.post("/bookings/")
async def create_booking_route(booking: BookingCreate, db: AsyncSession = Depends(get_db1)):
    try:
        result = await BookingService.create_booking(db=db, booking_data=booking)
        return Response(data=result, message="Booking created successfully", code=201)
    except Exception as e:
        return Response(message="Failed to create booking", code=500)


@router.get("/bookings/")
async def get_all_bookings_route(db: AsyncSession = Depends(get_db1)):
    try:
        bookings = await BookingService.get_all_bookings(db)
        return Response(data=bookings, message="Bookings fetched successfully")
    except Exception as e:
        return Response(message="Failed to fetch bookings", code=500)


@router.get("/bookings/{booking_id}")
async def get_booking_by_id_route(booking_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        result = await BookingService.get_booking(db=db, booking_id=booking_id)
        if not result:
            return Response(message="Booking not found", code=404)
        return Response(data=result, message="Booking fetched successfully")
    except Exception as e:
        return Response(message="Failed to fetch booking", code=500)


@router.put("/bookings/{booking_id}/status")
async def update_booking_status_route(booking_id: UUID, status: str, db: AsyncSession = Depends(get_db1)):
    try:
        status_enum = BookingStatus(status)
        result = await BookingService.update_booking_status(db=db, booking_id=booking_id, status=status_enum)
        return Response(data=result, message="Booking status updated")
    except ValueError:
        return Response(message="Invalid status value", code=400)
    except Exception as e:
        return Response(message="Failed to update status", code=500)


@router.put("/bookings/{booking_id}/protect")
async def protect_booking_route(booking_id: UUID, isprotected: bool, db: AsyncSession = Depends(get_db1)):
    try:
        booking_data = BookingUpdate(isprotected=isprotected)
        result = await BookingService.update_booking(db=db, booking_id=booking_id, booking_data=booking_data)
        return Response(data=result, message="Booking protection updated")
    except Exception as e:
        return Response(message="Failed to update protection", code=500)

@router.delete("/bookings/{booking_id}")
async def delete_booking_by_id(booking_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        result = await BookingService.delete_booking(db=db, booking_id=booking_id)
        if not result:
            return Response(message="Booking not found", code=404)
        return Response(data=result, message="Booking deleted successfully")
    except Exception as e:
        return Response(message="Failed to delete booking", code=500)