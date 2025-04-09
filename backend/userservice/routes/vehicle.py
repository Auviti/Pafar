from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from uuid import UUID
from services.vehicle import VehicleTypeService, VehicleService  # Assuming these are your service layers
from schemas.vehicle import VehicleTypeCreate, VehicleCreate  # Your Pydantic models
from core.database import get_db1
from core.utils.reponse import Response

router = APIRouter()

# VehicleType Routes
@router.post("/vehicle_types")
async def create_vehicle_type(
    vehicle_type: VehicleTypeCreate, db: AsyncSession = Depends(get_db1)
):
    try:
        vehicle_type_data = await VehicleTypeService.create_vehicle_type(db, vehicle_type)
        return Response(data=vehicle_type_data.to_dict(), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

@router.get("/vehicle_types")
async def get_vehicle_types(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db1)):
    try:
        vehicle_types = await VehicleTypeService.get_vehicle_types(db, skip, limit)
        return Response(data=vehicle_types, code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

# Vehicle Routes
@router.post("/vehicles", response_model=Response)
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db1)):
    try:
        vehicle_data = await VehicleService.create_vehicle(db, vehicle)
        return Response(data=vehicle_data.to_dict(), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)

@router.get("/vehicles/{vehicle_id}", response_model=Response)
async def get_vehicle(vehicle_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        vehicle = await VehicleService.get_vehicle_by_id(db, vehicle_id)
        if not vehicle:
            return Response(message="Vehicle not found", success=False, code=404)
        return Response(data=vehicle.to_dict(), code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)
