"""
Unit tests for fleet management services.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.user import User, UserRole
from app.schemas.fleet import (
    TerminalCreate, TerminalUpdate,
    RouteCreate, RouteUpdate,
    BusCreate, BusUpdate,
    TripCreate, TripUpdate
)
from app.services.fleet_service import (
    TerminalService, RouteService, BusService, TripService
)


class TestTerminalService:
    """Test cases for TerminalService."""

    @pytest.mark.asyncio
    async def test_create_terminal(self, db_session: AsyncSession):
        """Test creating a new terminal."""
        terminal_data = TerminalCreate(
            name="Central Station",
            city="New York",
            address="123 Main St",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        
        terminal = await TerminalService.create_terminal(db_session, terminal_data)
        
        assert terminal.id is not None
        assert terminal.name == "Central Station"
        assert terminal.city == "New York"
        assert terminal.address == "123 Main St"
        assert terminal.latitude == Decimal("40.7128")
        assert terminal.longitude == Decimal("-74.0060")
        assert terminal.is_active is True
        assert terminal.created_at is not None

    @pytest.mark.asyncio
    async def test_get_terminal(self, db_session: AsyncSession):
        """Test getting a terminal by ID."""
        # Create a terminal first
        terminal_data = TerminalCreate(
            name="Test Terminal",
            city="Test City"
        )
        created_terminal = await TerminalService.create_terminal(db_session, terminal_data)
        
        # Get the terminal
        retrieved_terminal = await TerminalService.get_terminal(db_session, created_terminal.id)
        
        assert retrieved_terminal is not None
        assert retrieved_terminal.id == created_terminal.id
        assert retrieved_terminal.name == "Test Terminal"

    @pytest.mark.asyncio
    async def test_get_terminal_not_found(self, db_session: AsyncSession):
        """Test getting a non-existent terminal."""
        non_existent_id = uuid4()
        terminal = await TerminalService.get_terminal(db_session, non_existent_id)
        assert terminal is None

    @pytest.mark.asyncio
    async def test_get_terminals_with_filters(self, db_session: AsyncSession):
        """Test getting terminals with filters."""
        # Create test terminals
        terminal1_data = TerminalCreate(name="Terminal 1", city="New York")
        terminal2_data = TerminalCreate(name="Terminal 2", city="Boston")
        terminal3_data = TerminalCreate(name="Terminal 3", city="New York", is_active=False)
        
        await TerminalService.create_terminal(db_session, terminal1_data)
        await TerminalService.create_terminal(db_session, terminal2_data)
        await TerminalService.create_terminal(db_session, terminal3_data)
        
        # Test city filter
        terminals, total = await TerminalService.get_terminals(db_session, city="New York")
        assert total == 2
        assert all(t.city == "New York" for t in terminals)
        
        # Test active filter
        terminals, total = await TerminalService.get_terminals(db_session, is_active=True)
        assert total == 2
        assert all(t.is_active for t in terminals)

    @pytest.mark.asyncio
    async def test_update_terminal(self, db_session: AsyncSession):
        """Test updating a terminal."""
        # Create a terminal
        terminal_data = TerminalCreate(name="Original Name", city="Original City")
        terminal = await TerminalService.create_terminal(db_session, terminal_data)
        
        # Update the terminal
        update_data = TerminalUpdate(name="Updated Name", city="Updated City")
        updated_terminal = await TerminalService.update_terminal(db_session, terminal.id, update_data)
        
        assert updated_terminal is not None
        assert updated_terminal.name == "Updated Name"
        assert updated_terminal.city == "Updated City"

    @pytest.mark.asyncio
    async def test_delete_terminal(self, db_session: AsyncSession):
        """Test deleting a terminal."""
        # Create a terminal
        terminal_data = TerminalCreate(name="To Delete", city="Test City")
        terminal = await TerminalService.create_terminal(db_session, terminal_data)
        
        # Delete the terminal
        success = await TerminalService.delete_terminal(db_session, terminal.id)
        assert success is True
        
        # Verify it's soft deleted
        deleted_terminal = await TerminalService.get_terminal(db_session, terminal.id)
        assert deleted_terminal.is_active is False


class TestRouteService:
    """Test cases for RouteService."""

    @pytest.mark.asyncio
    async def test_create_route(self, db_session: AsyncSession):
        """Test creating a new route."""
        # Create terminals first
        origin_data = TerminalCreate(name="Origin Terminal", city="City A")
        dest_data = TerminalCreate(name="Destination Terminal", city="City B")
        
        origin = await TerminalService.create_terminal(db_session, origin_data)
        destination = await TerminalService.create_terminal(db_session, dest_data)
        
        # Create route
        route_data = RouteCreate(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            distance_km=Decimal("150.5"),
            estimated_duration_minutes=180,
            base_fare=Decimal("25.00")
        )
        
        route = await RouteService.create_route(db_session, route_data)
        
        assert route.id is not None
        assert route.origin_terminal_id == origin.id
        assert route.destination_terminal_id == destination.id
        assert route.distance_km == Decimal("150.5")
        assert route.estimated_duration_minutes == 180
        assert route.base_fare == Decimal("25.00")

    @pytest.mark.asyncio
    async def test_create_route_with_invalid_terminals(self, db_session: AsyncSession):
        """Test creating a route with non-existent terminals."""
        route_data = RouteCreate(
            origin_terminal_id=uuid4(),
            destination_terminal_id=uuid4(),
            base_fare=Decimal("25.00")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await RouteService.create_route(db_session, route_data)
        
        assert exc_info.value.status_code == 404
        assert "terminals not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_route_with_terminals(self, db_session: AsyncSession):
        """Test getting a route with terminal information."""
        # Create terminals and route
        origin_data = TerminalCreate(name="Origin", city="City A")
        dest_data = TerminalCreate(name="Destination", city="City B")
        
        origin = await TerminalService.create_terminal(db_session, origin_data)
        destination = await TerminalService.create_terminal(db_session, dest_data)
        
        route_data = RouteCreate(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            base_fare=Decimal("25.00")
        )
        
        created_route = await RouteService.create_route(db_session, route_data)
        
        # Get route with terminals
        retrieved_route = await RouteService.get_route(db_session, created_route.id)
        
        assert retrieved_route is not None
        assert retrieved_route.origin_terminal is not None
        assert retrieved_route.destination_terminal is not None
        assert retrieved_route.origin_terminal.name == "Origin"
        assert retrieved_route.destination_terminal.name == "Destination"


class TestBusService:
    """Test cases for BusService."""

    @pytest.mark.asyncio
    async def test_create_bus(self, db_session: AsyncSession):
        """Test creating a new bus."""
        bus_data = BusCreate(
            license_plate="ABC-123",
            model="Mercedes Sprinter",
            capacity=50,
            amenities={"wifi": True, "ac": True}
        )
        
        bus = await BusService.create_bus(db_session, bus_data)
        
        assert bus.id is not None
        assert bus.license_plate == "ABC-123"
        assert bus.model == "Mercedes Sprinter"
        assert bus.capacity == 50
        assert bus.amenities == {"wifi": True, "ac": True}
        assert bus.is_active is True

    @pytest.mark.asyncio
    async def test_create_bus_duplicate_license_plate(self, db_session: AsyncSession):
        """Test creating a bus with duplicate license plate."""
        bus_data = BusCreate(
            license_plate="DUPLICATE-123",
            capacity=50
        )
        
        # Create first bus
        await BusService.create_bus(db_session, bus_data)
        
        # Try to create second bus with same license plate
        with pytest.raises(HTTPException) as exc_info:
            await BusService.create_bus(db_session, bus_data)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_buses_with_filters(self, db_session: AsyncSession):
        """Test getting buses with filters."""
        # Create test buses
        bus1_data = BusCreate(license_plate="BUS-001", capacity=50)
        bus2_data = BusCreate(license_plate="BUS-002", capacity=40, is_active=False)
        bus3_data = BusCreate(license_plate="COACH-001", capacity=60)
        
        await BusService.create_bus(db_session, bus1_data)
        await BusService.create_bus(db_session, bus2_data)
        await BusService.create_bus(db_session, bus3_data)
        
        # Test license plate filter
        buses, total = await BusService.get_buses(db_session, license_plate="BUS")
        assert total == 2
        assert all("BUS" in b.license_plate for b in buses)
        
        # Test active filter
        buses, total = await BusService.get_buses(db_session, is_active=True)
        assert total == 2
        assert all(b.is_active for b in buses)

    @pytest.mark.asyncio
    async def test_update_bus(self, db_session: AsyncSession):
        """Test updating a bus."""
        # Create a bus
        bus_data = BusCreate(license_plate="UPDATE-123", capacity=50)
        bus = await BusService.create_bus(db_session, bus_data)
        
        # Update the bus
        update_data = BusUpdate(model="Updated Model", capacity=60)
        updated_bus = await BusService.update_bus(db_session, bus.id, update_data)
        
        assert updated_bus is not None
        assert updated_bus.model == "Updated Model"
        assert updated_bus.capacity == 60
        assert updated_bus.license_plate == "UPDATE-123"  # Unchanged


class TestTripService:
    """Test cases for TripService."""

    @pytest.fixture
    async def setup_trip_dependencies(self, db_session: AsyncSession):
        """Set up dependencies for trip tests."""
        # Create terminals
        origin_data = TerminalCreate(name="Origin", city="City A")
        dest_data = TerminalCreate(name="Destination", city="City B")
        
        origin = await TerminalService.create_terminal(db_session, origin_data)
        destination = await TerminalService.create_terminal(db_session, dest_data)
        
        # Create route
        route_data = RouteCreate(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id,
            base_fare=Decimal("25.00")
        )
        route = await RouteService.create_route(db_session, route_data)
        
        # Create bus
        bus_data = BusCreate(license_plate="TRIP-BUS", capacity=50)
        bus = await BusService.create_bus(db_session, bus_data)
        
        # Create driver user
        driver = User(
            email="driver@test.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Driver",
            role=UserRole.DRIVER,
            is_verified=True,
            is_active=True
        )
        db_session.add(driver)
        await db_session.commit()
        await db_session.refresh(driver)
        
        return {
            "route": route,
            "bus": bus,
            "driver": driver
        }

    @pytest.mark.asyncio
    async def test_create_trip(self, db_session: AsyncSession, setup_trip_dependencies):
        """Test creating a new trip."""
        deps = await setup_trip_dependencies
        
        departure_time = datetime.now() + timedelta(hours=2)
        trip_data = TripCreate(
            route_id=deps["route"].id,
            bus_id=deps["bus"].id,
            driver_id=deps["driver"].id,
            departure_time=departure_time,
            fare=Decimal("30.00")
        )
        
        trip = await TripService.create_trip(db_session, trip_data)
        
        assert trip.id is not None
        assert trip.route_id == deps["route"].id
        assert trip.bus_id == deps["bus"].id
        assert trip.driver_id == deps["driver"].id
        assert trip.departure_time == departure_time
        assert trip.fare == Decimal("30.00")
        assert trip.status == TripStatus.SCHEDULED
        assert trip.available_seats == 50  # Should match bus capacity

    @pytest.mark.asyncio
    async def test_create_trip_with_invalid_route(self, db_session: AsyncSession, setup_trip_dependencies):
        """Test creating a trip with invalid route."""
        deps = await setup_trip_dependencies
        
        trip_data = TripCreate(
            route_id=uuid4(),  # Non-existent route
            bus_id=deps["bus"].id,
            driver_id=deps["driver"].id,
            departure_time=datetime.now() + timedelta(hours=2),
            fare=Decimal("30.00")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await TripService.create_trip(db_session, trip_data)
        
        assert exc_info.value.status_code == 404
        assert "Route not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_trip_with_invalid_driver(self, db_session: AsyncSession, setup_trip_dependencies):
        """Test creating a trip with invalid driver."""
        deps = await setup_trip_dependencies
        
        trip_data = TripCreate(
            route_id=deps["route"].id,
            bus_id=deps["bus"].id,
            driver_id=uuid4(),  # Non-existent driver
            departure_time=datetime.now() + timedelta(hours=2),
            fare=Decimal("30.00")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await TripService.create_trip(db_session, trip_data)
        
        assert exc_info.value.status_code == 404
        assert "Driver not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_trip_with_relations(self, db_session: AsyncSession, setup_trip_dependencies):
        """Test getting a trip with related data."""
        deps = await setup_trip_dependencies
        
        trip_data = TripCreate(
            route_id=deps["route"].id,
            bus_id=deps["bus"].id,
            driver_id=deps["driver"].id,
            departure_time=datetime.now() + timedelta(hours=2),
            fare=Decimal("30.00")
        )
        
        created_trip = await TripService.create_trip(db_session, trip_data)
        
        # Get trip with relations
        retrieved_trip = await TripService.get_trip(db_session, created_trip.id)
        
        assert retrieved_trip is not None
        assert retrieved_trip.route is not None
        assert retrieved_trip.bus is not None
        assert retrieved_trip.route.origin_terminal is not None
        assert retrieved_trip.route.destination_terminal is not None

    @pytest.mark.asyncio
    async def test_get_trips_with_filters(self, db_session: AsyncSession, setup_trip_dependencies):
        """Test getting trips with filters."""
        deps = await setup_trip_dependencies
        
        # Create multiple trips
        trip1_data = TripCreate(
            route_id=deps["route"].id,
            bus_id=deps["bus"].id,
            driver_id=deps["driver"].id,
            departure_time=datetime.now() + timedelta(hours=1),
            fare=Decimal("30.00")
        )
        
        trip2_data = TripCreate(
            route_id=deps["route"].id,
            bus_id=deps["bus"].id,
            driver_id=deps["driver"].id,
            departure_time=datetime.now() + timedelta(hours=2),
            fare=Decimal("35.00"),
            status=TripStatus.IN_TRANSIT
        )
        
        await TripService.create_trip(db_session, trip1_data)
        await TripService.create_trip(db_session, trip2_data)
        
        # Test route filter
        trips, total = await TripService.get_trips(db_session, route_id=deps["route"].id)
        assert total == 2
        
        # Test status filter
        trips, total = await TripService.get_trips(db_session, status=TripStatus.SCHEDULED.value)
        assert total == 1
        assert trips[0].status == TripStatus.SCHEDULED

    @pytest.mark.asyncio
    async def test_update_trip(self, db_session: AsyncSession, setup_trip_dependencies):
        """Test updating a trip."""
        deps = await setup_trip_dependencies
        
        # Create a trip
        trip_data = TripCreate(
            route_id=deps["route"].id,
            bus_id=deps["bus"].id,
            driver_id=deps["driver"].id,
            departure_time=datetime.now() + timedelta(hours=2),
            fare=Decimal("30.00")
        )
        
        trip = await TripService.create_trip(db_session, trip_data)
        
        # Update the trip
        new_departure = datetime.now() + timedelta(hours=3)
        update_data = TripUpdate(
            departure_time=new_departure,
            fare=Decimal("35.00"),
            status=TripStatus.BOARDING
        )
        
        updated_trip = await TripService.update_trip(db_session, trip.id, update_data)
        
        assert updated_trip is not None
        assert updated_trip.departure_time == new_departure
        assert updated_trip.fare == Decimal("35.00")
        assert updated_trip.status == TripStatus.BOARDING