"""
Authentication service with user management and JWT token handling.
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserUpdate, PasswordReset, PasswordResetConfirm, EmailVerification
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.core.redis import redis_client


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user with email verification."""
        # Check if user already exists
        existing_user = await self._get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check if phone number is already used
        if user_data.phone:
            existing_phone = await self._get_user_by_phone(user_data.phone)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            is_verified=False,  # Require email verification
            is_active=True
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        # Generate and send verification OTP
        await self._send_verification_otp(db_user.email)
        
        return db_user
    
    async def login_user(self, login_data: UserLogin) -> dict:
        """Authenticate user and return JWT tokens."""
        user = await self._get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Generate tokens
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in Redis
        await redis_client.setex(
            f"refresh_token:{user.id}",
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            refresh_token
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user
        }
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Generate new access token using refresh token."""
        try:
            payload = verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Check if refresh token exists in Redis
            stored_token = await redis_client.get(f"refresh_token:{user_id}")
            if not stored_token or stored_token != refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            
            # Get user and generate new access token
            user = await self._get_user_by_id(UUID(user_id))
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
            access_token = create_access_token(token_data)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def logout_user(self, user_id: UUID) -> bool:
        """Logout user by invalidating refresh token."""
        await redis_client.delete(f"refresh_token:{user_id}")
        return True
    
    async def verify_email(self, verification_data: EmailVerification) -> bool:
        """Verify user email with OTP."""
        user = await self._get_user_by_email(verification_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check OTP
        stored_otp = await redis_client.get(f"email_otp:{user.email}")
        if not stored_otp or stored_otp != verification_data.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Mark user as verified
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        
        # Remove OTP from Redis
        await redis_client.delete(f"email_otp:{user.email}")
        
        return True
    
    async def request_password_reset(self, reset_data: PasswordReset) -> bool:
        """Request password reset with OTP."""
        user = await self._get_user_by_email(reset_data.email)
        if not user:
            # Don't reveal if email exists for security
            return True
        
        # Generate and send reset OTP
        await self._send_password_reset_otp(user.email)
        return True
    
    async def confirm_password_reset(self, reset_data: PasswordResetConfirm) -> bool:
        """Confirm password reset with OTP and set new password."""
        user = await self._get_user_by_email(reset_data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check OTP
        stored_otp = await redis_client.get(f"password_reset_otp:{user.email}")
        if not stored_otp or stored_otp != reset_data.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Update password
        user.password_hash = get_password_hash(reset_data.new_password)
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        
        # Remove OTP from Redis and invalidate all refresh tokens
        await redis_client.delete(f"password_reset_otp:{user.email}")
        await redis_client.delete(f"refresh_token:{user.id}")
        
        return True
    
    async def update_user_profile(self, user_id: UUID, update_data: UserUpdate) -> User:
        """Update user profile information."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if phone number is already used by another user
        if update_data.phone and update_data.phone != user.phone:
            existing_phone = await self._get_user_by_phone(update_data.phone)
            if existing_phone and existing_phone.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number is already in use"
                )
        
        # Update fields
        if update_data.first_name is not None:
            user.first_name = update_data.first_name
        if update_data.last_name is not None:
            user.last_name = update_data.last_name
        if update_data.phone is not None:
            user.phone = update_data.phone
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        try:
            payload = verify_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            user = await self._get_user_by_id(UUID(user_id))
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is deactivated"
                )
            
            return user
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def _get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone number."""
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def _send_verification_otp(self, email: str) -> None:
        """Generate and store email verification OTP."""
        otp = self._generate_otp()
        
        # Store OTP in Redis with 10 minute expiration
        await redis_client.setex(f"email_otp:{email}", 600, otp)
        
        # TODO: Send email with OTP (implement email service)
        print(f"Email verification OTP for {email}: {otp}")
    
    async def _send_password_reset_otp(self, email: str) -> None:
        """Generate and store password reset OTP."""
        otp = self._generate_otp()
        
        # Store OTP in Redis with 10 minute expiration
        await redis_client.setex(f"password_reset_otp:{email}", 600, otp)
        
        # TODO: Send email with OTP (implement email service)
        print(f"Password reset OTP for {email}: {otp}")
    
    def _generate_otp(self, length: int = 6) -> str:
        """Generate random OTP."""
        return ''.join(secrets.choice(string.digits) for _ in range(length))