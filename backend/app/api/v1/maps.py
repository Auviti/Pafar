"""
Maps API endpoints for location and route services.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.maps_service import maps_service_instance
from app.schemas.maps import (
    GeocodeResponse,
    RouteCalculationResponse,
    TerminalSearchResponse,
    AutocompleteResponse,
    ETAResponse,
    PolylineResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/geocode/terminal/{terminal_id}", response_model=GeocodeResponse)
async def geocode_terminal(
    terminal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Geocode a terminal's address and update its coordinates.
    
    Args:
        terminal_id: Terminal ID to geocode
        db: Database session
        
    Returns:
        Geocoding result
        
    Raises:
        HTTPException: If terminal not found or geocoding fails
    """
    try:
        result = await maps_service_instance.geocode_terminal(db, terminal_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Terminal not found or geocoding failed"
            )
        
        return GeocodeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error geocoding terminal {terminal_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during geocoding"
        )


@router.post("/route/{route_id}/calculate", response_model=RouteCalculationResponse)
async def calculate_route_distance(
    route_id: str,
    update_route: bool = Query(True, description="Whether to update route in database"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate distance and duration for a route.
    
    Args:
        route_id: Route ID to calculate
        update_route: Whether to update the route in database
        db: Database session
        
    Returns:
        Route calculation result
        
    Raises:
        HTTPException: If route not found or calculation fails
    """
    try:
        result = await maps_service_instance.calculate_route_distance(
            db, route_id, update_route
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Route not found or calculation failed"
            )
        
        return RouteCalculationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating route {route_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during route calculation"
        )


@router.get("/terminals/search", response_model=List[TerminalSearchResponse])
async def search_terminals(
    query: str = Query(..., description="Search query for terminals"),
    latitude: Optional[float] = Query(None, description="Latitude for location bias"),
    longitude: Optional[float] = Query(None, description="Longitude for location bias"),
    radius: int = Query(50000, description="Search radius in meters", ge=1000, le=100000)
):
    """
    Search for terminals using Google Places API.
    
    Args:
        query: Search query
        latitude: Optional latitude for location bias
        longitude: Optional longitude for location bias
        radius: Search radius in meters
        
    Returns:
        List of terminal search results
    """
    try:
        location = None
        if latitude is not None and longitude is not None:
            location = (latitude, longitude)
        
        results = await maps_service_instance.search_terminals(
            query=query,
            location=location,
            radius=radius
        )
        
        return [TerminalSearchResponse(**result) for result in results]
        
    except Exception as e:
        logger.error(f"Error searching terminals for query '{query}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during terminal search"
        )


@router.get("/terminals/autocomplete", response_model=List[AutocompleteResponse])
async def get_terminal_autocomplete(
    input_text: str = Query(..., description="Input text for autocomplete"),
    latitude: Optional[float] = Query(None, description="Latitude for location bias"),
    longitude: Optional[float] = Query(None, description="Longitude for location bias"),
    radius: int = Query(50000, description="Search radius in meters", ge=1000, le=100000)
):
    """
    Get autocomplete suggestions for terminal search.
    
    Args:
        input_text: Input text for autocomplete
        latitude: Optional latitude for location bias
        longitude: Optional longitude for location bias
        radius: Search radius in meters
        
    Returns:
        List of autocomplete suggestions
    """
    try:
        location = None
        if latitude is not None and longitude is not None:
            location = (latitude, longitude)
        
        results = await maps_service_instance.get_terminal_autocomplete(
            input_text=input_text,
            location=location,
            radius=radius
        )
        
        return [AutocompleteResponse(**result) for result in results]
        
    except Exception as e:
        logger.error(f"Error getting autocomplete for '{input_text}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during autocomplete"
        )


@router.post("/trip/{trip_id}/eta", response_model=ETAResponse)
async def calculate_trip_eta(
    trip_id: str,
    latitude: float = Query(..., description="Current latitude"),
    longitude: float = Query(..., description="Current longitude"),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate ETA for a trip based on current location.
    
    Args:
        trip_id: Trip ID
        latitude: Current latitude
        longitude: Current longitude
        db: Database session
        
    Returns:
        ETA calculation result
        
    Raises:
        HTTPException: If trip not found or ETA calculation fails
    """
    try:
        current_location = (latitude, longitude)
        
        result = await maps_service_instance.calculate_trip_eta(
            db=db,
            trip_id=trip_id,
            current_location=current_location
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Trip not found or ETA calculation failed"
            )
        
        return ETAResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ETA for trip {trip_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during ETA calculation"
        )


@router.get("/route/{route_id}/polyline", response_model=PolylineResponse)
async def get_route_polyline(
    route_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get encoded polyline for a route.
    
    Args:
        route_id: Route ID
        db: Database session
        
    Returns:
        Encoded polyline string
        
    Raises:
        HTTPException: If route not found or polyline generation fails
    """
    try:
        polyline = await maps_service_instance.get_route_polyline(db, route_id)
        
        if not polyline:
            raise HTTPException(
                status_code=404,
                detail="Route not found or polyline generation failed"
            )
        
        return PolylineResponse(route_id=route_id, polyline=polyline)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting polyline for route {route_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during polyline generation"
        )