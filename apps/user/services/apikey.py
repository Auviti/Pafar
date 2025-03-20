from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, selectinload
from apps.user.models.user import ApiKey, UUID
from apps.user.schemas.apikey import ApiKeyCreate, ApiKeyUpdate, ApiKeyView
from uuid import UUID
from fastapi import HTTPException
from core.utils.auth.apikey import APIKeyGenerator
from core.utils.reponse import Response
from core.utils.encryption import PasswordManager
import sys, json

# Define a custom exception for user not found
class ApiKeyNotFoundException(Exception):
    def __init__(self, message="ApiKey not found", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    # Use string representation for other databases
    UUIDType = str
    mappeditem = str
    default = lambda: str(uuid4())
    
# Get all users (asynchronous)
async def get_apikeys(db: AsyncSession):
    try:
        result = await db.execute(select(ApiKey))
        # Get all users as a list of dictionaries
        apikeys = []
        
        # Remove sensitive keys from each user's dictionary
        for apikey in result.scalars().all():
            apikey_ = apikey.to_dict()
            apikeys.append(apikey_)
        return Response(data=apikeys,code=200)
    except Exception as error:
        return Response(message=str(error),success=False,code=500)

# Get a single user by ID (asynchronous)
async def get_apikey(db: AsyncSession, apikey_id: UUID):
    uid = str(apikey_id) if UUIDType is str else apikey_id
    
    try:
        result = await db.execute(select(ApiKey).filter(ApiKey.id == uid))
        apikey = result.scalars().first()
        if not apikey:
            return Response(message="ApiKey not found",success=False,code=404)
        return Response(data=apikey.to_dict(),code=200)
    except Exception as error:
        return Response(message=str(error), success=False, code=500)
    

# Create a new user (asynchronous)
async def create_apikey(db: AsyncSession, apikey: ApiKeyCreate):
    expires_in = timedelta(hours=1)

    apikeygen = APIKeyGenerator.generate_api_key(apikey.user_id, apikey.role, expires_in)
    
    # Set the expiration time
    expires_at = datetime.utcnow() + expiration

    # Create the API key record

    db_apikey = ApiKey(
        api_key=apikeygen,
        user_id=apikey.user_id,
        role=apikey.role,
        expires_at=apikey.expires_at
    )
    db.add(db_apikey)
    await db.commit()  # Use await here for async commit
    await db.refresh(db_apikey)  # Use await to refresh the instance
    return db_apikey

# Update an existing apikey (asynchronous)
async def update_apikey(db: AsyncSession, apikey_update: ApiKeyUpdate, apikey_id: UUID):
    uid = str(apikey_id) if UUIDType is str else apikey_id
    result = await db.execute(select(ApiKey).filter(ApiKey.id == uid))
    apikey = result.scalars().first()
    if not apikey:
        raise ApiKeyNotFoundException(message="ApiKey not found")

    if apikey_updaterole:
        apikey.role = apikey_update.role
    

    await db.commit()
    await db.refresh(apikey)
    return apikey

# Delete a user (asynchronous)
async def delete_apikey(db: AsyncSession, apikey_id: UUID):
    uid = str(apikey_id) if UUIDType is str else apikey_id
    result = await db.execute(select(ApiKey).filter(ApiKey.id == uid))
    db_apikey = result.scalars().first()
    if not db_apikey:
        raise UserNotFoundException(message="ApiKey not found", code=404)
    await db.delete(db_apikey)
    await db.commit()

# Filter users dynamically (asynchronous)
async def filter_apikeys(db: AsyncSession, filters: dict):
    # Start with the base query
    query = select(ApiKey)
    
    # Apply filters dynamically
    for field, value in filters.items():
        if hasattr(ApiKey, field):  # Check if User model has the attribute (field)
            query = query.filter(getattr(ApiKey, field) == value)

    # Execute the query after all filters are applied
    result = await db.execute(query)
    
    # Get all users as a list of dictionaries
    res=result.scalars().all()
    apikeys = []
    # Remove sensitive keys from each user's dictionary
    for apikey in res:
        apikey_dict = apikey.to_dict()
        
        apikeys.append(apikey_dict)
    return apikeys
 
