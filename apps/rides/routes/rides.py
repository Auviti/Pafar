from fastapi import APIRouter, Depends, HTTPException
from app.rides.schemas.rides import Ride, RideStatus
from app.rides.services.rides import RideCreate , RideRead
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db1
from uuid import UUID
from typing import Optional,List

router = APIRouter()

@router.post("/rides/", response_model=Ride)
def create_ride(driver_id: UUID, trip_fare: float, startlocation: dict, endlocation: dict, starts_at: datetime, ends_at: datetime, db: Session = Depends(get_db1)):
    ride = RideService.create_ride(db, driver_id, trip_fare, startlocation, endlocation, starts_at, ends_at)
    return ride

@router.get("/rides/{ride_id}", response_model=Ride)
def get_ride(ride_id: UUID, db: Session = Depends(get_db1)):
    ride = RideService.get_ride(db, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride

@router.get("/rides/", response_model=List[Ride])
def get_rides_by_status(status: RideStatus, skip: int = 0, limit: int = 100, db: Session = Depends(get_db1)):
    rides = RideService.get_rides_by_status(db, status, skip, limit)
    return rides

@router.put("/rides/{ride_id}/status", response_model=Ride)
def update_ride_status(ride_id: UUID, new_status: RideStatus, db: Session = Depends(get_db1)):
    ride = RideService.update_ride_status(db, ride_id, new_status)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride

@router.put("/rides/{ride_id}/location", response_model=Ride)
def update_ride_location(ride_id: UUID, startlocation: Optional[dict] = None, endlocation: Optional[dict] = None, db: Session = Depends(get_db1)):
    ride = RideService.update_ride_location(db, ride_id, startlocation, endlocation)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride

@router.delete("/rides/{ride_id}", response_model=Ride)
def delete_ride(ride_id: UUID, db: Session = Depends(get_db1)):
    ride = RideService.delete_ride(db, ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return ride