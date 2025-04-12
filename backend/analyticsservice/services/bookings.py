from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from models.bookings import DailyBookings, WeeklyBookings, MonthlyBookings, QuarterlyBookings, YearlyBookings,Location, BookingsByLocation, BookingLocationType
from uuid import uuid4
from datetime import datetime

class BookingService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # Create or update the booking if it exists
    async def create_or_update_daily_booking(self, daily_booking_data: dict):
        try:
            async with self.db.begin():
                result = await self.db.execute(select(DailyBookings).filter_by(created_at=daily_booking_data['created_at']))
                existing_booking = result.scalars().first()

                if existing_booking:
                    # Update the existing daily booking
                    existing_booking.count = daily_booking_data.get('count', existing_booking.count)
                    await self.db.commit()
                    return existing_booking
                else:
                    # Create a new daily booking
                    new_booking = DailyBookings(
                        count=daily_booking_data['count']
                    )
                    self.db.add(new_booking)
                    await self.db.commit()
                    return new_booking
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def create_or_update_weekly_booking(self, weekly_booking_data: dict):
        try:
            async with self.db.begin():
                result = await self.db.execute(select(WeeklyBookings).filter_by(start_date=weekly_booking_data['start_date'], end_date=weekly_booking_data['end_date']))
                existing_booking = result.scalars().first()

                if existing_booking:
                    # Update the existing weekly booking
                    existing_booking.count = weekly_booking_data.get('count', existing_booking.count)
                    await self.db.commit()
                    return existing_booking
                else:
                    # Create a new weekly booking
                    new_booking = WeeklyBookings(
                        count=weekly_booking_data['count'],
                        duration=weekly_booking_data['duration'],
                        start_date=weekly_booking_data['start_date'],
                        end_date=weekly_booking_data['end_date']
                    )
                    self.db.add(new_booking)
                    await self.db.commit()
                    return new_booking
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def create_or_update_monthly_booking(self, monthly_booking_data: dict):
        try:
            async with self.db.begin():
                result = await self.db.execute(select(MonthlyBookings).filter_by(month=monthly_booking_data['month'], year=monthly_booking_data['year']))
                existing_booking = result.scalars().first()

                if existing_booking:
                    # Update the existing monthly booking
                    existing_booking.count = monthly_booking_data.get('count', existing_booking.count)
                    await self.db.commit()
                    return existing_booking
                else:
                    # Create a new monthly booking
                    new_booking = MonthlyBookings(
                        count=monthly_booking_data['count'],
                        month=monthly_booking_data['month'],
                        year=monthly_booking_data['year']
                    )
                    self.db.add(new_booking)
                    await self.db.commit()
                    return new_booking
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def create_or_update_quarterly_booking(self, quarterly_booking_data: dict):
        try:
            async with self.db.begin():
                result = await self.db.execute(select(QuarterlyBookings).filter_by(quarter=quarterly_booking_data['quarter'], year=quarterly_booking_data['year']))
                existing_booking = result.scalars().first()

                if existing_booking:
                    # Update the existing quarterly booking
                    existing_booking.count = quarterly_booking_data.get('count', existing_booking.count)
                    await self.db.commit()
                    return existing_booking
                else:
                    # Create a new quarterly booking
                    new_booking = QuarterlyBookings(
                        count=quarterly_booking_data['count'],
                        quarter=quarterly_booking_data['quarter'],
                        year=quarterly_booking_data['year']
                    )
                    self.db.add(new_booking)
                    await self.db.commit()
                    return new_booking
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def create_or_update_yearly_booking(self, yearly_booking_data: dict):
        try:
            async with self.db.begin():
                result = await self.db.execute(select(YearlyBookings).filter_by(year=yearly_booking_data['year']))
                existing_booking = result.scalars().first()

                if existing_booking:
                    # Update the existing yearly booking
                    existing_booking.count = yearly_booking_data.get('count', existing_booking.count)
                    await self.db.commit()
                    return existing_booking
                else:
                    # Create a new yearly booking
                    new_booking = YearlyBookings(
                        count=yearly_booking_data['count'],
                        year=yearly_booking_data['year']
                    )
                    self.db.add(new_booking)
                    await self.db.commit()
                    return new_booking
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    # Retrieve a single booking by its ID
    async def get(self, booking_id: str, booking_type: str):
        model_mapping = {
            'daily': DailyBookings,
            'weekly': WeeklyBookings,
            'monthly': MonthlyBookings,
            'quarterly': QuarterlyBookings,
            'yearly': YearlyBookings,
        }

        if booking_type.lower() not in model_mapping:
            raise ValueError("Invalid booking type")

        booking_model = model_mapping[booking_type.lower()]
        result = await self.db.execute(select(booking_model).filter_by(id=booking_id))
        booking = result.scalars().first()

        return booking

    # Retrieve all bookings of a specific type
    async def get_all(self, booking_type: str):
        model_mapping = {
            'daily': DailyBookings,
            'weekly': WeeklyBookings,
            'monthly': MonthlyBookings,
            'quarterly': QuarterlyBookings,
            'yearly': YearlyBookings,
        }

        if booking_type.lower() not in model_mapping:
            raise ValueError("Invalid booking type")

        booking_model = model_mapping[booking_type.lower()]
        result = await self.db.execute(select(booking_model))
        bookings = result.scalars().all()

        return bookings

    # Update a booking by its ID
    async def update(self, booking_id: str, booking_data: dict, booking_type: str):
        model_mapping = {
            'daily': DailyBookings,
            'weekly': WeeklyBookings,
            'monthly': MonthlyBookings,
            'quarterly': QuarterlyBookings,
            'yearly': YearlyBookings,
        }

        if booking_type.lower() not in model_mapping:
            raise ValueError("Invalid booking type")

        booking_model = model_mapping[booking_type.lower()]
        result = await self.db.execute(select(booking_model).filter_by(id=booking_id))
        booking = result.scalars().first()

        if booking:
            # Update fields dynamically based on provided data
            for key, value in booking_data.items():
                setattr(booking, key, value)
            booking.updated_at = datetime.utcnow()  # Update timestamp
            await self.db.commit()
            return booking
        else:
            return None

    # Delete a booking by its ID
    async def delete(self, booking_id: str, booking_type: str):
        model_mapping = {
            'daily': DailyBookings,
            'weekly': WeeklyBookings,
            'monthly': MonthlyBookings,
            'quarterly': QuarterlyBookings,
            'yearly': YearlyBookings,
        }

        if booking_type.lower() not in model_mapping:
            raise ValueError("Invalid booking type")

        booking_model = model_mapping[booking_type.lower()]
        result = await self.db.execute(select(booking_model).filter_by(id=booking_id))
        booking = result.scalars().first()

        if booking:
            await self.db.delete(booking)
            await self.db.commit()
            return True
        else:
            return False

    async def create_location(self, name: str, location_type: BookingLocationType) -> Location:
        try:
            new_location = Location(
                name=name,
                type=location_type,
            )
            self.db.add(new_location)
            await self.db.commit()
            await self.db.refresh(new_location)
            return new_location
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def get_location(self, location_id: str) -> Location:
        async with self.db.begin():
            result = await self.db.execute(select(Location).filter_by(id=location_id))
            location = result.scalars().first()
            return location

    async def update_location(self, location_id: str, name: str, location_type: BookingLocationType) -> Location:
        location = await self.get_location(location_id)
        if location:
            location.name = name
            location.type = location_type
            await self.db.commit()
            await self.db.refresh(location)
            return location
        return None

    async def delete_location(self, location_id: str) -> bool:
        location = await self.get_location(location_id)
        if location:
            await self.db.delete(location)
            await self.db.commit()
            return True
        return False

    async def create_booking_by_location(
        self, location_id: str, location_name: str, location_type: BookingLocationType, booking_count: int
    ) -> BookingsByLocation:
        try:
            new_booking = BookingsByLocation(
                location_id=location_id,
                location_name=location_name,
                location_type=location_type,
                booking_count=booking_count,
            )
            self.db.add(new_booking)
            await self.db.commit()
            await self.db.refresh(new_booking)
            return new_booking
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e

    async def get_booking_by_location(self, booking_id: str) -> BookingsByLocation:
        async with self.db.begin():
            result = await self.db.execute(select(BookingsByLocation).filter_by(id=booking_id))
            booking = result.scalars().first()
            return booking

    async def update_booking_by_location(
        self, booking_id: str, location_name: str, location_type: BookingLocationType, booking_count: int
    ) -> BookingsByLocation:
        booking = await self.get_booking_by_location(booking_id)
        if booking:
            booking.location_name = location_name
            booking.location_type = location_type
            booking.booking_count = booking_count
            await self.db.commit()
            await self.db.refresh(booking)
            return booking
        return None

    async def delete_booking_by_location(self, booking_id: str) -> bool:
        booking = await self.get_booking_by_location(booking_id)
        if booking:
            await self.db.delete(booking)
            await self.db.commit()
            return True
        return False

    async def get_all_bookings_by_location(self, location_id: str) -> list:
        async with self.db.begin():
            result = await self.db.execute(
                select(BookingsByLocation).filter_by(location_id=location_id)
            )
            bookings = result.scalars().all()
            return bookings
