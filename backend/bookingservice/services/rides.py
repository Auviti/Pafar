
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import FastAPI, HTTPException, Depends, Query
import asyncpg
from sqlalchemy import cast
from models.rides import Ride,mappeditem # Import the ORM model
from schemas.rides import RideStatus, RideCreate, RideUpdate, UUID,RideFilter
from datetime import datetime
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict

class RideService:

    @staticmethod
    async def create_ride(db: AsyncSession, ride_data: RideCreate):
        """Creates a new ride in the database."""
        
        try:
            ride = Ride(
                name = ride_data.name,
                status=ride_data.status,
                ride_class = ride_data.ride_class,
                ride_type=ride_data.ride_type,
                vehicle_id=ride_data.vehicle_id,
                trip_fare=ride_data.trip_fare,
                startlocation=ride_data.startlocation,
                currentlocation=ride_data.currentlocation,
                endlocation=ride_data.endlocation,
                starts_at = datetime.fromisoformat(ride_data.starts_at.replace("Z", "+00:00")),
                ends_at = datetime.fromisoformat(ride_data.ends_at.replace("Z", "+00:00")),
                suitcase=ride_data.suitcase,
                handluggage=ride_data.handluggage,
                otherluggage=ride_data.otherluggage,
            )
            db.add(ride)
            await db.commit()  # Async commit
            await db.refresh(ride)  # Async refresh
            return ride.to_dict()
        except Exception as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error creating ride: {str(e)}")

    @staticmethod
    async def get_ride(db: AsyncSession, ride_id: UUID):
        """Fetches a ride by its ID."""
        rideid = str(ride_id) if mappeditem is str else ride_id
        try:
            result = await db.execute(select(Ride).filter(Ride.id == rideid))
            res = result.scalars().first()
            if res:
                return res.to_dict()
            return res
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching ride: {str(e)}")

    @staticmethod
    async def get_all_rides(db: AsyncSession, skip: int = 0, limit: int = 100):
        """Fetches all rides, paginated by skip and limit."""
        try:
            result = await db.execute(select(Ride).offset(skip).limit(limit))
            rides=[]
            # Remove sensitive keys from each ride's dictionary
            for ride in result.scalars().all():
                ride_ = ride.to_dict()
                rides.append(ride_)
            return rides
        except SQLAlchemyError as e:
            raise Exception(f"Error fetching rides: {str(e)}")
        
    # Filter rides dynamically (asynchronous)
    @staticmethod
    async def filter_rides(db: AsyncSession, filter: Optional[RideFilter], skip: int = 0, limit: int = 10):
        try:
            # Start building the query
            query = select(Ride)

            # Check if filter is provided
            if filter:
                # Filtering based on the fields available in the filter object
                if filter.name:
                    query = query.filter(Ride.name.ilike(f"%{filter.name}%"))
                if filter.status:
                    query = query.filter(Ride.status == filter.status)
                if filter.ride_class:
                    query = query.filter(Ride.ride_class == filter.ride_class)
                if filter.ride_type:
                    query = query.filter(Ride.ride_type == filter.ride_type)
                if filter.vehicle_id:
                    query = query.filter(Ride.vehicle_id == filter.vehicle_id)

                if filter.startlocation:
                    query = query.filter(Ride.startlocation.ilike(f"%{filter.startlocation}%"))
                if filter.currentlocation:
                    query = query.filter(Ride.currentlocation.ilike(f"%{filter.currentlocation}%"))
                if filter.endlocation:
                    query = query.filter(Ride.endlocation.ilike(f"%{filter.endlocation}%"))
                if filter.starts_at:
                    query = query.filter(Ride.starts_at >= datetime.fromisoformat(filter.starts_at))  # Assume ISO format
                if filter.ends_at:
                    query = query.filter(Ride.ends_at <= datetime.fromisoformat(filter.ends_at))  # Assume ISO format
                if filter.suitcase is not None:
                    query = query.filter(Ride.suitcase == filter.suitcase)
                if filter.handluggage is not None:
                    query = query.filter(Ride.handluggage == filter.handluggage)
                if filter.otherluggage is not None:
                    query = query.filter(Ride.otherluggage == filter.otherluggage)

            # Apply pagination
            query = query.offset(skip).limit(limit)

            # Execute the query
            result = await db.execute(query)
            rides = result.scalars().all()

            # Return the rides as dictionaries (assuming Ride model has a to_dict method)
            return [ride.to_dict() for ride in rides]
        except SQLAlchemyError as e:
            raise HTTPException(status_code=400, detail=f"{str(e)}")

        except asyncpg.exceptions.UniqueViolationError as e:
            raise HTTPException(status_code=400, detail=f"{str(e)}")

        except asyncpg.exceptions.DataError as e:
            raise HTTPException(status_code=400, detail=f"{str(e)}")

        except asyncpg.exceptions.InvalidTextRepresentationError as e:
            raise HTTPException(status_code=400, detail=f"{str(e)}")

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"{str(e)}")

    
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
    async def update_ride(db: AsyncSession, ride_id: UUID, ride_data: RideUpdate):
        """Updates the status of a ride."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            ride = result.scalars().first()
            if ride:
                ride.name = ride_data.name
                ride.status = ride_data.status
                ride.ride_class = ride_data.ride_class
                ride.ride_type = ride_data.ride_type
                ride.status = ride_data.status
                ride.vehicle_id = ride_data.vehicle_id
                ride.trip_fare = ride_data.trip_fare

                # Ensure the startlocation, currentlocation, and endlocation are valid Location instances
                ride.startlocation = Location(**ride_data.startlocation)
                ride.currentlocation = Location(**ride_data.currentlocation)
                ride.endlocation = Location(**ride_data.endlocation)

                ride.suitcase = ride_data.suitcase
                ride.handluggage = ride_data.handluggage
                ride.otherluggage = ride_data.otherluggage

                # Ensure starts_at and ends_at are valid datetime objects
                ride.starts_at = datetime.fromisoformat(ride_data.starts_at)
                ride.ends_at = datetime.fromisoformat(ride_data.ends_at)

                await db.commit()  # Async commit
                await db.refresh(ride)  # Async refresh
                return ride
            return None
        except SQLAlchemyError as e:
            await db.rollback()  # Async rollback
            raise Exception(f"Error updating ride status: {str(e)}")
    
    @staticmethod
    async def update_ride_vehicle(db: AsyncSession, ride_id: UUID, vehicle_id: UUID):
        """Updates the bus of a ride (if applicable, such as for buses or vehicles)."""
        try:
            result = await db.execute(select(Ride).filter(Ride.id == ride_id))
            ride = result.scalars().first()
            if ride:
                ride.vehicle_id = vehicle_id
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
