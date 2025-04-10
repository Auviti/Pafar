from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from schemas.rides import RideCreate, RideUpdate, RideResponse, RideStatus
from services.rides import RideService
from core.database import get_db1
from core.utils.reponse import Response

router = APIRouter()
# Create a ride
@router.post("/rides/", response_model=RideResponse)
async def create_ride(ride_data: RideCreate, db: AsyncSession = Depends(get_db1)):
    try:
        ride = await RideService.create_ride(db, ride_data)  # Await async method
        return Response(data=ride, message="Ride created successfully", code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=400)

# Get a ride by ID
@router.get("/rides/{ride_id}", response_model=RideResponse)
async def get_ride(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    ride = await RideService.get_ride(db, ride_id)  # Await async method
    if ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=ride, message="Ride fetched successfully", code=200)

# Get all rides with pagination
@router.get("/rides/", response_model=List[RideResponse])
async def get_all_rides(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db1)):
    rides = await RideService.get_all_rides(db, skip=skip, limit=limit)  # Await async method
    return Response(data=rides, message="Rides fetched successfully", code=200)

# Update the ride
@router.put("/rides/{ride_id}", response_model=RideResponse)
async def update_ride_details(ride_id: UUID, ride_data: RideUpdate, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride(db, ride_id, ride_data)  # Await async method
    if updated_ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=updated_ride, message="Ride updated successfully", code=200)

# Update the status of a ride
@router.put("/rides/{ride_id}/status", response_model=RideResponse)
async def update_ride_status(ride_id: UUID, status: RideStatus, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride_status(db, ride_id, status)  # Await async method
    if updated_ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=updated_ride, message="Ride status updated successfully", code=200)

# Update the bus of a ride
@router.put("/rides/{ride_id}/bus", response_model=RideResponse)
async def update_ride_bus(ride_id: UUID, bus_id: UUID, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride_bus(db, ride_id, bus_id)  # Await async method
    if updated_ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=updated_ride, message="Ride bus updated successfully", code=200)

# Update the location of a ride
@router.put("/rides/{ride_id}/location", response_model=RideResponse)
async def update_ride_location(ride_id: UUID, location: dict, is_start_location: bool = False, db: AsyncSession = Depends(get_db1)):
    updated_ride = await RideService.update_ride_location(db, ride_id, location, is_start_location)  # Await async method
    if updated_ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=updated_ride, message="Ride location updated successfully", code=200)

# Delete a ride by ID
@router.delete("/rides/{ride_id}", response_model=RideResponse)
async def delete_ride(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    deleted_ride = await RideService.delete_ride(db, ride_id)  # Await async method
    if deleted_ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=deleted_ride, message="Ride deleted successfully", code=200)

# Calculate the total fare for a ride
@router.get("/rides/{ride_id}/fare", response_model=float)
async def calculate_ride_fare(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    ride = await RideService.get_ride(db, ride_id)  # Await async method
    if ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=await RideService.calculate_ride_fare(ride), message="Fare calculated successfully", code=200)

# Get the duration of a ride
@router.get("/rides/{ride_id}/duration", response_model=float)
async def get_ride_duration(ride_id: UUID, db: AsyncSession = Depends(get_db1)):
    ride = await RideService.get_ride(db, ride_id)  # Await async method
    if ride is None:
        return Response(success=False, message="Ride not found", code=404)
    return Response(data=await RideService.get_ride_duration(ride), message="Ride duration fetched successfully", code=200)