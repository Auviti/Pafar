from fastapi import APIRouter, Depends, HTTPException
from app.driver.schemas.driver import DriverCreate, DriverRead, VehicleCreate, VehicleRead
from app.driver.services.driver import create_driver, create_vehicle, get_drivers, get_driver_by_id, get_vehicle_by_driver
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from uuid import UUID

router = APIRouter()

# Route to create a new driver
@router.post("/driver/", response_model=DriverRead)
async def create_driver_route(driver: DriverCreate, db: AsyncSession = Depends(get_db)):
    return await create_driver(db=db, driver=driver)

# Route to get all drivers
@router.get("/driver/", response_model=list[DriverRead])
async def get_all_drivers_route(db: AsyncSession = Depends(get_db)):
    return await get_drivers(db)

# Route to get a driver by ID
@router.get("/driver/{driver_id}", response_model=DriverRead)
async def get_driver_by_id_route(driver_id: UUID, db: AsyncSession = Depends(get_db)):
    return await get_driver_by_id(db=db, driver_id=driver_id)

# Route to create a new vehicle for a specific driver
@router.post("/driver/{driver_id}/vehicle", response_model=VehicleRead)
async def create_vehicle_route(driver_id: UUID, vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    return await create_vehicle(db=db, driver_id=driver_id, vehicle=vehicle)

# Route to get the vehicle of a specific driver
@router.get("/driver/{driver_id}/vehicle", response_model=VehicleRead)
async def get_vehicle_route(driver_id: UUID, db: AsyncSession = Depends(get_db)):
    return await get_vehicle_by_driver(db=db, driver_id=driver_id)
