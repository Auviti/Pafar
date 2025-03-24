from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from fastapi import HTTPException
from user.models.user import Address  # Assuming Address is already defined
from user.schemas.user import AddressCreate, AddressUpdate


# Get all addresses (asynchronous)
async def get_addresses(db: AsyncSession):
    result = await db.execute(select(Address))
    return result.scalars().all()


# Get a single address by ID (asynchronous)
async def get_address(db: AsyncSession, address_id: UUID):
    result = await db.execute(select(Address).filter(Address.id == address_id))
    return result.scalars().first()


# Create a new address (asynchronous)
async def create_address(db: AsyncSession, address_create: AddressCreate):
    db_address = Address(
        email_address=address_create.email_address, 
        street=address_create.street, 
        city=address_create.city, 
        state=address_create.state,
        country=address_create.country,
        post_code=address_create.post_code,
        kind=address_create.kind
    )
    db.add(db_address)
    await db.commit()  # Use await here for async commit
    await db.refresh(db_address)  # Use await to refresh the instance
    return db_address


# Update an existing address (asynchronous)
async def update_address(db: AsyncSession, address_update: AddressUpdate, address_id: UUID):
    result = await db.execute(select(Address).filter(Address.id == address_id))
    db_address = result.scalars().first()

    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")

    # Update the address's fields with the new values from address_update
    if address_update.email_address:
        db_address.email_address = address_update.email_address
    if address_update.street:
        db_address.street = address_update.street
    if address_update.city:
        db_address.city = address_update.city
    if address_update.state:
        db_address.state = address_update.state
    if address_update.country:
        db_address.country = address_update.country
    if address_update.post_code:
        db_address.post_code = address_update.post_code
    if address_update.kind:
        db_address.kind = address_update.kind

    await db.commit()  # Use await to commit changes asynchronously
    await db.refresh(db_address)  # Use await to refresh the instance
    return db_address


# Delete an address (asynchronous)
async def delete_address(db: AsyncSession, address_id: UUID):
    result = await db.execute(select(Address).filter(Address.id == address_id))
    db_address = result.scalars().first()

    if not db_address:
        raise HTTPException(status_code=404, detail="Address not found")

    await db.delete(db_address)  # Delete the address
    await db.commit()  # Commit the changes asynchronously


# Filter addresses dynamically (asynchronous)
async def filter_addresses(db: AsyncSession, **filters):
    query = select(Address)
    
    for field, value in filters.items():
        if hasattr(Address, field):
            query = query.filter(getattr(Address, field) == value)
    
    result = await db.execute(query)
    return result.scalars().all()
