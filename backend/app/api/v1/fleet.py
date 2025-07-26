"""
Fleet management API endpoints.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.schemas.fleet import (
    Terminal, TerminalCreate, TerminalUpdate, TerminalList,
    Route, RouteCreate, RouteUpdate, RouteList,
    Bus, BusCreate, BusUpdate, BusList,
    Trip, TripCreate, TripUpdate, TripList
)
from app.services.fleet_service import (
    TerminalService, RouteService, BusService, TripService
)

router = APIRouter()


# Terminal endpoints
@router.post("/terminals", response_model=Terminal, status_code=status.HTTP_201_CREATED)
async def create_terminal(
    terminal_data: TerminalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new terminal. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create terminals"
        )
    
    return await TerminalService.create_terminal(db, terminal_data)


@router.get("/terminals", response_model=TerminalList)
async def get_terminals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    city: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get terminals with optional filtering."""
    terminals, total = await TerminalService.get_terminals(
        db, skip=skip, limit=limit, city=city, is_active=is_active
    )
    
    return TerminalList(
        terminals=terminals,
        total=total,
        page=skip // limit + 1,
        size=len(terminals)
    )


@router.get("/terminals/{terminal_id}", response_model=Terminal)
async def get_terminal(
    terminal_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a terminal by ID."""
    terminal = await TerminalService.get_terminal(db, terminal_id)
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )
    return terminal


@router.put("/terminals/{terminal_id}", response_model=Terminal)
async def update_terminal(
    terminal_id: UUID,
    terminal_data: TerminalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a terminal. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update terminals"
        )
    
    terminal = await TerminalService.update_terminal(db, terminal_id, terminal_data)
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )
    return terminal


@router.delete("/terminals/{terminal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_terminal(
    terminal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a terminal. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete terminals"
        )
    
    success = await TerminalService.delete_terminal(db, terminal_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terminal not found"
        )


# Route endpoints
@router.post("/routes", response_model=Route, status_code=status.HTTP_201_CREATED)
async def create_route(
    route_data: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new route. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create routes"
        )
    
    return await RouteService.create_route(db, route_data)


@router.get("/routes", response_model=RouteList)
async def get_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    origin_terminal_id: Optional[UUID] = Query(None),
    destination_terminal_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get routes with optional filtering."""
    routes, total = await RouteService.get_routes(
        db, 
        skip=skip, 
        limit=limit, 
        origin_terminal_id=origin_terminal_id,
        destination_terminal_id=destination_terminal_id,
        is_active=is_active
    )
    
    return RouteList(
        routes=routes,
        total=total,
        page=skip // limit + 1,
        size=len(routes)
    )


@router.get("/routes/{route_id}", response_model=Route)
async def get_route(
    route_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a route by ID."""
    route = await RouteService.get_route(db, route_id)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return route


@router.put("/routes/{route_id}", response_model=Route)
async def update_route(
    route_id: UUID,
    route_data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a route. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update routes"
        )
    
    route = await RouteService.update_route(db, route_id, route_data)
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return route


@router.delete("/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a route. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete routes"
        )
    
    success = await RouteService.delete_route(db, route_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )


# Bus endpoints
@router.post("/buses", response_model=Bus, status_code=status.HTTP_201_CREATED)
async def create_bus(
    bus_data: BusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new bus. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create buses"
        )
    
    return await BusService.create_bus(db, bus_data)


@router.get("/buses", response_model=BusList)
async def get_buses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    license_plate: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get buses with optional filtering."""
    buses, total = await BusService.get_buses(
        db, skip=skip, limit=limit, license_plate=license_plate, is_active=is_active
    )
    
    return BusList(
        buses=buses,
        total=total,
        page=skip // limit + 1,
        size=len(buses)
    )


@router.get("/buses/{bus_id}", response_model=Bus)
async def get_bus(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a bus by ID."""
    bus = await BusService.get_bus(db, bus_id)
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )
    return bus


@router.put("/buses/{bus_id}", response_model=Bus)
async def update_bus(
    bus_id: UUID,
    bus_data: BusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a bus. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update buses"
        )
    
    bus = await BusService.update_bus(db, bus_id, bus_data)
    if not bus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )
    return bus


@router.delete("/buses/{bus_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bus(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a bus. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete buses"
        )
    
    success = await BusService.delete_bus(db, bus_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found"
        )


# Trip endpoints
@router.post("/trips", response_model=Trip, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new trip. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create trips"
        )
    
    return await TripService.create_trip(db, trip_data)


@router.get("/trips", response_model=TripList)
async def get_trips(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    route_id: Optional[UUID] = Query(None),
    bus_id: Optional[UUID] = Query(None),
    driver_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get trips with optional filtering."""
    trips, total = await TripService.get_trips(
        db, 
        skip=skip, 
        limit=limit, 
        route_id=route_id,
        bus_id=bus_id,
        driver_id=driver_id,
        status=status
    )
    
    return TripList(
        trips=trips,
        total=total,
        page=skip // limit + 1,
        size=len(trips)
    )


@router.get("/trips/{trip_id}", response_model=Trip)
async def get_trip(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a trip by ID."""
    trip = await TripService.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    return trip


@router.put("/trips/{trip_id}", response_model=Trip)
async def update_trip(
    trip_id: UUID,
    trip_data: TripUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a trip. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update trips"
        )
    
    trip = await TripService.update_trip(db, trip_id, trip_data)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    return trip


@router.delete("/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a trip. Requires admin role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete trips"
        )
    
    success = await TripService.delete_trip(db, trip_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )