from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db1
from user.schemas.address import ApiKeyCreate, ApiKeyUpdate, ApiKeyView
from user.services.address import get_apikeys, get_apikey, create_apikey, update_apikey, delete_apikey, filter_apikeys

router = APIRouter()

# Get all apikeys
@router.get("/apikeys", response_model=List[ApiKeyView])
async def get_all_apikeys(db: AsyncSession = Depends(get_db)):
    apikeys = await get_apikeys(db)
    return apikeys

# Get a single address by ID
@router.get("/apikeys/{apikey_id}", response_model=ApiKeyView)
async def get_apikey_by_id(address_id: UUID, db: AsyncSession = Depends(get_db)):
    apikey = await get_apikey(db, address_id)
    if apikey is None:
        raise HTTPException(status_code=404, detail="ApiKey not found")
    return apikey

# Create a new address
@router.post("/apikeys", response_model=ApiKeyView, status_code=201)
async def create_new_apikey(apikey: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    return await create_apikey(db, apikey)

# Update an existing address
@router.put("/apikeys/{apikey_id}", response_model=ApiKeyView)
async def update_apikey_by_id(apikey_id: UUID, apikey_update: ApiKeyUpdate, db: AsyncSession = Depends(get_db)):
    updated_apikey = await update_apikey(db, apikey_update, apikey_id)
    if updated_apikey is None:
        raise HTTPException(status_code=404, detail="ApiKey not found")
    return updated_apikey

# Delete an address
@router.delete("/apikeys/{apikey_id}", status_code=204)
async def delete_apikey_by_id(apikey_id: UUID, db: AsyncSession = Depends(get_db)):
    await delete_apikey(db, apikey_id)
    return {"message": "ApiKey successfully deleted"}

# Filter addresses by dynamic criteria
@router.get("/apikeys/filter", response_model=List[ApiKeyView])
async def filter_apikeys_by_criteria(filters: dict, db: AsyncSession = Depends(get_db)):
    apikeys = await filter_apikeys(db, **filters)
    return apikeys
