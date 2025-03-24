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

# Enum for Address types: Billing or Shipping
class AddressType(str, Enum):
    Billing = "Billing"
    Shipping = "Shipping"

# Pydantic schema for Address base (used in create, update, and view)
class AddressBase(BaseModel):
    email_address: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    post_code: Optional[str] = None
    kind: AddressType  # Enum for AddressType (Billing or Shipping)

    class Config:
        from_attributes = True

class AddressCreate(AddressBase):
    """ Schema for creating a new address. """
    pass

class AddressUpdate(AddressBase):
    """ Schema for updating an existing address. """
    pass

class AddressView(AddressBase):
    id: UUIDType
    created_at: str
    updated_at: str



