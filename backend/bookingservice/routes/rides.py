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

# Filter users by dynamic criteria
@router.post("/rides/filter")
async def filter_rides_by_criteria(filters: dict,  db: AsyncSession = Depends(get_db1)):
    try:
        rides = await RideService.filter_rides(db, filters)
#         ride_example_schema = {
#     "id": "UUID",  # e.g. "a1b2c3d4-e5f6-7890-1234-56789abcdef0"
#     "name": "string",  # e.g. "John's Ride"
    
#     # Enum: One of these strings
#     "status": ["ASSIGNED", "ONGOING", "COMPLETED", "CANCELED"],

#     # Enum: Ride class options
#     "ride_class": ["ECONOMY", "BUSINESS", "LUXURY"],

#     # Enum: Type of ride
#     "ride_type": ["ONE_WAY", "ROUND_TRIP"],

#     "vehicle_id": "UUID",  # e.g. "4d2a8f3d-1ab2-4c9d-a45b-001a1b2c3d4e"
#     "trip_fare": 25.00,  # base fare in float

#     # JSON object: location with coordinates + address
#     "startlocation": {
#         "latitude": 41.8781,
#         "longitude": -87.6298,
#         "address": "233 S Wacker Dr, Chicago, IL"
#     },
#     "currentlocation": {
#         "latitude": 41.9000,
#         "longitude": -87.6500,
#         "address": "123 N Clark St, Chicago, IL"
#     },
#     "endlocation": {
#         "latitude": 41.881832,
#         "longitude": -87.623177,
#         "address": "Millennium Park, Chicago"
#     },

#     "starts_at": "2025-04-14T10:30:00Z",  # ISO 8601 timestamp
#     "ends_at": "2025-04-14T11:00:00Z",    # ISO 8601 timestamp

#     "created_at": "2025-04-14T10:00:00Z",  # Automatically generated
#     "updated_at": "2025-04-14T10:15:00Z",  # Auto-updated on changes

#     # Luggage weights in kg (or units)
#     "suitcase": 5.0,
#     "handluggage": 2.0,
#     "otherluggage": 1.5,

#     # Calculated fields
#     "duration": 1800,  # in seconds (30 mins)
#     "total_fare": 25.18  # base fare + luggage cost (0.02 * total luggage weight)
# }

        return Response(data=rides,code=200)
    except Exception as error:
        return Response(message=str(error),success=False,code=500)