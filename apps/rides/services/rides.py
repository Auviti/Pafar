from app.rides.schemas.models import Ride, RideStatus, RideCreate, RideUpdate
# from app.rides.schemas.models import Bus  # Assuming Bus model exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from datetime import datetime
import asyncio

class RideService:

    @staticmethod
    async def create_ride(db: AsyncSession, ride_data: RideCreate):
        """Creates a new ride in the database."""
        try:
            ride = Ride(
                status=ride_data.status,
                driver_id=ride_data.driver_id,
                bus_id=ride_data.bus_id,
                trip_fare=ride_data.trip_fare,
                passengers=ride_data.passengers,
                startlocation=ride_data.startlocation,
                currentlocation=ride_data.currentlocation,
                endlocation=ride_data.endlocation,
                starts_at=ride_data.starts_at,
                ends_at=ride_data.ends_at,
                suitcase=ride_data.suitcase,
                handluggage=ride_data.handluggage,
                otherluggage=ride_data.otherluggage,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(ride)
            await db.commit()  # Async commit
            await db.refresh(ride)  # Async refresh
            return ride
        except SQLAlchemyError as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error creating ride: {str(e)}")

    @staticmethod
    async def get_ride(db: AsyncSession, ride_id: UUID):
        """Fetches a ride by its ID."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching ride: {str(e)}")

    @staticmethod
    async def get_all_rides(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Fetches all rides, paginated by skip and limit."""
        try:
            result = await db.execute(select(Ride).offset(skip).limit(limit))
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching rides: {str(e)}")

    @staticmethod
    async def update_ride_status(db: AsyncSession, ride_id: UUID, status: RideStatus):
        """Updates the status of a ride."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            ride = result.scalars().first()
            if ride:
                ride.status = status
                ride.updated_at = datetime.utcnow()
                await db.commit()  # Async commit
                await db.refresh(ride)  # Async refresh
                return ride
            return None
        except SQLAlchemyError as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error updating ride status: {str(e)}")

    
    @staticmethod
    async def update_ride_bus(db: AsyncSession, ride_id: UUID, bus_id: UUID):
        """Updates the bus of a ride (if applicable, such as for buses or vehicles)."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            ride = result.scalars().first()
            if ride:
                ride.bus_id = bus_id
                await db.commit()  # Async commit
                await db.refresh(ride)  # Async refresh
                return ride
            return None
        except SQLAlchemyError as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error updating ride bus: {str(e)}")

    @staticmethod
    async def update_ride_location(db: AsyncSession, ride_id: UUID, location: dict, is_start_location: bool = False):
        """Updates the start or end location of a ride."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            ride = result.scalars().first()
            if ride:
                if is_start_location:
                    ride.startlocation = location
                else:
                    ride.endlocation = location
                ride.updated_at = datetime.utcnow()
                await db.commit()  # Async commit
                await db.refresh(ride)  # Async refresh
                return ride
            return None
        except SQLAlchemyError as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error updating ride location: {str(e)}")

    @staticmethod
    async def delete_ride(db: AsyncSession, ride_id: UUID):
        """Deletes a ride by its ID."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            ride = result.scalars().first()
            if ride:
                await db.delete(ride)  # Async delete
                await db.commit()  # Async commit
                return ride
            return None
        except SQLAlchemyError as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error deleting ride: {str(e)}")

    @staticmethod
    async def calculate_ride_fare(ride: Ride):
        """Calculates the total fare for the ride, including luggage charges."""
        # Simulating a non-blocking operation (even though it's inherently synchronous)
        await asyncio.to_thread(RideService._calculate_fare, ride)
        
    @staticmethod
    def _calculate_fare(ride: Ride):
        """Synchronous helper function to calculate fare"""
        luggage_fare = 0.02 * (ride.suitcase + ride.handluggage + ride.otherluggage)
        total_fare = ride.trip_fare + luggage_fare
        return total_fare

    @staticmethod
    async def get_ride_duration(ride: Ride):
        """Calculates the duration of the ride in seconds."""
        # Simulating a non-blocking operation (even though it's inherently synchronous)
        return await asyncio.to_thread(RideService._get_duration, ride)

    @staticmethod
    def _get_duration(ride: Ride):
        """Synchronous helper function to calculate duration"""
        if ride.starts_at and ride.ends_at:
            return (ride.ends_at - ride.starts_at).total_seconds()
        return None

    # @staticmethod
    # def assign_bus_to_ride(db: AsyncSession, ride_id: UUID, bus_id: UUID):
    #     """Assign a bus to a ride."""
    #     try:
    #         ride = db.query(Ride).filter(Ride.id == ride_id).first()
    #         bus = db.query(Bus).filter(Bus.id == bus_id).first()
    #         if ride and bus:
    #             # Assuming a relationship between Ride and Bus exists, we can add the bus_id to ride
    #             ride.bus_id = bus.id  # If ride model has bus_id column for relation
    #             db.commit()
    #             db.refresh(ride)
    #             return ride
    #         return None
    #     except SQLAlchemyError as e:
    #         db.rollback()
    #         raise Exception(f"Error assigning bus to ride: {str(e)}")
