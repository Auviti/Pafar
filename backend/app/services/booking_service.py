"""
Booking service for trip reservations and seat management.
"""
import secrets
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import and_, or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.fleet import Trip, Bus, Route, Terminal, TripStatus
from app.models.user import User
from app.schemas.booking import (
    BookingCreate, BookingUpdate, TripSearchRequest, 
    SeatReservationRequest, BookingCancellationRequest,
    SeatAvailabilityResponse, TripDetails, BookingResponse
)
from app.core.redis import get_redis


class BookingNotAvailableException(Exception):
    """Exception raised when booking is not available."""
    pass


class SeatNotAvailableException(Exception):
    """Exception raised when seats are not available."""
    pass


class BookingNotFoundException(Exception):
    """Exception raised when booking is not found."""
    pass


class BookingService:
    """Service for managing trip bookings and seat reservations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = get_redis()
    
    async def search_trips(
        self, 
        search_request: TripSearchRequest,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search for available trips with filtering."""
        query = select(Trip).options(
            selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Trip.bus)
        )
        
        # Apply filters
        conditions = [Trip.status.in_([TripStatus.SCHEDULED, TripStatus.BOARDING])]
        
        if search_request.origin_terminal_id:
            query = query.join(Route).filter(
                Route.origin_terminal_id == search_request.origin_terminal_id
            )
        
        if search_request.destination_terminal_id:
            query = query.join(Route).filter(
                Route.destination_terminal_id == search_request.destination_terminal_id
            )
        
        if search_request.departure_date:
            start_date = search_request.departure_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            conditions.append(
                and_(
                    Trip.departure_time >= start_date,
                    Trip.departure_time < end_date
                )
            )
        
        if search_request.max_fare:
            conditions.append(Trip.fare <= search_request.max_fare)
        
        if search_request.min_seats:
            conditions.append(Trip.available_seats >= search_request.min_seats)
        
        query = query.filter(and_(*conditions))
        
        # Add pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Get total count
        count_query = select(func.count(Trip.id)).filter(and_(*conditions))
        if search_request.origin_terminal_id or search_request.destination_terminal_id:
            count_query = count_query.join(Route)
        
        result = await self.db.execute(query)
        trips = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return {
            "trips": [TripDetails.model_validate(trip) for trip in trips],
            "total": total,
            "page": page,
            "size": size
        }
    
    async def get_seat_availability(self, trip_id: UUID) -> SeatAvailabilityResponse:
        """Get seat availability for a specific trip."""
        # Get trip with bus capacity
        query = select(Trip).options(selectinload(Trip.bus)).filter(Trip.id == trip_id)
        result = await self.db.execute(query)
        trip = result.scalar_one_or_none()
        
        if not trip:
            raise BookingNotFoundException(f"Trip {trip_id} not found")
        
        total_seats = trip.bus.capacity
        
        # Get occupied seats from confirmed bookings
        booking_query = select(Booking.seat_numbers).filter(
            and_(
                Booking.trip_id == trip_id,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            )
        )
        booking_result = await self.db.execute(booking_query)
        bookings = booking_result.scalars().all()
        
        occupied_seats = []
        for booking_seats in bookings:
            if booking_seats:
                occupied_seats.extend(booking_seats)
        
        # Get temporarily reserved seats from Redis
        redis_key = f"temp_reservations:{trip_id}"
        temp_reservations = await self.redis.hgetall(redis_key)
        temporarily_reserved_seats = []
        
        for seat_data in temp_reservations.values():
            import json
            seat_info = json.loads(seat_data)
            temporarily_reserved_seats.extend(seat_info.get('seats', []))
        
        # Calculate available seats
        all_seats = list(range(1, total_seats + 1))
        unavailable_seats = set(occupied_seats + temporarily_reserved_seats)
        available_seats = [seat for seat in all_seats if seat not in unavailable_seats]
        
        return SeatAvailabilityResponse(
            trip_id=trip_id,
            total_seats=total_seats,
            available_seats=available_seats,
            occupied_seats=sorted(list(set(occupied_seats))),
            temporarily_reserved_seats=sorted(list(set(temporarily_reserved_seats)))
        )
    
    async def reserve_seats_temporarily(
        self, 
        user_id: UUID, 
        reservation_request: SeatReservationRequest
    ) -> Dict[str, Any]:
        """Reserve seats temporarily for 10 minutes."""
        trip_id = reservation_request.trip_id
        seat_numbers = reservation_request.seat_numbers
        
        # Check seat availability
        availability = await self.get_seat_availability(trip_id)
        
        # Check if requested seats are available
        unavailable_seats = set(seat_numbers) - set(availability.available_seats)
        if unavailable_seats:
            raise SeatNotAvailableException(
                f"Seats {list(unavailable_seats)} are not available"
            )
        
        # Create temporary reservation in Redis
        redis_key = f"temp_reservations:{trip_id}"
        reservation_id = f"{user_id}:{int(datetime.utcnow().timestamp())}"
        
        reservation_data = {
            "user_id": str(user_id),
            "seats": seat_numbers,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
        import json
        await self.redis.hset(
            redis_key, 
            reservation_id, 
            json.dumps(reservation_data)
        )
        
        # Set expiration for the reservation
        await self.redis.expire(redis_key, 600)  # 10 minutes
        
        return {
            "reservation_id": reservation_id,
            "trip_id": trip_id,
            "seats": seat_numbers,
            "expires_at": reservation_data["expires_at"]
        }
    
    def _generate_booking_reference(self) -> str:
        """Generate unique booking reference."""
        # Generate 8-character alphanumeric reference
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(8))
    
    async def create_booking(
        self, 
        user_id: UUID, 
        booking_data: BookingCreate
    ) -> BookingResponse:
        """Create a new booking with seat confirmation."""
        trip_id = booking_data.trip_id
        seat_numbers = booking_data.seat_numbers
        
        # Verify trip exists and is bookable
        query = select(Trip).options(
            selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Trip.bus)
        ).filter(Trip.id == trip_id)
        
        result = await self.db.execute(query)
        trip = result.scalar_one_or_none()
        
        if not trip:
            raise BookingNotFoundException(f"Trip {trip_id} not found")
        
        if trip.status not in [TripStatus.SCHEDULED, TripStatus.BOARDING]:
            raise BookingNotAvailableException(f"Trip {trip_id} is not available for booking")
        
        # Check seat availability one more time
        availability = await self.get_seat_availability(trip_id)
        unavailable_seats = set(seat_numbers) - set(availability.available_seats)
        if unavailable_seats:
            raise SeatNotAvailableException(
                f"Seats {list(unavailable_seats)} are not available"
            )
        
        # Calculate total amount
        total_amount = trip.fare * len(seat_numbers)
        
        # Generate unique booking reference
        booking_reference = self._generate_booking_reference()
        
        # Ensure reference is unique
        while True:
            existing = await self.db.execute(
                select(Booking).filter(Booking.booking_reference == booking_reference)
            )
            if not existing.scalar_one_or_none():
                break
            booking_reference = self._generate_booking_reference()
        
        # Create booking
        booking = Booking(
            user_id=user_id,
            trip_id=trip_id,
            seat_numbers=seat_numbers,
            total_amount=total_amount,
            booking_reference=booking_reference,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING
        )
        
        self.db.add(booking)
        await self.db.commit()
        await self.db.refresh(booking)
        
        # Update trip available seats
        trip.available_seats = len(availability.available_seats) - len(seat_numbers)
        await self.db.commit()
        
        # Remove temporary reservation if exists
        redis_key = f"temp_reservations:{trip_id}"
        temp_reservations = await self.redis.hgetall(redis_key)
        
        for reservation_id, reservation_data in temp_reservations.items():
            import json
            reservation_info = json.loads(reservation_data)
            if str(user_id) == reservation_info.get('user_id'):
                await self.redis.hdel(redis_key, reservation_id)
                break
        
        # Load booking with relationships for response
        query = select(Booking).options(
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Booking.trip).selectinload(Trip.bus)
        ).filter(Booking.id == booking.id)
        
        result = await self.db.execute(query)
        booking_with_relations = result.scalar_one()
        
        return BookingResponse.model_validate(booking_with_relations)
    
    async def get_booking(self, booking_id: UUID, user_id: Optional[UUID] = None) -> BookingResponse:
        """Get booking by ID."""
        query = select(Booking).options(
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Booking.trip).selectinload(Trip.bus)
        ).filter(Booking.id == booking_id)
        
        if user_id:
            query = query.filter(Booking.user_id == user_id)
        
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise BookingNotFoundException(f"Booking {booking_id} not found")
        
        return BookingResponse.model_validate(booking)
    
    async def get_user_bookings(
        self, 
        user_id: UUID, 
        page: int = 1, 
        size: int = 20
    ) -> Dict[str, Any]:
        """Get user's bookings with pagination."""
        query = select(Booking).options(
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Booking.trip).selectinload(Trip.bus)
        ).filter(Booking.user_id == user_id).order_by(Booking.created_at.desc())
        
        # Add pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Get total count
        count_query = select(func.count(Booking.id)).filter(Booking.user_id == user_id)
        
        result = await self.db.execute(query)
        bookings = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return {
            "bookings": [BookingResponse.model_validate(booking) for booking in bookings],
            "total": total,
            "page": page,
            "size": size
        }
    
    async def cancel_booking(
        self, 
        booking_id: UUID, 
        user_id: UUID,
        cancellation_request: BookingCancellationRequest
    ) -> BookingResponse:
        """Cancel a booking with policy enforcement."""
        # Get booking
        query = select(Booking).options(
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Booking.trip).selectinload(Trip.bus)
        ).filter(
            and_(
                Booking.id == booking_id,
                Booking.user_id == user_id
            )
        )
        
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise BookingNotFoundException(f"Booking {booking_id} not found")
        
        if booking.status == BookingStatus.CANCELLED:
            raise BookingNotAvailableException("Booking is already cancelled")
        
        if booking.status == BookingStatus.COMPLETED:
            raise BookingNotAvailableException("Cannot cancel completed booking")
        
        # Check cancellation policy (e.g., can't cancel within 2 hours of departure)
        time_until_departure = booking.trip.departure_time - datetime.utcnow()
        if time_until_departure < timedelta(hours=2):
            raise BookingNotAvailableException(
                "Cannot cancel booking within 2 hours of departure"
            )
        
        # Update booking status
        booking.status = BookingStatus.CANCELLED
        booking.updated_at = datetime.utcnow()
        
        # Update trip available seats
        trip = booking.trip
        trip.available_seats = (trip.available_seats or 0) + len(booking.seat_numbers)
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return BookingResponse.model_validate(booking)
    
    async def update_booking_status(
        self, 
        booking_id: UUID, 
        update_data: BookingUpdate
    ) -> BookingResponse:
        """Update booking status (admin function)."""
        query = select(Booking).options(
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.origin_terminal),
            selectinload(Booking.trip).selectinload(Trip.route).selectinload(Route.destination_terminal),
            selectinload(Booking.trip).selectinload(Trip.bus)
        ).filter(Booking.id == booking_id)
        
        result = await self.db.execute(query)
        booking = result.scalar_one_or_none()
        
        if not booking:
            raise BookingNotFoundException(f"Booking {booking_id} not found")
        
        # Update fields
        if update_data.status is not None:
            booking.status = update_data.status
        
        if update_data.payment_status is not None:
            booking.payment_status = update_data.payment_status
        
        booking.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(booking)
        
        return BookingResponse.model_validate(booking)
    
    async def cleanup_expired_reservations(self) -> int:
        """Clean up expired temporary reservations."""
        # This would typically be called by a background task
        current_time = datetime.utcnow()
        cleaned_count = 0
        
        # Get all temporary reservation keys
        pattern = "temp_reservations:*"
        keys = await self.redis.keys(pattern)
        
        for key in keys:
            reservations = await self.redis.hgetall(key)
            expired_reservations = []
            
            for reservation_id, reservation_data in reservations.items():
                import json
                reservation_info = json.loads(reservation_data)
                expires_at = datetime.fromisoformat(reservation_info['expires_at'])
                
                if current_time > expires_at:
                    expired_reservations.append(reservation_id)
            
            # Remove expired reservations
            if expired_reservations:
                await self.redis.hdel(key, *expired_reservations)
                cleaned_count += len(expired_reservations)
        
        return cleaned_count