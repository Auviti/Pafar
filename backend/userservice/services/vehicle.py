from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.vehicle import Vehicle,VehicleType
from schemas.vehicle import VehicleCreate,VehicleTypeCreate
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from core.utils.auth.jwt_auth import JWTManager
from core.utils.reponse import Response
from core.utils.encryption import PasswordManager

class VehicleTypeService:

    @staticmethod
    async def create_vehicle_type(db: AsyncSession, vehicle_type: VehicleTypeCreate):
        db_vehicle_type = VehicleType(
            name=vehicle_type.name,
            description=vehicle_type.description
        )
        db.add(db_vehicle_type)
        await db.commit()
        await db.refresh(db_vehicle_type)
        return db_vehicle_type

    @staticmethod
    async def get_vehicle_types(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(VehicleType).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_vehicle_type_by_id(db: AsyncSession, vehicle_type_id: UUID):
        result = await db.execute(select(VehicleType).filter(VehicleType.id == vehicle_type_id))
        return result.scalars().first()

    @staticmethod
    async def update_vehicle_type(db: AsyncSession, vehicle_type_id: UUID, vehicle_type: VehicleTypeCreate):
        db_vehicle_type = await db.execute(select(VehicleType).filter(VehicleType.id == vehicle_type_id))
        db_vehicle_type = db_vehicle_type.scalars().first()
        if db_vehicle_type:
            db_vehicle_type.name = vehicle_type.name
            db_vehicle_type.description = vehicle_type.description
            await db.commit()
            await db.refresh(db_vehicle_type)
        return db_vehicle_type

    @staticmethod
    async def delete_vehicle_type(db: AsyncSession, vehicle_type_id: UUID):
        db_vehicle_type = await db.execute(select(VehicleType).filter(VehicleType.id == vehicle_type_id))
        db_vehicle_type = db_vehicle_type.scalars().first()
        if db_vehicle_type:
            await db.delete(db_vehicle_type)
            await db.commit()
        return db_vehicle_type

class VehicleService:

    @staticmethod
    async def create_vehicle(db: AsyncSession, vehicle: VehicleCreate):
        db_vehicle = Vehicle(
            license_number=vehicle.license_number,
            model=vehicle.model,
            year=vehicle.year,
            color=vehicle.color,
            vehicle_type_id=vehicle.vehicle_type_id,
            driver_id=vehicle.driver_id
        )
        db.add(db_vehicle)
        await db.commit()
        await db.refresh(db_vehicle)
        return db_vehicle

    @staticmethod
    async def get_vehicles(db: AsyncSession, skip: int = 0, limit: int = 100):
        result = await db.execute(select(Vehicle).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_vehicle_by_id(db: AsyncSession, vehicle_id: UUID):
        result = await db.execute(select(Vehicle).filter(Vehicle.id == vehicle_id))
        return result.scalars().first()

    @staticmethod
    async def update_vehicle(db: AsyncSession, vehicle_id: UUID, vehicle: VehicleCreate):
        result = await db.execute(select(Vehicle).filter(Vehicle.id == vehicle_id))
        db_vehicle = result.scalars().first()
        if db_vehicle:
            db_vehicle.license_number = vehicle.license_number
            db_vehicle.model = vehicle.model
            db_vehicle.year = vehicle.year
            db_vehicle.color = vehicle.color
            db_vehicle.vehicle_type_id = vehicle.vehicle_type_id
            db_vehicle.driver_id = vehicle.driver_id
            await db.commit()
            await db.refresh(db_vehicle)
        return db_vehicle

    @staticmethod
    async def delete_vehicle(db: AsyncSession, vehicle_id: UUID):
        result = await db.execute(select(Vehicle).filter(Vehicle.id == vehicle_id))
        db_vehicle = result.scalars().first()
        if db_vehicle:
            await db.delete(db_vehicle)
            await db.commit()
        return db_vehicle
