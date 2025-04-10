from fastapi import APIRouter, Depends
from schemas.bookings import BookingCreate, BookingResponse
from services.bookings import BookingService
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db1
from core.utils.reponse import Response
from uuid import UUID

router = APIRouter()

# Route to create a new booking
@router.post("/bookings/", response_model=BookingResponse)
async def create_booking_route(booking: BookingCreate, db: AsyncSession = Depends(get_db1)):
    response = await BookingService.create_booking(db=db, booking_data=booking)
    return Response(success=True, data=response, message="Booking created successfully", code=201)

# Route to get all bookings
@router.get("/bookings/", response_model=list[BookingResponse])
async def get_all_bookings_route(db: AsyncSession = Depends(get_db1)):
    bookings = await BookingService.get_all_bookings(db)
    return Response(success=True, data=bookings, message="Bookings fetched successfully", code=200)

# Route to get a booking by ID
@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id_route(booking_id: UUID, db: AsyncSession = Depends(get_db1)):
    response = await BookingService.get_booking(db=db, booking_id=booking_id)
    if not response.success:
        return Response(success=False, message=response.message, code=404)
    return Response(success=True, data=response, message="Booking fetched successfully", code=200)

# Route to update booking status
@router.put("/bookings/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status_route(booking_id: UUID, status: str, db: AsyncSession = Depends(get_db1)):
    status_enum = BookingStatus(status)
    response = await BookingService.update_booking_status(db=db, booking_id=booking_id, status=status_enum)
    return Response(success=True, data=response, message="Booking status updated", code=200)

# Route to protect a booking
@router.put("/bookings/{booking_id}/protect", response_model=BookingResponse)
async def protect_booking_route(booking_id: UUID, isprotected: bool, db: AsyncSession = Depends(get_db1)):
    booking_data = BookingUpdate(isprotected=isprotected)
    response = await BookingService.update_booking(db=db, booking_id=booking_id, booking_data=booking_data)
    return Response(success=True, data=response, message="Booking protection status updated", code=200)
