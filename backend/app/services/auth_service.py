"""
Authentication service for user management and JWT operations.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..core.config import settings
from ..models.user import User, UserType
from ..schemas.user import UserCreate, UserUpdate


class AuthService:
    """Service class for authentication operations."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.verification_tokens: Dict[str, Dict[str, Any]] = {}  # In-memory store for demo
        self.reset_tokens: Dict[str, Dict[str, Any]] = {}  # In-memory store for demo
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def create_user(self, db: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.get_user_by_email(db, user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if phone already exists
        result = await db.execute(select(User).where(User.phone == user_create.phone))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
        
        # Create new user
        user = User(
            id=uuid4(),
            email=user_create.email,
            phone=user_create.phone,
            full_name=user_create.full_name,
            password_hash=self.hash_password(user_create.password),
            user_type=user_create.user_type,
            is_verified=False,  # Email verification required
            is_active=True,
            average_rating=0.0,
            total_rides=0,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(db, email)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    async def update_user(self, db: AsyncSession, user: User, user_update: UserUpdate) -> User:
        """Update user information."""
        update_data = user_update.dict(exclude_unset=True)
        
        # Check if phone number is being updated and is unique
        if "phone" in update_data and update_data["phone"] != user.phone:
            result = await db.execute(select(User).where(User.phone == update_data["phone"]))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already in use"
                )
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update_password(self, db: AsyncSession, user: User, current_password: str, new_password: str) -> bool:
        """Update user password after verifying current password."""
        if not self.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        user.password_hash = self.hash_password(new_password)
        await db.commit()
        return True
    
    def generate_verification_token(self, user_id: UUID) -> str:
        """Generate email verification token."""
        token = secrets.token_urlsafe(32)
        self.verification_tokens[token] = {
            "user_id": str(user_id),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "type": "email_verification"
        }
        return token
    
    def generate_reset_token(self, user_id: UUID) -> str:
        """Generate password reset token."""
        token = secrets.token_urlsafe(32)
        self.reset_tokens[token] = {
            "user_id": str(user_id),
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "type": "password_reset"
        }
        return token
    
    def verify_verification_token(self, token: str) -> Optional[UUID]:
        """Verify email verification token."""
        token_data = self.verification_tokens.get(token)
        if not token_data:
            return None
        
        if datetime.utcnow() > token_data["expires_at"]:
            del self.verification_tokens[token]
            return None
        
        user_id = UUID(token_data["user_id"])
        del self.verification_tokens[token]  # Token is single-use
        return user_id
    
    def verify_reset_token(self, token: str) -> Optional[UUID]:
        """Verify password reset token."""
        token_data = self.reset_tokens.get(token)
        if not token_data:
            return None
        
        if datetime.utcnow() > token_data["expires_at"]:
            del self.reset_tokens[token]
            return None
        
        return UUID(token_data["user_id"])
    
    async def verify_user_email(self, db: AsyncSession, token: str) -> bool:
        """Verify user email with token."""
        user_id = self.verify_verification_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_verified = True
        await db.commit()
        return True
    
    async def reset_password_with_token(self, db: AsyncSession, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        user_id = self.verify_reset_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = await self.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.password_hash = self.hash_password(new_password)
        await db.commit()
        
        # Clean up the token
        del self.reset_tokens[token]
        return True
    
    def send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification email (simplified for development)."""
        verification_url = f"http://localhost:3000/verify-email?token={token}"
        print(f"Email verification would be sent to {email}")
        print(f"Verification URL: {verification_url}")
        print(f"Token: {token}")
        return True  # Always return True for development
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email (simplified for development)."""
        reset_url = f"http://localhost:3000/reset-password?token={token}"
        print(f"Password reset email would be sent to {email}")
        print(f"Reset URL: {reset_url}")
        print(f"Token: {token}")
        return True  # Always return True for development


# Global auth service instance
auth_service = AuthService()