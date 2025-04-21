from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
import json
from models.bookings import Booking, List,Optional,datetime, timezone
from schemas.bookings import BookingCreate, BookingUpdate, BookingResponse
from core.utils.scanner.qrcode import QRCode

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
            # Convert booking_data to dict for mutation
            print(booking_data,'-------+')
            data = booking_data.dict()
            data['ticket_id']=str(booking_data.ticket_id)
            data['user_id']=str(booking_data.user_id)
            data['created_at']=datetime.now(timezone.utc)
            data['updated_at']=datetime.now(timezone.utc)
            # Convert the booking_data to a JSON-formatted string
            stringified_data = json.dumps(data, default=str)  # default=str handles datetime & UUID

            qrcode = QRCode()
            qrcoderesult = qrcode.generate_qrcode(
                data=stringified_data,
                save_as_png=False
            )
            # data['barcode']=qrcoderesult
            # print(data,'======')
        
            booking = Booking(
                ticket_id=booking_data.ticket_id,
                code=booking_data.code,
                barcode=qrcoderesult,
                user_id=booking_data.user_id,
                pick_up_location=booking_data.pick_up_location,
                drop_off_location=booking_data.drop_off_location,
                fare_amount=booking_data.fare_amount,
                isprotected=booking_data.isprotected,
                seats=booking_data.seats
            )
            db.add(booking)
            await db.commit()
            await db.refresh(booking)
            return booking.to_dict()  # Converts to Pydantic model

        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(str(e))
        except Exception as e:
            raise Exception(f"An unexpected error occurred while creating booking: {str(e)}")

    @staticmethod
    async def get_booking(db: AsyncSession, booking_id: UUID) -> BookingResponse:
        """
        Retrieve a booking by its ID.
        :param db: Database session
        :param booking_id: UUID of the booking to fetch
        :return: BookingResponse
        """
        try:
            async with db.begin():
                stmt = select(Booking).filter(Booking.id == booking_id)
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()
                if not booking:
                    raise Exception("Booking not found")
                return booking.to_dict()

        except SQLAlchemyError as e:
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while fetching booking: {str(e)}")

    @staticmethod
    async def get_all_bookings(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[BookingResponse]:
        """
        Retrieve all bookings with pagination.
        :param db: Database session
        :param skip: Number of records to skip (for pagination)
        :param limit: Number of records to fetch
        :return: List of BookingResponse
        """
        try:
            async with db.begin():
                stmt = select(Booking).offset(skip).limit(limit)
                result = await db.execute(stmt)
                bookings = result.scalars().all()
                return [booking.to_dict() for booking in bookings]

        except SQLAlchemyError as e:
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while fetching all bookings: {str(e)}")

    @staticmethod
    async def update_booking(db: AsyncSession, booking_id: UUID, booking_data: BookingUpdate) -> BookingResponse:
        """
        Update an existing booking in the database.
        :param db: Database session
        :param booking_id: UUID of the booking to update
        :param booking_data: BookingUpdate Pydantic model
        :return: The updated BookingResponse
        """
        try:
            
        
            async with db.begin():
                stmt = select(Booking).filter(Booking.id == booking_id)
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()
                if not booking:
                    raise Exception("Booking not found")
                # Convert booking_data to dict for mutation
                data = booking_data.dict()
                data['created_at']=booking.created_at
                data['updated_at']=datetime.now(timezone.utc)
                barcode = Barcode()
                barcoderes = barcode.generate_barcode(
                    data=data,
                    filename='barcode.png',
                    save_as_png=False
                )
            
                # Update the fields that are provided in the request body
                if booking_data.code:
                    booking.code = booking_data.code
                if barcoderes:
                    booking.barcode = booking_data.barcoderes
                if booking_data.pick_up_location:
                    booking.pick_up_location = booking_data.pick_up_location
                if booking_data.drop_off_location:
                    booking.drop_off_location = booking_data.drop_off_location
                
                if booking_data.fare_amount:
                    booking.fare_amount = booking_data.fare_amount
                if booking_data.isprotected is not None:
                    booking.isprotected = booking_data.isprotected
                if booking_data.seats:
                    booking.seats = booking_data.seats

                await db.commit()
                await db.refresh(booking)
                return booking.to_dict()

        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while updating booking: {str(e)}")

    @staticmethod
    async def delete_booking(db: AsyncSession, booking_id: UUID) -> bool:
        """
        Delete a booking by its ID.
        :param db: Database session
        :param booking_id: UUID of the booking to delete
        :return: Confirmation message
        """
        try:
            async with db.begin():
                stmt = select(Booking).filter(Booking.id == booking_id)
                result = await db.execute(stmt)
                booking = result.scalar_one_or_none()
                if not booking:
                    raise Exception("Booking not found")
                
                await db.delete(booking)
                await db.commit()
                return True

        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)
        except Exception as e:
            raise Exception(f"An unexpected error occurred while deleting booking: {str(e)}")

    @staticmethod
    async def calculate_fare(db: AsyncSession, booking_id: UUID) -> float:
        """
        Calculate the fare of a booking.
        :param db: Database session
        :param booking_id: UUID of the booking
        :return: Calculated fare amount (float)
        """
        try:
            booking = await BookingService.get_booking(db, booking_id)
            # Here you could add some business logic to calculate the fare
            # For simplicity, let's return the stored fare amount
            return booking.fare_amount

        except Exception as e:
            raise Exception(f"An unexpected error occurred while calculating fare: {str(e)}")

