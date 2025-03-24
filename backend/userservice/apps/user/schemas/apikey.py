from sqlalchemy import Integer, String, DateTime, UUID, ForeignKey
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4
import sys

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

# Enum for user roles (make sure it's a valid Enum class)
class UserRole(str, Enum):
    Guest = 'Guest'
    Buyer = "Buyer"
    Seller = "Seller"
    Admin = "Admin"
    GodAdmin = "GodAdmin"
    SuperAdmin = "SuperAdmin"
    Moderator = "Moderator"
    Support = "Support"
    Manager = "Manager"

# Pydantic schema for Address base (used in create, update, and view)
class ApiKeyBase(BaseModel):
    api_key: str
    user_id: UUID
    role: UserRole  # Enum for UserRole 

    class Config:
        from_attributes = True

class ApiKeyCreate(ApiKeyBase):
    """ Schema for creating a new address. """
    pass

class ApiKeyUpdate(BaseModel):
    """ Schema for updating an existing address. """
    role: UserRole  # Enum for UserRole 

    class Config:
        from_attributes = True

class ApiKeyView(ApiKeyBase):
    id: UUIDType
    expires_at: str
    created_at: str



