"""
Authentication endpoints for user registration, login, and management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserUpdate, 
    PasswordReset, PasswordResetConfirm, EmailVerification,
    TokenResponse, RefreshTokenRequest
)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get authentication service."""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Dependency to get current authenticated user."""
    return await auth_service.get_current_user(credentials.credentials)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (required)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **first_name**: User's first name (required)
    - **last_name**: User's last name (required)
    - **phone**: Phone number (optional)
    - **role**: User role (passenger, driver, admin) - defaults to passenger
    
    Returns the created user information. Email verification required before login.
    """
    user = await auth_service.register_user(user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT tokens.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token, refresh token, and user information.
    """
    result = await auth_service.login_user(login_data)
    return result


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Generate new access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token.
    """
    result = await auth_service.refresh_access_token(refresh_data.refresh_token)
    return result


@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user by invalidating refresh token.
    
    Requires valid access token in Authorization header.
    """
    await auth_service.logout_user(current_user.id)
    return {"message": "Successfully logged out"}


@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email address with OTP.
    
    - **email**: User's email address
    - **otp**: 6-digit OTP sent to email
    
    Marks the user account as verified.
    """
    await auth_service.verify_email(verification_data)
    return {"message": "Email verified successfully"}


@router.post("/request-password-reset")
async def request_password_reset(
    reset_data: PasswordReset,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Request password reset with OTP.
    
    - **email**: User's email address
    
    Sends OTP to email for password reset.
    """
    await auth_service.request_password_reset(reset_data)
    return {"message": "Password reset OTP sent to email"}


@router.post("/confirm-password-reset")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Confirm password reset with OTP and set new password.
    
    - **email**: User's email address
    - **otp**: 6-digit OTP sent to email
    - **new_password**: New strong password
    
    Resets the user's password and invalidates all sessions.
    """
    await auth_service.confirm_password_reset(reset_data)
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get current user information.
    
    Requires valid access token in Authorization header.
    Returns current user's profile information.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user's profile information.
    
    - **first_name**: Updated first name (optional)
    - **last_name**: Updated last name (optional)
    - **phone**: Updated phone number (optional)
    
    Requires valid access token in Authorization header.
    """
    updated_user = await auth_service.update_user_profile(current_user.id, update_data)
    return updated_user