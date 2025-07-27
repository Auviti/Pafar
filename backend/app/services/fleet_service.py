"""
Fleet management service layer.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.fleet import Terminal, Route, Bus, Trip
from app.models.user import User
from app.schemas.fleet import (
    TerminalCreate, TerminalUpdate,
    RouteCreate, RouteUpdate,
    BusCreate, BusUpdate,
    TripCreate, TripUpdate
)


class TerminalService:
    """Service for terminal management operations."""

    @staticmethod
    async def create_terminal(db: AsyncSession, terminal_data: TerminalCreate) -> Terminal:
        """Create a new terminal."""
        terminal = Terminal(**terminal_data.model_dump())
        db.add(terminal)
        await db.commit()
        await db.refresh(terminal)
        return terminal

    @staticmethod
    async def get_terminal(db: AsyncSession, terminal_id: UUID) -> Optional[Terminal]:
        """Get a terminal by ID."""
        result = await db.execute(select(Terminal).where(Terminal.id == terminal_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_terminals(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Terminal], int]:
        """Get terminals with optional filtering."""
        query = select(Terminal)
        count_query = select(func.count(Terminal.id))

        # Apply filters
        filters = []
        if city:
            filters.append(Terminal.city.ilike(f"%{city}%"))
        if is_active is not None:
            filters.append(Terminal.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get terminals with pagination
        query = query.offset(skip).limit(limit).order_by(Terminal.created_at.desc())
        result = await db.execute(query)
        terminals = result.scalars().all()

        return list(terminals), total

    @staticmethod
    async def update_terminal(
        db: AsyncSession, 
        terminal_id: UUID, 
        terminal_data: TerminalUpdate
    ) -> Optional[Terminal]:
        """Update a terminal."""
        terminal = await TerminalService.get_terminal(db, terminal_id)
        if not terminal:
            return None

        update_data = terminal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(terminal, field, value)

        await db.commit()
        await db.refresh(terminal)
        return terminal

    @staticmethod
    async def delete_terminal(db: AsyncSession, terminal_id: UUID) -> bool:
        """Delete a terminal (soft delete by setting is_active=False)."""
        terminal = await TerminalService.get_terminal(db, terminal_id)
        if not terminal:
            return False

        # Check if terminal is used in any routes
        route_check = await db.execute(
            select(Route).where(
                or_(
                    Route.origin_terminal_id == terminal_id,
                    Route.destination_terminal_id == terminal_id
                )
            ).limit(1)
        )
        if route_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete terminal that is used in routes"
            )

        terminal.is_active = False
        await db.commit()
        return True


class RouteService:
    """Service for route management operations."""

    @staticmethod
    async def create_route(db: AsyncSession, route_data: RouteCreate) -> Route:
        """Create a new route."""
        # Verify terminals exist
        origin_terminal = await TerminalService.get_terminal(db, route_data.origin_terminal_id)
        destination_terminal = await TerminalService.get_terminal(db, route_data.destination_terminal_id)
        
        if not origin_terminal or not destination_terminal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both terminals not found"
            )

        if not origin_terminal.is_active or not destination_terminal.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create route with inactive terminals"
            )

        route = Route(**route_data.model_dump())
        db.add(route)
        await db.commit()
        await db.refresh(route)
        return route

    @staticmethod
    async def get_route(db: AsyncSession, route_id: UUID) -> Optional[Route]:
        """Get a route by ID with related terminals."""
        result = await db.execute(
            select(Route)
            .options(
                selectinload(Route.origin_terminal),
                selectinload(Route.destination_terminal)
            )
            .where(Route.id == route_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_routes(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        origin_terminal_id: Optional[UUID] = None,
        destination_terminal_id: Optional[UUID] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Route], int]:
        """Get routes with optional filtering."""
        query = select(Route).options(
            selectinload(Route.origin_terminal),
            selectinload(Route.destination_terminal)
        )
        count_query = select(func.count(Route.id))

        # Apply filters
        filters = []
        if origin_terminal_id:
            filters.append(Route.origin_terminal_id == origin_terminal_id)
        if destination_terminal_id:
            filters.append(Route.destination_terminal_id == destination_terminal_id)
        if is_active is not None:
            filters.append(Route.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get routes with pagination
        query = query.offset(skip).limit(limit).order_by(Route.created_at.desc())
        result = await db.execute(query)
        routes = result.scalars().all()

        return list(routes), total

    @staticmethod
    async def update_route(
        db: AsyncSession, 
        route_id: UUID, 
        route_data: RouteUpdate
    ) -> Optional[Route]:
        """Update a route."""
        route = await RouteService.get_route(db, route_id)
        if not route:
            return None

        update_data = route_data.model_dump(exclude_unset=True)
        
        # Verify terminals if being updated
        if 'origin_terminal_id' in update_data or 'destination_terminal_id' in update_data:
            origin_id = update_data.get('origin_terminal_id', route.origin_terminal_id)
            dest_id = update_data.get('destination_terminal_id', route.destination_terminal_id)
            
            origin_terminal = await TerminalService.get_terminal(db, origin_id)
            destination_terminal = await TerminalService.get_terminal(db, dest_id)
            
            if not origin_terminal or not destination_terminal:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or both terminals not found"
                )

        for field, value in update_data.items():
            setattr(route, field, value)

        await db.commit()
        await db.refresh(route)
        return route

    @staticmethod
    async def delete_route(db: AsyncSession, route_id: UUID) -> bool:
        """Delete a route (soft delete by setting is_active=False)."""
        route = await RouteService.get_route(db, route_id)
        if not route:
            return False

        # Check if route is used in any trips
        trip_check = await db.execute(
            select(Trip).where(Trip.route_id == route_id).limit(1)
        )
        if trip_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete route that has scheduled trips"
            )

        route.is_active = False
        await db.commit()
        return True


class BusService:
    """Service for bus management operations."""

    @staticmethod
    async def create_bus(db: AsyncSession, bus_data: BusCreate) -> Bus:
        """Create a new bus."""
        # Check if license plate already exists
        existing_bus = await db.execute(
            select(Bus).where(Bus.license_plate == bus_data.license_plate)
        )
        if existing_bus.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bus with this license plate already exists"
            )

        bus = Bus(**bus_data.model_dump())
        db.add(bus)
        await db.commit()
        await db.refresh(bus)
        return bus

    @staticmethod
    async def get_bus(db: AsyncSession, bus_id: UUID) -> Optional[Bus]:
        """Get a bus by ID."""
        result = await db.execute(select(Bus).where(Bus.id == bus_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_buses(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        license_plate: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[Bus], int]:
        """Get buses with optional filtering."""
        query = select(Bus)
        count_query = select(func.count(Bus.id))

        # Apply filters
        filters = []
        if license_plate:
            filters.append(Bus.license_plate.ilike(f"%{license_plate}%"))
        if is_active is not None:
            filters.append(Bus.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get buses with pagination
        query = query.offset(skip).limit(limit).order_by(Bus.created_at.desc())
        result = await db.execute(query)
        buses = result.scalars().all()

        return list(buses), total

    @staticmethod
    async def update_bus(
        db: AsyncSession, 
        bus_id: UUID, 
        bus_data: BusUpdate
    ) -> Optional[Bus]:
        """Update a bus."""
        bus = await BusService.get_bus(db, bus_id)
        if not bus:
            return None

        update_data = bus_data.model_dump(exclude_unset=True)
        
        # Check license plate uniqueness if being updated
        if 'license_plate' in update_data:
            existing_bus = await db.execute(
                select(Bus).where(
                    and_(
                        Bus.license_plate == update_data['license_plate'],
                        Bus.id != bus_id
                    )
                )
            )
            if existing_bus.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bus with this license plate already exists"
                )

        for field, value in update_data.items():
            setattr(bus, field, value)

        await db.commit()
        await db.refresh(bus)
        return bus

    @staticmethod
    async def delete_bus(db: AsyncSession, bus_id: UUID) -> bool:
        """Delete a bus (soft delete by setting is_active=False)."""
        bus = await BusService.get_bus(db, bus_id)
        if not bus:
            return False

        # Check if bus is used in any trips
        trip_check = await db.execute(
            select(Trip).where(Trip.bus_id == bus_id).limit(1)
        )
        if trip_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete bus that has scheduled trips"
            )

        bus.is_active = False
        await db.commit()
        return True


class TripService:
    """Service for trip management operations."""

    @staticmethod
    async def create_trip(db: AsyncSession, trip_data: TripCreate) -> Trip:
        """Create a new trip."""
        # Verify route exists
        route = await RouteService.get_route(db, trip_data.route_id)
        if not route or not route.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found or inactive"
            )

        # Verify bus exists
        bus = await BusService.get_bus(db, trip_data.bus_id)
        if not bus or not bus.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bus not found or inactive"
            )

        # Verify driver exists and has driver role
        driver_result = await db.execute(
            select(User).where(
                and_(
                    User.id == trip_data.driver_id,
                    User.role == "driver",
                    User.is_active == True
                )
            )
        )
        driver = driver_result.scalar_one_or_none()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver not found or not active"
            )

        # Set available seats to bus capacity if not provided
        if trip_data.available_seats is None:
            trip_data.available_seats = bus.capacity

        trip = Trip(**trip_data.model_dump())
        db.add(trip)
        await db.commit()
        await db.refresh(trip)
        return trip

    @staticmethod
    async def get_trip(db: AsyncSession, trip_id: UUID) -> Optional[Trip]:
        """Get a trip by ID with related data."""
        result = await db.execute(
            select(Trip)
            .options(
                selectinload(Trip.route).selectinload(Route.origin_terminal),
                selectinload(Trip.route).selectinload(Route.destination_terminal),
                selectinload(Trip.bus)
            )
            .where(Trip.id == trip_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_trips(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        route_id: Optional[UUID] = None,
        bus_id: Optional[UUID] = None,
        driver_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> tuple[List[Trip], int]:
        """Get trips with optional filtering."""
        query = select(Trip).options(
            selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Trip.bus)
        )
        count_query = select(func.count(Trip.id))

        # Apply filters
        filters = []
        if route_id:
            filters.append(Trip.route_id == route_id)
        if bus_id:
            filters.append(Trip.bus_id == bus_id)
        if driver_id:
            filters.append(Trip.driver_id == driver_id)
        if status:
            filters.append(Trip.status == status)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get trips with pagination
        query = query.offset(skip).limit(limit).order_by(Trip.departure_time.asc())
        result = await db.execute(query)
        trips = result.scalars().all()

        return list(trips), total

    @staticmethod
    async def update_trip(
        db: AsyncSession, 
        trip_id: UUID, 
        trip_data: TripUpdate
    ) -> Optional[Trip]:
        """Update a trip."""
        trip = await TripService.get_trip(db, trip_id)
        if not trip:
            return None

        update_data = trip_data.model_dump(exclude_unset=True)
        
        # Verify route if being updated
        if 'route_id' in update_data:
            route = await RouteService.get_route(db, update_data['route_id'])
            if not route or not route.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Route not found or inactive"
                )

        # Verify bus if being updated
        if 'bus_id' in update_data:
            bus = await BusService.get_bus(db, update_data['bus_id'])
            if not bus or not bus.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bus not found or inactive"
                )

        # Verify driver if being updated
        if 'driver_id' in update_data:
            driver_result = await db.execute(
                select(User).where(
                    and_(
                        User.id == update_data['driver_id'],
                        User.role == "driver",
                        User.is_active == True
                    )
                )
            )
            driver = driver_result.scalar_one_or_none()
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Driver not found or not active"
                )

        for field, value in update_data.items():
            setattr(trip, field, value)

        await db.commit()
        await db.refresh(trip)
        return trip

    @staticmethod
    async def delete_trip(db: AsyncSession, trip_id: UUID) -> bool:
        """Delete a trip (only if no bookings exist)."""
        trip = await TripService.get_trip(db, trip_id)
        if not trip:
            return False

        # Check if trip has any bookings
        from app.models.booking import Booking
        booking_check = await db.execute(
            select(Booking).where(Booking.trip_id == trip_id).limit(1)
        )
        if booking_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete trip that has bookings"
            )

        await db.delete(trip)
        await db.commit()
        return True