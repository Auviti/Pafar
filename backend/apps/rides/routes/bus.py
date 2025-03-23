from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.rides.schemas.services.bus import BusService
from app.rides.schemas.models.bus import Bus, BusStatus
from .dependencies import get_db

router = APIRouter()

@router.post("/buses/", response_model=Bus)
def create_bus(bus_number: str, capacity: int, driver_id: UUID, route: str = None, db: Session = Depends(get_db)):
    bus = BusService.create_bus(db, bus_number, capacity, driver_id, route)
    return bus

@router.get("/buses/{bus_id}", response_model=Bus)
def get_bus(bus_id: UUID, db: Session = Depends(get_db)):
    bus = BusService.get_bus(db, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

@router.get("/buses/", response_model=List[Bus])
def get_all_buses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    buses = BusService.get_all_buses(db, skip, limit)
    return buses

@router.put("/buses/{bus_id}/status", response_model=Bus)
def update_bus_status(bus_id: UUID, status: BusStatus, db: Session = Depends(get_db)):
    bus = BusService.update_bus_status(db, bus_id, status)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

@router.delete("/buses/{bus_id}", response_model=Bus)
def delete_bus(bus_id: UUID, db: Session = Depends(get_db)):
    bus = BusService.delete_bus(db, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus
