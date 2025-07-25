"""
User model for authentication and profile management.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..core.database import Base


class UserType(str, Enum):
    """User type enumeration."""
    CUSTOMER = "customer"
    DRIVER = "driver"
    ADMIN = "admin"


class User(Base):
    """User model for customers, drivers, and admins."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False, default=UserType.CUSTOMER)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    profile_image_url = Column(String(500), nullable=True)
    average_rating = Column(Float, default=0.0, nullable=False)
    total_rides = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, type={self.user_type})>"