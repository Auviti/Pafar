from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.bookings.models.bookings import Booking
from app.bookings.schemas.bookings import BookingCreate
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Service to create a new booking
async def create_booking(db: AsyncSession, booking: BookingCreate) -> Booking:
    try:
        new_booking = Booking(
            user_id=booking.user_id,
            driver_id=booking.driver_id,
            pick_up_location=booking.pick_up_location,
            drop_off_location=booking.drop_off_location,
            booking_time=booking.booking_time or datetime.utcnow(),  # Default to current time if not provided
            fare_amount=booking.fare_amount
        )
        db.add(new_booking)
        await db.commit()
        await db.refresh(new_booking)
        return new_booking
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get all bookings
async def get_bookings(db: AsyncSession) -> list[Booking]:
    try:
        result = await db.execute(select(Booking))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get a booking by ID
async def get_booking_by_id(db: AsyncSession, booking_id: UUID) -> Booking:
    try:
        result = await db.execute(select(Booking).filter(Booking.id == booking_id))
        booking = result.scalars().first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to update the status of a booking
async def update_booking_status(db: AsyncSession, booking_id: UUID, status: str) -> Booking:
    try:
        result = await db.execute(select(Booking).filter(Booking.id == booking_id))
        booking = result.scalars().first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        booking.booking_status = status
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
