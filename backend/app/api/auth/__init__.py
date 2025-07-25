"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...core.database import get_db
from ...models.user import User
from ...schemas.user import (
    UserCreate, UserResponse, UserLogin, UserUpdate, 
    UserPasswordReset, UserPasswordUpdate
)
from ...services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get current authenticated user."""
    payload = auth_service.verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(db, UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    user = await auth_service.create_user(db, user_create)
    
    # Generate and send verification email
    verification_token = auth_service.generate_verification_token(user.id)
    auth_service.send_verification_email(user.email, verification_token)
    
    return user


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access token."""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification instructions."
        )
    
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@router.post("/login-json")
async def login_json(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    """Alternative login endpoint that accepts JSON payload."""
    user = await auth_service.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification instructions."
        )
    
    access_token = auth_service.create_access_token({"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Update current user profile."""
    updated_user = await auth_service.update_user(db, current_user, user_update)
    return updated_user


@router.post("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify user email with verification token."""
    success = await auth_service.verify_user_email(db, token)
    if success:
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )


@router.post("/resend-verification")
async def resend_verification(current_user: User = Depends(get_current_user)):
    """Resend email verification for current user."""
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    verification_token = auth_service.generate_verification_token(current_user.id)
    success = auth_service.send_verification_email(current_user.email, verification_token)
    
    if success:
        return {"message": "Verification email sent successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post("/password-reset-request")
async def password_reset_request(reset_request: UserPasswordReset, db: AsyncSession = Depends(get_db)):
    """Request password reset by email."""
    user = await auth_service.get_user_by_email(db, reset_request.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset link has been sent"}
    
    reset_token = auth_service.generate_reset_token(user.id)
    success = auth_service.send_password_reset_email(user.email, reset_token)
    
    if success:
        return {"message": "If the email exists, a password reset link has been sent"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@router.post("/password-reset-confirm")
async def password_reset_confirm(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
    """Confirm password reset with token and new password."""
    success = await auth_service.reset_password_with_token(db, token, new_password)
    if success:
        return {"message": "Password reset successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed"
        )


@router.post("/password-update")
async def password_update(
    password_update: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Update password for authenticated user."""
    success = await auth_service.update_password(
        db, current_user, password_update.current_password, password_update.new_password
    )
    if success:
        return {"message": "Password updated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password update failed"
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)."""
    return {"message": "Logged out successfully"}


@router.get("/verify-token")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if current token is valid."""
    return {
        "valid": True,
        "user": UserResponse.from_orm(current_user)
    }