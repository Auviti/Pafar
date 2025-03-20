from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.rides.models.rides import RideStatus
from app.rides.schemas.rides import RideStatusCreate
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Service to create a new ride status
async def create_ride_status(db: AsyncSession, ride_status: RideStatusCreate) -> RideStatus:
    try:
        # Check if location is provided and validated by Pydantic
        if ride_status.location:
            # Ensure latitude, longitude, and address are present
            location = ride_status.location
            if 'latitude' not in location or 'longitude' not in location or 'address' not in location:
                raise HTTPException(status_code=400, detail="Location must include latitude, longitude, and address.")
        
        new_ride_status = RideStatus(
            booking_id=ride_status.booking_id,
            ride_status=ride_status.ride_status,
            location=ride_status.location  # Save the location if provided
        )
        db.add(new_ride_status)
        await db.commit()
        await db.refresh(new_ride_status)
        return new_ride_status
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get all ride statuses
async def get_ride_statuses(db: AsyncSession) -> list[RideStatus]:
    try:
        result = await db.execute(select(RideStatus))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get a ride status by ID
async def get_ride_status_by_id(db: AsyncSession, ride_status_id: UUID) -> RideStatus:
    try:
        result = await db.execute(select(RideStatus).filter(RideStatus.id == ride_status_id))
        ride_status = result.scalars().first()
        if not ride_status:
            raise HTTPException(status_code=404, detail="Ride Status not found")
        return ride_status
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to update the status of a ride
async def update_ride_status(db: AsyncSession, ride_status_id: UUID, status: str, location: Optional[dict] = None) -> RideStatus:
    try:
        result = await db.execute(select(RideStatus).filter(RideStatus.id == ride_status_id))
        ride_status = result.scalars().first()
        if not ride_status:
            raise HTTPException(status_code=404, detail="Ride Status not found")
        
        ride_status.ride_status = status
        if location:
            ride_status.location = location  # Update the location if provided
        
        db.add(ride_status)
        await db.commit()
        await db.refresh(ride_status)
        return ride_status
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))