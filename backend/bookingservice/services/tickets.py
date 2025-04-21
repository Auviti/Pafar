from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
import asyncpg
from datetime import datetime
import asyncio
from typing import Optional, List, Dict
from uuid import UUID

from models.tickets import Ticket, mappeditem
from schemas.tickets import (
    TicketStatus,
    TicketCreate,
    TicketUpdate,
    TicketFilter,
)

class TicketService:

    @staticmethod
    async def create_ticket(db: AsyncSession, ticket_data: TicketCreate):
        """Creates a new ticket in the database."""
        try:
            ticket = Ticket(
                name=ticket_data.name,
                status=ticket_data.status,
                ticket_class=ticket_data.ticket_class,
                ticket_type=ticket_data.ticket_type,
                vehicle_id=ticket_data.vehicle_id,
                trip_fare=ticket_data.trip_fare,
                passengers=ticket_data.passengers,
                startlocation=ticket_data.startlocation,
                currentlocation=ticket_data.currentlocation,
                endlocation=ticket_data.endlocation,
                starts_at=datetime.fromisoformat(ticket_data.starts_at.replace("Z", "+00:00")),
                ends_at=datetime.fromisoformat(ticket_data.ends_at.replace("Z", "+00:00")),
                suitcase=ticket_data.suitcase,
                handluggage=ticket_data.handluggage,
                otherluggage=ticket_data.otherluggage,
            )
            db.add(ticket)
            await db.commit()
            await db.refresh(ticket)
            return ticket.to_dict()
        except Exception as e:
            await db.rollback()
            raise Exception(f"Error creating ticket: {str(e)}")

    @staticmethod
    async def get_ticket(db: AsyncSession, ticket_id: UUID):
        ticketid = str(ticket_id) if mappeditem is str else ticket_id
        try:
            result = await db.execute(select(Ticket).filter(Ticket.id == ticketid))
            res = result.scalars().first()
            if res:
                return res.to_dict()
            return res
        except SQLAlchemyError as e:
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def get_all_tickets(db: AsyncSession, skip: int = 0, limit: int = 100):
        try:
            result = await db.execute(select(Ticket).offset(skip).limit(limit))
            return [ticket.to_dict() for ticket in result.scalars().all()]
        except SQLAlchemyError as e:
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def filter_tickets(db: AsyncSession, filter: Optional[TicketFilter], skip: int = 0, limit: int = 10):
        try:
            query = select(Ticket)

            if filter:
                if filter.name:
                    query = query.filter(Ticket.name.ilike(f"%{filter.name}%"))
                if filter.status:
                    query = query.filter(Ticket.status == filter.status)
                if filter.ticket_class:
                    query = query.filter(Ticket.ticket_class == filter.ticket_class)
                if filter.ticket_type:
                    query = query.filter(Ticket.ticket_type == filter.ticket_type)
                if filter.vehicle_id:
                    query = query.filter(Ticket.vehicle_id == filter.vehicle_id)
                if filter.startlocation:
                    query = query.filter(Ticket.startlocation.ilike(f"%{filter.startlocation}%"))
                if filter.currentlocation:
                    query = query.filter(Ticket.currentlocation.ilike(f"%{filter.currentlocation}%"))
                if filter.endlocation:
                    query = query.filter(Ticket.endlocation.ilike(f"%{filter.endlocation}%"))
                if filter.starts_at:
                    query = query.filter(Ticket.starts_at >= datetime.fromisoformat(filter.starts_at))
                if filter.ends_at:
                    query = query.filter(Ticket.ends_at <= datetime.fromisoformat(filter.ends_at))
                if filter.suitcase is not None:
                    query = query.filter(Ticket.suitcase == filter.suitcase)
                if filter.handluggage is not None:
                    query = query.filter(Ticket.handluggage == filter.handluggage)
                if filter.otherluggage is not None:
                    query = query.filter(Ticket.otherluggage == filter.otherluggage)
                if filter.passengers is not None:
                    query = query.filter(Ticket.passengers == filter.passengers)

            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            tickets = result.scalars().all()
            return [ticket.to_dict() for ticket in tickets]

        except (SQLAlchemyError, asyncpg.exceptions.UniqueViolationError,
                asyncpg.exceptions.DataError, asyncpg.exceptions.InvalidTextRepresentationError) as e:
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def update_ticket_status(db: AsyncSession, ticket_id: UUID, status: TicketStatus):
        try:
            result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
            ticket = result.scalars().first()
            if ticket:
                ticket.status = status
                ticket.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(ticket)
                return ticket
            return None
        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def update_ticket(db: AsyncSession, ticket_id: UUID, ticket_data: TicketUpdate):
        try:
            result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
            ticket = result.scalars().first()
            if ticket:
                ticket.name = ticket_data.name
                ticket.status = ticket_data.status
                ticket.ticket_class = ticket_data.ticket_class
                ticket.ticket_type = ticket_data.ticket_type
                ticket.vehicle_id = ticket_data.vehicle_id
                ticket.trip_fare = ticket_data.trip_fare
                ticket.passengers = ticket_data.passengers
                ticket.startlocation = ticket_data.startlocation
                ticket.currentlocation = ticket_data.currentlocation
                ticket.endlocation = ticket_data.endlocation
                ticket.suitcase = ticket_data.suitcase
                ticket.handluggage = ticket_data.handluggage
                ticket.otherluggage = ticket_data.otherluggage
                ticket.starts_at = datetime.fromisoformat(ticket_data.starts_at)
                ticket.ends_at = datetime.fromisoformat(ticket_data.ends_at)

                await db.commit()
                await db.refresh(ticket)
                return ticket
            return None
        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def update_ticket_vehicle(db: AsyncSession, ticket_id: UUID, vehicle_id: UUID):
        try:
            result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
            ticket = result.scalars().first()
            if ticket:
                ticket.vehicle_id = vehicle_id
                await db.commit()
                await db.refresh(ticket)
                return ticket
            return None
        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def update_ticket_location(db: AsyncSession, ticket_id: UUID, location: str, is_start_location: bool = False):
        try:
            result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
            ticket = result.scalars().first()
            if ticket:
                if is_start_location:
                    ticket.startlocation = location
                else:
                    ticket.endlocation = location
                ticket.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(ticket)
                return ticket
            return None
        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def delete_ticket(db: AsyncSession, ticket_id: UUID):
        try:
            result = await db.execute(select(Ticket).filter(Ticket.id == ticket_id))
            ticket = result.scalars().first()
            if ticket:
                await db.delete(ticket)
                await db.commit()
                return ticket
            return None
        except SQLAlchemyError as e:
            await db.rollback()
            error_message = str(e)
            result = error_message[error_message.index('<class')+6:error_message.index('[SQL')]
            raise Exception(result)

    @staticmethod
    async def calculate_ticket_fare(ticket: Ticket):
        return await asyncio.to_thread(TicketService._calculate_fare, ticket)

    @staticmethod
    def _calculate_fare(ticket: Ticket):
        luggage_fare = 0.02 * (ticket.suitcase + ticket.handluggage + ticket.otherluggage)
        return ticket.trip_fare + luggage_fare

    @staticmethod
    async def get_ticket_duration(ticket: Ticket):
        return await asyncio.to_thread(TicketService._get_duration, ticket)

    @staticmethod
    def _get_duration(ticket: Ticket):
        if ticket.starts_at and ticket.ends_at:
            return (ticket.ends_at - ticket.starts_at).total_seconds()
        return None
