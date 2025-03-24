from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db1
from user.schemas.address import AddressCreate, AddressUpdate, AddressView

from user.services.address import get_addresses, get_address, create_address, update_address, delete_address, filter_addresses

router = APIRouter()

# Get all addresses
@router.get("/addresses", response_model=List[AddressView])
async def get_all_addresses(db: AsyncSession = Depends(get_db)):
    addresses = await get_addresses(db)
    return addresses

# Get a single address by ID
@router.get("/addresses/{address_id}", response_model=AddressView)
async def get_address_by_id(address_id: UUID, db: AsyncSession = Depends(get_db)):
    address = await get_address(db, address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address

# Create a new address
@router.post("/addresses", response_model=AddressView, status_code=201)
async def create_new_address(address: AddressCreate, db: AsyncSession = Depends(get_db)):
    return await create_address(db, address)

# Update an existing address
@router.put("/addresses/{address_id}", response_model=AddressView)
async def update_address_by_id(address_id: UUID, address_update: AddressUpdate, db: AsyncSession = Depends(get_db)):
    updated_address = await update_address(db, address_update, address_id)
    if updated_address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return updated_address

# Delete an address
@router.delete("/addresses/{address_id}", status_code=204)
async def delete_address_by_id(address_id: UUID, db: AsyncSession = Depends(get_db)):
    await delete_address(db, address_id)
    return {"message": "Address successfully deleted"}

# Filter addresses by dynamic criteria
@router.get("/addresses/filter", response_model=List[AddressView])
async def filter_addresses_by_criteria(filters: dict, db: AsyncSession = Depends(get_db)):
    addresses = await filter_addresses(db, **filters)
    return addresses
