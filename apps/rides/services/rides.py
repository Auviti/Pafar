from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from app.rides.schemas.rides import Ride, RideStatus
from typing import List, Optional
from uuid import UUID

class RideService:
    @staticmethod
    def create_ride(db: Session, driver_id: UUID, trip_fare: float, startlocation: dict, endlocation: dict, starts_at: datetime, ends_at: datetime, suitcase: float = 0.0, handluggage: float = 0.0, otherluggage: float = 0.0, passengers: int = 0):
        # Ensure latitude, longitude, and address are present
        location = ride_status.location
        if 'latitude' not in startlocation or 'longitude' not in startlocation or 'address' not in startlocation:
            raise HTTPException(status_code=400, detail="Start Location must include latitude, longitude, and address.")
        if 'latitude' not in endlocation or 'longitude' not in endlocation or 'address' not in endlocation:
            raise HTTPException(status_code=400, detail="End Location must include latitude, longitude, and address.")
        
        ride = Ride(
            driver_id=driver_id,
            trip_fare=trip_fare,
            startlocation=startlocation,
            endlocation=endlocation,
            starts_at=starts_at,
            ends_at=ends_at,
            suitcase=suitcase,
            handluggage=handluggage,
            otherluggage=otherluggage,
            passengers=passengers,
            status=RideStatus.ASSIGNED  # Initial status is assigned
        )
        db.add(ride)
        db.commit()
        db.refresh(ride)
        return ride

    @staticmethod
    def get_ride(db: Session, ride_id: UUID):
        return db.query(Ride).filter(Ride.id == ride_id).first()

    @staticmethod
    def get_rides_by_status(db: Session, status: RideStatus, skip: int = 0, limit: int = 100) -> List[Ride]:
        return db.query(Ride).filter(Ride.status == status).offset(skip).limit(limit).all()

    @staticmethod
    def update_ride_status(db: Session, ride_id: UUID, new_status: RideStatus):
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if ride:
            ride.status = new_status
            db.commit()
            db.refresh(ride)
            return ride
        return None

    @staticmethod
    def update_ride_location(db: Session, ride_id: UUID, startlocation: Optional[dict] = None, endlocation: Optional[dict] = None):
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if ride:
            if startlocation:
                ride.startlocation = startlocation
            if endlocation:
                ride.endlocation = endlocation
            db.commit()
            db.refresh(ride)
            return ride
        return None

    @staticmethod
    def delete_ride(db: Session, ride_id: UUID):
        ride = db.query(Ride).filter(Ride.id == ride_id).first()
        if ride:
            db.delete(ride)
            db.commit()
            return ride
        return None
