from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List
from app.rides.schemas.bus import BusOut, SeatOut,BusIn
from app.rides.schemas.models import Bus, Seat
from app.database import get_db1
from fastapi import HTTPException

# BusService
class BusService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_bus_by_id(self, bus_id: UUID) -> BusOut:
        """Fetch bus details by bus ID."""
        async with self.db.begin():
            result = await self.db.execute(select(Bus).filter(Bus.id == bus_id))
            bus = result.scalars().first()
            if not bus:
                raise HTTPException(status_code=404, detail=f"Bus with ID {bus_id} not found")
            return BusOut.from_orm(bus)

    async def get_all_buses(self) -> List[BusOut]:
        """Fetch all buses."""
        async with self.db.begin():
            result = await self.db.execute(select(Bus))
            buses = result.scalars().all()
            return [BusOut.from_orm(bus) for bus in buses]

    async def get_seats_by_bus(self, bus_id: UUID) -> List[SeatOut]:
        """Fetch all seats for a particular bus."""
        async with self.db.begin():
            result = await self.db.execute(select(Seat).filter(Seat.bus_id == bus_id))
            seats = result.scalars().all()
            return [SeatOut.from_orm(seat) for seat in seats]
    
    async def create_bus_and_seats(self, bus_in: BusIn) -> BusOut:
        """Create a bus and its associated seats."""
        # Create the bus instance
        bus = Bus(
            bus_number=bus_in.bus_number,
            capacity=bus_in.capacity,
            driver_id=bus_in.driver_id,
            status=bus_in.status,
        )
        
        # Create seats based on bus capacity
        seats = []
        for i in range(1, bus_in.capacity + 1):
            seat = Seat(
                seat_number=f"{i}",
                bus_id=bus.id,
                available=True  # all seats are available initially
            )
            seats.append(seat)
        
        # Add bus and seats to the session
        self.db.add(bus)
        self.db.add_all(seats)

        # Commit to the database
        await self.db.commit()
        await self.db.refresh(bus)  # Refresh to get the bus ID
        return BusOut.from_orm(bus)

# SeatService
class SeatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_seat_by_id(self, seat_id: int) -> SeatOut:
        """Fetch seat details by seat ID."""
        async with self.db.begin():
            result = await self.db.execute(select(Seat).filter(Seat.id == seat_id))
            seat = result.scalars().first()
            if not seat:
                raise HTTPException(status_code=404, detail=f"Seat with ID {seat_id} not found")
            return SeatOut.from_orm(seat)

    async def get_seats_by_bus(self, bus_id: UUID) -> List[SeatOut]:
        """Fetch all seats for a particular bus."""
        async with self.db.begin():
            result = await self.db.execute(select(Seat).filter(Seat.bus_id == bus_id))
            seats = result.scalars().all()
            return [SeatOut.from_orm(seat) for seat in seats]

    async def get_seats_by_user(self, user_id: UUID) -> List[SeatOut]:
        """Fetch all seats booked by a user."""
        async with self.db.begin():
            result = await self.db.execute(select(Seat).filter(Seat.user_id == user_id))
            seats = result.scalars().all()
            return [SeatOut.from_orm(seat) for seat in seats]