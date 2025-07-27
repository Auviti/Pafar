"""
Booking API endpoints for trip reservations and seat management.
"""
from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.booking_service import (
    BookingService, 
    BookingNotAvailableException,
    SeatNotAvailableException,
    BookingNotFoundException
)
from app.schemas.booking import (
    BookingCreate, BookingUpdate, TripSearchRequest,
    SeatReservationRequest, BookingCancellationRequest,
    BookingResponse, SeatAvailabilityResponse, BookingListResponse
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/search-trips")
async def search_trips(
    search_request: TripSearchRequest,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Search for available trips with filtering capabilities."""
    booking_service = BookingService(db)
    
    try:
        result = await booking_service.search_trips(search_request, page, size)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching trips: {str(e)}"
        )


@router.get("/trips/{trip_id}/seats")
async def get_seat_availability(
    trip_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> SeatAvailabilityResponse:
    """Get seat availability for a specific trip."""
    booking_service = BookingService(db)
    
    try:
        return await booking_service.get_seat_availability(trip_id)
    except BookingNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting seat availability: {str(e)}"
        )


@router.post("/reserve-seats")
async def reserve_seats_temporarily(
    reservation_request: SeatReservationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Reserve seats temporarily for 10 minutes."""
    booking_service = BookingService(db)
    
    try:
        result = await booking_service.reserve_seats_temporarily(
            current_user.id, 
            reservation_request
        )
        return result
    except SeatNotAvailableException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BookingNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reserving seats: {str(e)}"
        )


@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """Create a new booking with seat confirmation."""
    booking_service = BookingService(db)
    
    try:
        return await booking_service.create_booking(current_user.id, booking_data)
    except BookingNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (BookingNotAvailableException, SeatNotAvailableException) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating booking: {str(e)}"
        )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """Get booking by ID."""
    booking_service = BookingService(db)
    
    try:
        return await booking_service.get_booking(booking_id, current_user.id)
    except BookingNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting booking: {str(e)}"
        )


@router.get("/", response_model=Dict[str, Any])
async def get_user_bookings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user's bookings with pagination."""
    booking_service = BookingService(db)
    
    try:
        return await booking_service.get_user_bookings(current_user.id, page, size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user bookings: {str(e)}"
        )


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    cancellation_request: BookingCancellationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """Cancel a booking with policy enforcement."""
    booking_service = BookingService(db)
    
    try:
        return await booking_service.cancel_booking(
            booking_id, 
            current_user.id, 
            cancellation_request
        )
    except BookingNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BookingNotAvailableException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling booking: {str(e)}"
        )


# Admin endpoints
@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: UUID,
    update_data: BookingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> BookingResponse:
    """Update booking status (admin only)."""
    # Check if user is admin
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update booking status"
        )
    
    booking_service = BookingService(db)
    
    try:
        return await booking_service.update_booking_status(booking_id, update_data)
    except BookingNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating booking status: {str(e)}"
        )