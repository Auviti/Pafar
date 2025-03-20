from fastapi import APIRouter, Depends, HTTPException
from app.bookings.schemas.bookings import BookingCreate, BookingRead
from app.bookings.services.bookings import create_booking, get_bookings, get_booking_by_id, update_booking_status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from uuid import UUID

router = APIRouter()

# Route to create a new booking
@router.post("/bookings/", response_model=BookingRead)
async def create_booking_route(booking: BookingCreate, db: AsyncSession = Depends(get_db)):
    return await create_booking(db=db, booking=booking)

# Route to get all bookings
@router.get("/bookings/", response_model=list[BookingRead])
async def get_all_bookings_route(db: AsyncSession = Depends(get_db)):
    return await get_bookings(db)

# Route to get a booking by ID
@router.get("/bookings/{booking_id}", response_model=BookingRead)
async def get_booking_by_id_route(booking_id: UUID, db: AsyncSession = Depends(get_db)):
    return await get_booking_by_id(db=db, booking_id=booking_id)

# Route to update booking status
@router.put("/bookings/{booking_id}/status", response_model=BookingRead)
async def update_booking_status_route(booking_id: UUID, status: str, db: AsyncSession = Depends(get_db)):
    return await update_booking_status(db=db, booking_id=booking_id, status=status)
