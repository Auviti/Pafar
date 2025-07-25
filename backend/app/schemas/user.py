"""
User Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from ..models.user import UserType


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=255)
    user_type: UserType = UserType.CUSTOMER


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        # Remove common phone number characters
        cleaned = ''.join(c for c in v if c.isdigit() or c in '+()-. ')
        if len(cleaned.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    profile_image_url: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v is not None:
            cleaned = ''.join(c for c in v if c.isdigit() or c in '+()-. ')
            if len(cleaned.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) < 10:
                raise ValueError('Phone number must be at least 10 digits')
        return v


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    is_verified: bool
    is_active: bool
    profile_image_url: Optional[str] = None
    average_rating: float
    total_rides: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserPasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class UserPasswordUpdate(BaseModel):
    """Schema for password update."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v