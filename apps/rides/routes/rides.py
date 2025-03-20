from fastapi import APIRouter, Depends, HTTPException
from app.rides.schemas.rides import RideStatusCreate, RideStatusRead
from app.rides.services.rides import create_ride_status, get_ride_statuses, get_ride_status_by_id, update_ride_status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from uuid import UUID
from typing import Optional

router = APIRouter()

# Route to create a new ride status
@router.post("/rides/", response_model=RideStatusRead)
async def create_ride_status_route(ride_status: RideStatusCreate, db: AsyncSession = Depends(get_db)):
    return await create_ride_status(db=db, ride_status=ride_status)

# Route to get all ride statuses
@router.get("/rides/", response_model=list[RideStatusRead])
async def get_all_ride_statuses_route(db: AsyncSession = Depends(get_db)):
    return await get_ride_statuses(db)

# Route to get a ride status by ID
@router.get("/rides/{ride_status_id}", response_model=RideStatusRead)
async def get_ride_status_by_id_route(ride_status_id: UUID, db: AsyncSession = Depends(get_db)):
    return await get_ride_status_by_id(db=db, ride_status_id=ride_status_id)

# Route to update ride status
@router.put("/rides/{ride_status_id}/status", response_model=RideStatusRead)
async def update_ride_status_route(ride_status_id: UUID, status: str, location: Optional[dict] = None, db: AsyncSession = Depends(get_db)):
    return await update_ride_status(db=db, ride_status_id=ride_status_id, status=status, location=location)
