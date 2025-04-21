from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from schemas.tickets import TicketCreate, TicketUpdate, TicketResponse, TicketStatus, TicketFilter
from services.tickets import TicketService, Optional, List, Dict
from core.database import get_db1
from core.utils.response import Response

router = APIRouter()

# Create a ticket
@router.post("/tickets/", response_model=TicketResponse)
async def create_ticket(ticket_data: TicketCreate, db: AsyncSession = Depends(get_db1)):
    try:
        ticket = await TicketService.create_ticket(db, ticket_data)
        return Response(data=ticket, message="Ticket created successfully", code=201)
    except Exception as e:
        return Response(success=False, message=str(e), code=400)

# Get a ticket by ID
@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db1)):
    ticket = await TicketService.get_ticket(db, ticket_id)
    if ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=ticket, message="Ticket fetched successfully", code=200)

# Get all tickets with pagination
@router.get("/tickets/", response_model=List[TicketResponse])
async def get_all_tickets(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db1)):
    tickets = await TicketService.get_all_tickets(db, skip=skip, limit=limit)
    return Response(data=tickets, message="Tickets fetched successfully", code=200)

# Update ticket details
@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket_details(ticket_id: UUID, ticket_data: TicketUpdate, db: AsyncSession = Depends(get_db1)):
    updated_ticket = await TicketService.update_ticket(db, ticket_id, ticket_data)
    if updated_ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=updated_ticket, message="Ticket updated successfully", code=200)

# Update the status of a ticket
@router.put("/tickets/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(ticket_id: UUID, status: TicketStatus, db: AsyncSession = Depends(get_db1)):
    updated_ticket = await TicketService.update_ticket_status(db, ticket_id, status)
    if updated_ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=updated_ticket, message="Ticket status updated successfully", code=200)

# Update the bus of a ticket
@router.put("/tickets/{ticket_id}/bus", response_model=TicketResponse)
async def update_ticket_bus(ticket_id: UUID, bus_id: UUID, db: AsyncSession = Depends(get_db1)):
    updated_ticket = await TicketService.update_ticket_bus(db, ticket_id, bus_id)
    if updated_ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=updated_ticket, message="Ticket bus updated successfully", code=200)

# Update the location of a ticket
@router.put("/tickets/{ticket_id}/location", response_model=TicketResponse)
async def update_ticket_location(ticket_id: UUID, location: dict, is_start_location: bool = False, db: AsyncSession = Depends(get_db1)):
    updated_ticket = await TicketService.update_ticket_location(db, ticket_id, location, is_start_location)
    if updated_ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=updated_ticket, message="Ticket location updated successfully", code=200)

# Delete a ticket by ID
@router.delete("/tickets/{ticket_id}", response_model=TicketResponse)
async def delete_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db1)):
    deleted_ticket = await TicketService.delete_ticket(db, ticket_id)
    if deleted_ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=deleted_ticket, message="Ticket deleted successfully", code=200)

# Calculate the total fare for a ticket
@router.get("/tickets/{ticket_id}/fare", response_model=float)
async def calculate_ticket_fare(ticket_id: UUID, db: AsyncSession = Depends(get_db1)):
    ticket = await TicketService.get_ticket(db, ticket_id)
    if ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=await TicketService.calculate_ticket_fare(ticket), message="Fare calculated successfully", code=200)

# Get the duration of a ticket
@router.get("/tickets/{ticket_id}/duration", response_model=float)
async def get_ticket_duration(ticket_id: UUID, db: AsyncSession = Depends(get_db1)):
    ticket = await TicketService.get_ticket(db, ticket_id)
    if ticket is None:
        return Response(success=False, message="Ticket not found", code=404)
    return Response(data=await TicketService.get_ticket_duration(ticket), message="Ticket duration fetched successfully", code=200)

# Filter tickets by dynamic criteria
@router.post("/tickets/filter")
async def filter_tickets_by_criteria(filter: TicketFilter, db: AsyncSession = Depends(get_db1)):
    try:
        tickets = await TicketService.filter_tickets(db, filter)
        return Response(data=tickets, code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)
