from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from uuid import UUID
from services.vehicle import VehicleTypeService, VehicleService  # Assuming these are your service layers
from schemas.vehicle import VehicleTypeCreate,VehicleTypeResponse, VehicleCreate,VehicleResponse  # Your Pydantic models
from core.database import get_db1
from core.utils.reponse import Response

router = APIRouter()

# VehicleType Routes
@router.post("/vehicle_types", response_model=Response)
async def create_vehicle_type(
    vehicle_type: VehicleTypeCreate, db: AsyncSession = Depends(get_db1)
):
    try:
        vehicle_type_data = await VehicleTypeService.create_vehicle_type(db, vehicle_type)
        return Response(data=VehicleTypeResponse.from_orm(vehicle_type_data), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


@router.get("/vehicle_types", response_model=Response)
async def get_vehicle_types(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db1)):
    try:
        vehicle_types = await VehicleTypeService.get_vehicle_types(db, skip, limit)
        return Response(
            data=[VehicleTypeResponse.from_orm(vt) for vt in vehicle_types],
            code=200
        )
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


@router.get("/vehicle_types/{vehicle_type_id}", response_model=Response)
async def get_vehicle_type_by_id(vehicle_type_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        vt = await VehicleTypeService.get_vehicle_type_by_id(db, vehicle_type_id)
        if vt:
            return Response(data=VehicleTypeResponse.from_orm(vt), code=200)
        raise HTTPException(status_code=404, detail="Vehicle type not found")
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


@router.put("/vehicle_types/{vehicle_type_id}", response_model=Response)
async def update_vehicle_type(
    vehicle_type_id: UUID,
    vehicle_type: VehicleTypeCreate,
    db: AsyncSession = Depends(get_db1)
):
    try:
        updated_vt = await VehicleTypeService.update_vehicle_type(db, vehicle_type_id, vehicle_type)
        if updated_vt:
            return Response(data=VehicleTypeResponse.from_orm(updated_vt), code=200)
        raise HTTPException(status_code=404, detail="Vehicle type not found")
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


@router.delete("/vehicle_types/{vehicle_type_id}", response_model=Response)
async def delete_vehicle_type(vehicle_type_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        deleted_vt = await VehicleTypeService.delete_vehicle_type(db, vehicle_type_id)
        if deleted_vt:
            return Response(message="Vehicle type deleted successfully", code=204)
        raise HTTPException(status_code=404, detail="Vehicle type not found")
    except Exception as error:
        return Response(message=str(error), success=False, code=500)



# Create a vehicle
@router.post("/vehicles", response_model=Response)
async def create_vehicle(vehicle: VehicleCreate, db: AsyncSession = Depends(get_db1)):
    try:
        vehicle_data = await VehicleService.create_vehicle(db, vehicle)
        return Response(data=VehicleResponse.from_orm(vehicle_data), code=201)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


# Get a vehicle by ID
@router.get("/vehicles/{vehicle_id}", response_model=Response)
async def get_vehicle(vehicle_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        vehicle = await VehicleService.get_vehicle_by_id(db, vehicle_id)
        if not vehicle:
            return Response(message="Vehicle not found", success=False, code=404)
        return Response(data=VehicleResponse.from_orm(vehicle), code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


# Get all vehicles with pagination
@router.get("/vehicles", response_model=Response)
async def get_vehicles(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db1)):
    try:
        vehicles = await VehicleService.get_vehicles(db, skip, limit)
        return Response(data=[VehicleResponse.from_orm(v) for v in vehicles], code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


# Update a vehicle by ID
@router.put("/vehicles/{vehicle_id}", response_model=Response)
async def update_vehicle(vehicle_id: UUID, vehicle: VehicleCreate, db: AsyncSession = Depends(get_db1)):
    try:
        updated_vehicle = await VehicleService.update_vehicle(db, vehicle_id, vehicle)
        if not updated_vehicle:
            return Response(message="Vehicle not found", success=False, code=404)
        return Response(data=VehicleResponse.from_orm(updated_vehicle), code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)


# Delete a vehicle by ID
@router.delete("/vehicles/{vehicle_id}", response_model=Response)
async def delete_vehicle(vehicle_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        deleted_vehicle = await VehicleService.delete_vehicle(db, vehicle_id)
        if not deleted_vehicle:
            return Response(message="Vehicle not found", success=False, code=404)
        return Response(message="Vehicle deleted successfully", code=204)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)
