from sqlalchemy.orm import mapped_column, Mapped, relationship, validates
from sqlalchemy import Enum, Integer, String, DateTime, ForeignKey, Boolean, Text
from core.database import Base, CHAR_LENGTH
from core.utils.encryption import PasswordManager
from uuid import uuid4  # to generate unique UUIDs
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from uuid import UUID
import sys


# Database type detection
if 'postgresql' in sys.argv:
    # Use native UUID for PostgreSQL
    UUIDType = UUID(as_uuid=True)
    mappeditem = UUID
    default = uuid4
else:
    # Use string representation for other databases
    UUIDType = String(36)
    mappeditem = str
    default = lambda: str(uuid4())

# Enum for Address types: Billing or Shipping
class AddressType(PyEnum):
    Billing = "Billing"
    Shipping = "Shipping"

class Address(Base):
    __tablename__ = "addresses"

    # Define the fields
    # Use UUID type with default to auto-generate UUID
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    
    email_address: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Optional email field
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)  # ForeignKey referencing user (UUID)
    user: Mapped["User"] = relationship("User", back_populates="addresses" , uselist=False)  # Relationship with User model
    
    street: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Optional street
    city: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Optional city
    state: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Optional state
    country: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Optional country
    post_code: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Optional postal code
    kind: Mapped[AddressType] = mapped_column(Enum(AddressType), nullable=False)  # Address type (either Billing or Shipping)

    # Optional timestamp for tracking address creation/updates
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Optional timestamp
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Auto update timestamp
    
    
    def __repr__(self):
        return f"Address(id={self.id!r}, kind={self.kind!r}, email_address={self.email_address!r})"

    
# Enum for user roles (make sure it's a valid Enum class)
class UserRole(PyEnum):
    Guest = 'Guest'
    Customer = "Customer"
    Driver = "Driver"
    Admin = "Admin"
    Moderator = "Moderator"
    Support = "Support"
    Manager = "Manager"
    SuperAdmin = "SuperAdmin"
    GodAdmin = "GodAdmin"

class UserGender(PyEnum):
    Male = 'Male'
    Female = "Female"

class User(Base):
    __tablename__ = "users"
    
    # Use UUID type with default to auto-generate UUID
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation
    
    # User details
    firstname: Mapped[str] = mapped_column(String(CHAR_LENGTH))  # First name as string
    lastname: Mapped[str] = mapped_column(String(CHAR_LENGTH))  # Last name as string
    password: Mapped[str] = mapped_column(Text, nullable=True)  # Password as string
    email: Mapped[str] = mapped_column(String(CHAR_LENGTH), unique=True, index=True)  # Email as unique string
    picture: Mapped[str] = mapped_column(Text, nullable=True)  # picture as string 
    # Role as Enum with a non-nullable constraint
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)  # User role as Enum
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Created timestamp (UTC)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Updated timestamp (auto updates)
    
    # Additional fields
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_number: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Phone number as string (nullable)
    phone_number_pre: Mapped[str] = mapped_column(String(CHAR_LENGTH), nullable=True)  # Phone number prefix (nullable)
    age: Mapped[int] = mapped_column(Integer, nullable=False)  # Tags as string (nullable)
    gender: Mapped[str] = mapped_column(Enum(UserGender), nullable=False)  # Tags as string (nullable)
    
    # Relationship with Address model
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan", uselist=True, lazy="joined", passive_deletes=True)


    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=True)

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    @validates("role")
    def validate_role(self, key, role):
        # Validate role to ensure it's one of the defined UserRoles
        if role not in UserRole.__members__:
            raise ValueError(f"Invalid role: {role}")
        return role

    def verify_password(self, password):
        password_manager = PasswordManager()
        is_correct = password_manager.verify_password(password, hashed_password = self.password)
        return is_correct

    def to_dict(self):
        return {
            "id": str(self.id),
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "picture":self.picture,
            "role": self.role.value,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "phone_number": self.phone_number,
            "phone_number_pre": self.phone_number_pre,
            "gender": self.gender.value,
            "age": self.age,
            'addresses':self.addresses,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token
        }

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, firstname={self.firstname!r}, lastname={self.lastname!r}, role={self.role!r})"
    
    
# API Key Model
class ApiKey(Base):
    __tablename__ = "api_keys"

    # Use UUID type with default to auto-generate UUID
    id: Mapped[mappeditem] = mapped_column(UUIDType, primary_key=True, default=default)  # UUID with auto-generation

    # Unique API key value
    api_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # User association (Foreign Key to the user table)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)  # ForeignKey referencing user (UUID)

    # The roles associated with the API key (e.g., Buyer, Admin, etc.)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)  # User role as Enum
    
    # Expiration date for the API key
    expires_at: Mapped[datetime] = mapped_column(DateTime,  nullable=False)

    # Timestamp for when the API key was created
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<APIKey(id={self.id}, user_id={self.user_id}, api_key={self.api_key}, expires_at={self.expires_at})>"

    # Method to check if the API key is expired
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @validates("role")
    def validate_role(self, key, role):
        # Validate role to ensure it's one of the defined UserRoles
        if role not in UserRole.__members__:
            raise ValueError(f"Invalid role: {role}")
        return role

    def to_dict(self):
        return {
            "id": str(self.id),
            "api_key": self.api_key,
            "user_id": self.user_id,
            "role": self.role.value,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
