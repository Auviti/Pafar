from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.rides.schemas.rides import RideCreate, RideUpdate
from app.rides.services.rides import RideService
from core.database import get_db1  # Assuming get_db1 provides AsyncSession

router = APIRouter()

# Create a ride
@router.post("/rides/", response_model=RideCreate)
async def create_ride(ride_data: RideCreate, db: AsyncSession = Depends(get_db1)):
    try:
        ride = await RideService.create_ride(db, ride_data)  # Await async method
        return ride
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Get a ride by ID
@router.get("/rides/{ride_id}", response_model=RideUpdate)
async def get_ride(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    ride = await RideService.get_ride(db, ride_id)  # Await async method
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride

# Get all rides with pagination
@router.get("/rides/", response_model=List[RideUpdate])
async def get_all_rides(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db1)):
    rides = await RideService.get_all_rides(db, skip=skip, limit=limit)  # Await async method
    return rides

# Update the ride
@router.put("/rides/{ride_id}", response_model=RideUpdate)
async def update_ride_details(ride_id: UUID, ride_data: RideUpdate, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride(db, ride_id, ride_data)  # Await async method
    if updated_ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return updated_ride

# Update the status of a ride
@router.put("/rides/{ride_id}/status", response_model=RideUpdate)
async def update_ride_status(ride_id: UUID, status: RideStatus, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride_status(db, ride_id, status)  # Await async method
    if updated_ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return updated_ride

# Update the bus of a ride
@router.put("/rides/{ride_id}/bus", response_model=RideUpdate)
async def update_ride_bus(ride_id: UUID, bus_id: UUID, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride_bus(db, ride_id, bus_id)  # Await async method
    if updated_ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return updated_ride

# Update the location of a ride
@router.put("/rides/{ride_id}/location", response_model=RideUpdate)
async def update_ride_location(ride_id: UUID, location: dict, is_start_location: bool = False, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride_location(db, ride_id, location, is_start_location)  # Await async method
    if updated_ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return updated_ride

# Delete a ride by ID
@router.delete("/rides/{ride_id}", response_model=RideUpdate)
async def delete_ride(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    deleted_ride = await RideService.delete_ride(db, ride_id)  # Await async method
    if deleted_ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return deleted_ride

# Calculate the total fare for a ride
@router.get("/rides/{ride_id}/fare", response_model=float)
async def calculate_ride_fare(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    ride = await RideService.get_ride(db, ride_id)  # Await async method
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return RideService.calculate_ride_fare(ride)

# Get the duration of a ride
@router.get("/rides/{ride_id}/duration", response_model=float)
async def get_ride_duration(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    ride = await RideService.get_ride(db, ride_id)  # Await async method
    if ride is None:
        raise HTTPException(status_code=404, detail="Ride not found")
    return RideService.get_ride_duration(ride)
