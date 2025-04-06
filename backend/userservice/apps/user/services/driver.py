from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.user.models.driver import Driver, Vehicle
from app.user.schemas.driver import DriverCreate, VehicleCreate
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Service to create a new driver
async def create_driver(db: AsyncSession, driver: DriverCreate) -> Driver:
    try:
        new_driver = Driver(
            user_id=driver.user_id,
            rating=driver.rating
        )
        db.add(new_driver)
        await db.commit()
        await db.refresh(new_driver)
        return new_driver
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to create a new vehicle and associate it with a driver
async def create_vehicle(db: AsyncSession, driver_id: UUID, vehicle: VehicleCreate) -> Vehicle:
    try:
        new_vehicle = Vehicle(
            driver_id=driver_id,
            vehicle_type=vehicle.vehicle_type,
            license_number=vehicle.license_number,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color
        )
        db.add(new_vehicle)
        await db.commit()
        await db.refresh(new_vehicle)
        return new_vehicle
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get all drivers
async def get_drivers(db: AsyncSession) -> list[Driver]:
    try:
        result = await db.execute(select(Driver))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get a driver by ID
async def get_driver_by_id(db: AsyncSession, driver_id: UUID) -> Driver:
    try:
        result = await db.execute(select(Driver).filter(Driver.id == driver_id))
        driver = result.scalars().first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        return driver
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Service to get a vehicle by driver ID
async def get_vehicle_by_driver(db: AsyncSession, driver_id: UUID) -> Vehicle:
    try:
        result = await db.execute(select(Vehicle).filter(Vehicle.driver_id == driver_id))
        vehicle = result.scalars().first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return vehicle
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))
