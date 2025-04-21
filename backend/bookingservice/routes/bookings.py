from fastapi import APIRouter, Depends

from schemas.bookings import BookingCreate, BookingResponse, BookingUpdate
from services.bookings import BookingService,AsyncSession

from core.database import get_db1
from core.utils.response import Response
from uuid import UUID
from models.bookings import List  # assuming your status enum is here

router = APIRouter()


@router.post("/bookings/", response_model=BookingResponse)
async def create_booking_route(booking: BookingCreate, db: AsyncSession = Depends(get_db1)):
    try:
        # Call the service to create the booking
        result = await BookingService.create_booking(db=db, booking_data=booking)
        return Response(data=result, message="Booking created successfully", code=201)
    except Exception as e:
        # If something goes wrong, return an error response
        return Response(message="Failed to create booking", error=str(e), code=500)


@router.get("/bookings/", response_model=List[BookingResponse])
async def get_all_bookings_route(db: AsyncSession = Depends(get_db1)):
    try:
        # Call the service to get all bookings with pagination
        bookings = await BookingService.get_all_bookings(db)
        return Response(data=bookings, message="Bookings fetched successfully", code=200)
    except Exception as e:
        # Handle any errors while fetching bookings
        return Response(message="Failed to fetch bookings", error=str(e), code=500)


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id_route(booking_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        # Call the service to fetch a booking by its ID
        result = await BookingService.get_booking(db=db, booking_id=booking_id)
        if not result:
            # Return 404 if the booking is not found
            return Response(message="Booking not found", code=404)
        return Response(data=result, message="Booking fetched successfully", code=200)
    except Exception as e:
        # Handle errors while fetching the booking
        return Response(message="Failed to fetch booking", error=str(e), code=500)


@router.put("/bookings/{booking_id}/protect", response_model=BookingResponse)
async def protect_booking_route(booking_id: UUID, isprotected: bool, db: AsyncSession = Depends(get_db1)):
    try:
        # Create a BookingUpdate instance to modify the protection status
        booking_data = BookingUpdate(isprotected=isprotected)
        # Call the service to update the booking protection status
        result = await BookingService.update_booking(db=db, booking_id=booking_id, booking_data=booking_data)
        return Response(data=result, message="Booking protection status updated successfully", code=200)
    except Exception as e:
        # Handle exceptions during the update process
        return Response(message="Failed to update protection status", error=str(e), code=500)


@router.delete("/bookings/{booking_id}", response_model=Response)
async def delete_booking_by_id(booking_id: UUID, db: AsyncSession = Depends(get_db1)):
    try:
        # Call the service to delete the booking by its ID
        result = await BookingService.delete_booking(db=db, booking_id=booking_id)
        if not result:
            # Return 404 if the booking is not found
            return Response(message="Booking not found", error="Booking with the provided ID doesn't exist", code=404)
        return Response(message="Booking deleted successfully", code=200)
    except Exception as e:
        # Handle errors during the deletion process
        return Response(message="Failed to delete booking", error=str(e), code=500)
