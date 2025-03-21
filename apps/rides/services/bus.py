from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from app.rides.schemas.models import Bus, BusStatus
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from core.database import get_db1
from app.rides.schemas.services import BusService

router = APIRouter()

@router.post("/buses/", response_model=Bus)
def create_bus(bus_number: str, capacity: int, driver_id: UUID, route: str = None, db: Session = Depends(get_db)):
    bus = BusService.create_bus(db, bus_number, capacity, driver_id, route)
    return bus

@router.put("/buses/{bus_id}/route", response_model=Bus)
def update_route(bus_id: UUID, new_route: str, db: Session = Depends(get_db)):
    bus = BusService.update_bus_route(db, bus_id, new_route)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

@router.get("/buses/{bus_id}/route", response_model=str)
def get_route(bus_id: UUID, db: Session = Depends(get_db)):
    route = BusService.get_bus_route(db, bus_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.get("/buses/routes", response_model=list)
def get_all_routes(db: Session = Depends(get_db)):
    return BusService.get_all_routes(db)

@router.delete("/buses/{bus_id}", response_model=Bus)
def delete_bus(bus_id: UUID, db: Session = Depends(get_db)):
    bus = BusService.delete_bus(db, bus_id)
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

