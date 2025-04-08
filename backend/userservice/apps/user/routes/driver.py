from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from uuid import UUID
from apps.user.services.driver import VehicleTypeService, DriverService, VehicleService  # Assuming these are your service layers
from apps.user.schemas.driver import VehicleTypeCreate, DriverCreate, VehicleCreate  # Your Pydantic models
from core.database import get_db1
from core.utils.reponse import Response

router = APIRouter()

# VehicleType Routes
@router.post("/vehicle_types")
async def create_vehicle_type(
    vehicle_type: VehicleTypeCreate, db: AsyncSession = Depends(get_db)
):
    try:
        vehicle_type_data = await VehicleTypeService.create_vehicle_type(db, vehicle_type)
        return Response(data=vehicle_type_data.to_dict(), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

@router.get("/vehicle_types")
async def get_vehicle_types(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    try:
        vehicle_types = await VehicleTypeService.get_vehicle_types(db, skip, limit)
        return Response(data=vehicle_types, code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

# Driver Routes
@router.post("/drivers")
async def create_driver(driver: DriverCreate, db: AsyncSession = Depends(get_db)):
    try:
        driver_data = await DriverService.create_driver(db, driver)
        return Response(data=driver_data.to_dict(), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

@router.get("/drivers/{driver_id}", response_model=Response)
async def get_driver(driver_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        driver = await DriverService.get_driver_by_id(db, driver_id)
        if not driver:
            return Response(message="Driver not found", success=False, code=404)
        return Response(data=driver.to_dict(), code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

# Vehicle Routes
@router.post("/vehicles", response_model=Response)
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db)):
    try:
        vehicle_data = await VehicleService.create_vehicle(db, vehicle)
        return Response(data=vehicle_data.to_dict(), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

@router.get("/vehicles/{vehicle_id}", response_model=Response)
async def get_vehicle(vehicle_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        vehicle = await VehicleService.get_vehicle_by_id(db, vehicle_id)
        if not vehicle:
            return Response(message="Vehicle not found", success=False, code=404)
        return Response(data=vehicle.to_dict(), code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)
