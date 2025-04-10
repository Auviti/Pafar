from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from uuid import UUID
from models.bookings import Booking,BookingStatus  # Import the ORM model
from schemas.bookings import BookingCreate, BookingUpdate, BookingResponse
from sqlalchemy.exc import SQLAlchemyError
from core.utils.reponse import Response  # Custom response handler for uniform responses
from typing import List, Optional

class BookingService:

    @staticmethod
    async def create_booking(db: AsyncSession, booking_data: BookingCreate) -> BookingResponse:
        """
        Creates a new booking in the database.
        :param db: Database session
        :param booking_data: BookingCreate Pydantic model
        :return: The created BookingResponse
        """
        try:
            booking = Booking(
                ride_id=booking_data.ride_id,
                code=booking_data.code,
                barcode=booking_data.barcode,
                user_id=booking_data.user_id,
                pick_up_location=booking_data.pick_up_location,
                drop_off_location=booking_data.drop_off_location,
                booking_time=booking_data.booking_time or datetime.utcnow(),
                booking_status=booking_data.booking_status,
                fare_amount=booking_data.fare_amount,
                isprotected=booking_data.isprotected,
                seats=booking_data.seats
            )
            db.add(booking)
            await db.commit()
            await db.refresh(booking)
            return BookingResponse.from_orm(booking)  # Converts to Pydantic model

        except SQLAlchemyError as e:
            await db.rollback()
            raise Exception(f"Error creating booking: {str(e)}")

    @staticmethod
    async def get_booking(db: AsyncSession, booking_id: UUID) -> BookingResponse:
        """
        Retrieve a booking by its ID.
        :param db: Database session
        :param booking_id: UUID of the booking to fetch
        :return: BookingResponse
        """
        async with db.begin():
            stmt = select(Booking).filter(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()
            if not booking:
                raise Exception("Booking not found")
            return BookingResponse.from_orm(booking)

    @staticmethod
    async def get_all_bookings(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[BookingResponse]:
        """
        Retrieve all bookings with pagination.
        :param db: Database session
        :param skip: Number of records to skip (for pagination)
        :param limit: Number of records to fetch
        :return: List of BookingResponse
        """
        async with db.begin():
            stmt = select(Booking).offset(skip).limit(limit)
            result = await db.execute(stmt)
            bookings = result.scalars().all()
            return [BookingResponse.from_orm(booking) for booking in bookings]

    @staticmethod
    async def update_booking(db: AsyncSession, booking_id: UUID, booking_data: BookingUpdate) -> BookingResponse:
        """
        Update an existing booking in the database.
        :param db: Database session
        :param booking_id: UUID of the booking to update
        :param booking_data: BookingUpdate Pydantic model
        :return: The updated BookingResponse
        """
        async with db.begin():
            stmt = select(Booking).filter(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()
            if not booking:
                raise Exception("Booking not found")

            # Update the fields that are provided in the request body
            if booking_data.code:
                booking.code = booking_data.code
            if booking_data.barcode:
                booking.barcode = booking_data.barcode
            if booking_data.pick_up_location:
                booking.pick_up_location = booking_data.pick_up_location
            if booking_data.drop_off_location:
                booking.drop_off_location = booking_data.drop_off_location
            if booking_data.booking_status:
                booking.booking_status = booking_data.booking_status
            if booking_data.fare_amount:
                booking.fare_amount = booking_data.fare_amount
            if booking_data.isprotected is not None:
                booking.isprotected = booking_data.isprotected
            if booking_data.seats:
                booking.seats = booking_data.seats

            await db.commit()
            await db.refresh(booking)
            return BookingResponse.from_orm(booking)

    @staticmethod
    async def delete_booking(db: AsyncSession, booking_id: UUID) -> str:
        """
        Delete a booking by its ID.
        :param db: Database session
        :param booking_id: UUID of the booking to delete
        :return: Confirmation message
        """
        async with db.begin():
            stmt = select(Booking).filter(Booking.id == booking_id)
            result = await db.execute(stmt)
            booking = result.scalar_one_or_none()
            if not booking:
                raise Exception("Booking not found")
            
            await db.delete(booking)
            await db.commit()
            return f"Booking {booking_id} deleted successfully"

    @staticmethod
    async def calculate_fare(db: AsyncSession, booking_id: UUID) -> float:
        """
        Calculate the fare of a booking.
        :param db: Database session
        :param booking_id: UUID of the booking
        :return: Calculated fare amount (float)
        """
        booking = await BookingService.get_booking(db, booking_id)
        # Here you could add some business logic to calculate the fare
        # For simplicity, let's return the stored fare amount
        return booking.fare_amount

    @staticmethod
    async def update_booking_status(db: AsyncSession, booking_id: UUID, status: BookingStatus) -> BookingResponse:
        """
        Update the status of a booking.
        :param db: Database session
        :param booking_id: UUID of the booking to update
        :param status: New status to set
        :return: Updated BookingResponse
        """
        booking_data = BookingUpdate(booking_status=status)
        return await BookingService.update_booking(db, booking_id, booking_data)
