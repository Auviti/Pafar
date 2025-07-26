"""
Unit tests for authentication service.
"""
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.services.auth_service import AuthService
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserUpdate, PasswordReset, PasswordResetConfirm, EmailVerification
from app.core.security import get_password_hash, verify_password


@pytest.mark.asyncio
class TestAuthService:
    """Test cases for AuthService."""
    
    async def test_register_user_success(self, db_session: AsyncSession, mock_redis):
        """Test successful user registration."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe",
                phone="+1234567890"
            )
            
            user = await auth_service.register_user(user_data)
            
            assert user.email == "test@example.com"
            assert user.first_name == "John"
            assert user.last_name == "Doe"
            assert user.phone == "+1234567890"
            assert user.role == UserRole.PASSENGER
            assert user.is_verified is False
            assert user.is_active is True
            assert verify_password("TestPass123", user.password_hash)
    
    async def test_register_user_duplicate_email(self, db_session: AsyncSession, mock_redis):
        """Test registration with duplicate email."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Create first user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            await auth_service.register_user(user_data)
            
            # Try to create second user with same email
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(user_data)
            
            assert exc_info.value.status_code == 400
            assert "already exists" in exc_info.value.detail
    
    async def test_register_user_duplicate_phone(self, db_session: AsyncSession, mock_redis):
        """Test registration with duplicate phone number."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Create first user
            user_data1 = UserCreate(
                email="test1@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe",
                phone="+1234567890"
            )
            await auth_service.register_user(user_data1)
            
            # Try to create second user with same phone
            user_data2 = UserCreate(
                email="test2@example.com",
                password="TestPass123",
                first_name="Jane",
                last_name="Doe",
                phone="+1234567890"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(user_data2)
            
            assert exc_info.value.status_code == 400
            assert "phone number already exists" in exc_info.value.detail
    
    async def test_login_user_success(self, db_session: AsyncSession, mock_redis):
        """Test successful user login."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user first
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            user = await auth_service.register_user(user_data)
            
            # Login
            login_data = UserLogin(email="test@example.com", password="TestPass123")
            result = await auth_service.login_user(login_data)
            
            assert "access_token" in result
            assert "refresh_token" in result
            assert result["token_type"] == "bearer"
            assert result["user"].id == user.id
    
    async def test_login_user_invalid_email(self, db_session: AsyncSession, mock_redis):
        """Test login with invalid email."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            login_data = UserLogin(email="nonexistent@example.com", password="TestPass123")
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login_user(login_data)
            
            assert exc_info.value.status_code == 401
            assert "Invalid email or password" in exc_info.value.detail
    
    async def test_login_user_invalid_password(self, db_session: AsyncSession, mock_redis):
        """Test login with invalid password."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user first
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            await auth_service.register_user(user_data)
            
            # Login with wrong password
            login_data = UserLogin(email="test@example.com", password="WrongPass123")
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login_user(login_data)
            
            assert exc_info.value.status_code == 401
            assert "Invalid email or password" in exc_info.value.detail
    
    async def test_login_user_inactive_account(self, db_session: AsyncSession, mock_redis):
        """Test login with inactive account."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user and deactivate
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            user = await auth_service.register_user(user_data)
            user.is_active = False
            await db_session.commit()
            
            # Try to login
            login_data = UserLogin(email="test@example.com", password="TestPass123")
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login_user(login_data)
            
            assert exc_info.value.status_code == 401
            assert "deactivated" in exc_info.value.detail
    
    async def test_verify_email_success(self, db_session: AsyncSession, mock_redis):
        """Test successful email verification."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            user = await auth_service.register_user(user_data)
            
            # Set OTP in mock Redis
            mock_redis.data["email_otp:test@example.com"] = "123456"
            
            # Verify email
            verification_data = EmailVerification(email="test@example.com", otp="123456")
            result = await auth_service.verify_email(verification_data)
            
            assert result is True
            await db_session.refresh(user)
            assert user.is_verified is True
    
    async def test_verify_email_invalid_otp(self, db_session: AsyncSession, mock_redis):
        """Test email verification with invalid OTP."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            await auth_service.register_user(user_data)
            
            # Set different OTP in mock Redis
            mock_redis.data["email_otp:test@example.com"] = "123456"
            
            # Try to verify with wrong OTP
            verification_data = EmailVerification(email="test@example.com", otp="654321")
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.verify_email(verification_data)
            
            assert exc_info.value.status_code == 400
            assert "Invalid or expired OTP" in exc_info.value.detail
    
    async def test_request_password_reset_success(self, db_session: AsyncSession, mock_redis):
        """Test successful password reset request."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            await auth_service.register_user(user_data)
            
            # Request password reset
            reset_data = PasswordReset(email="test@example.com")
            result = await auth_service.request_password_reset(reset_data)
            
            assert result is True
            # Check that OTP was stored
            assert "password_reset_otp:test@example.com" in mock_redis.data
    
    async def test_request_password_reset_nonexistent_user(self, db_session: AsyncSession, mock_redis):
        """Test password reset request for nonexistent user."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Request password reset for nonexistent user
            reset_data = PasswordReset(email="nonexistent@example.com")
            result = await auth_service.request_password_reset(reset_data)
            
            # Should return True for security (don't reveal if email exists)
            assert result is True
    
    async def test_confirm_password_reset_success(self, db_session: AsyncSession, mock_redis):
        """Test successful password reset confirmation."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            user = await auth_service.register_user(user_data)
            old_password_hash = user.password_hash
            
            # Set OTP in mock Redis
            mock_redis.data["password_reset_otp:test@example.com"] = "123456"
            
            # Confirm password reset
            reset_data = PasswordResetConfirm(
                email="test@example.com",
                otp="123456",
                new_password="NewPass123"
            )
            result = await auth_service.confirm_password_reset(reset_data)
            
            assert result is True
            await db_session.refresh(user)
            assert user.password_hash != old_password_hash
            assert verify_password("NewPass123", user.password_hash)
    
    async def test_confirm_password_reset_invalid_otp(self, db_session: AsyncSession, mock_redis):
        """Test password reset confirmation with invalid OTP."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            await auth_service.register_user(user_data)
            
            # Set different OTP in mock Redis
            mock_redis.data["password_reset_otp:test@example.com"] = "123456"
            
            # Try to confirm with wrong OTP
            reset_data = PasswordResetConfirm(
                email="test@example.com",
                otp="654321",
                new_password="NewPass123"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.confirm_password_reset(reset_data)
            
            assert exc_info.value.status_code == 400
            assert "Invalid or expired OTP" in exc_info.value.detail
    
    async def test_update_user_profile_success(self, db_session: AsyncSession, mock_redis):
        """Test successful user profile update."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register user
            user_data = UserCreate(
                email="test@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe"
            )
            user = await auth_service.register_user(user_data)
            
            # Update profile
            update_data = UserUpdate(
                first_name="Jane",
                last_name="Smith",
                phone="+1234567890"
            )
            updated_user = await auth_service.update_user_profile(user.id, update_data)
            
            assert updated_user.first_name == "Jane"
            assert updated_user.last_name == "Smith"
            assert updated_user.phone == "+1234567890"
    
    async def test_update_user_profile_duplicate_phone(self, db_session: AsyncSession, mock_redis):
        """Test profile update with duplicate phone number."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            # Register first user
            user_data1 = UserCreate(
                email="test1@example.com",
                password="TestPass123",
                first_name="John",
                last_name="Doe",
                phone="+1234567890"
            )
            await auth_service.register_user(user_data1)
            
            # Register second user
            user_data2 = UserCreate(
                email="test2@example.com",
                password="TestPass123",
                first_name="Jane",
                last_name="Smith"
            )
            user2 = await auth_service.register_user(user_data2)
            
            # Try to update second user with first user's phone
            update_data = UserUpdate(phone="+1234567890")
            
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.update_user_profile(user2.id, update_data)
            
            assert exc_info.value.status_code == 400
            assert "already in use" in exc_info.value.detail
    
    async def test_logout_user_success(self, db_session: AsyncSession, mock_redis):
        """Test successful user logout."""
        with patch('app.services.auth_service.redis_client', mock_redis):
            auth_service = AuthService(db_session)
            
            user_id = uuid4()
            mock_redis.data[f"refresh_token:{user_id}"] = "some_token"
            
            result = await auth_service.logout_user(user_id)
            
            assert result is True
            assert f"refresh_token:{user_id}" not in mock_redis.data
    
    async def test_generate_otp(self, db_session: AsyncSession):
        """Test OTP generation."""
        auth_service = AuthService(db_session)
        
        otp = auth_service._generate_otp()
        
        assert len(otp) == 6
        assert otp.isdigit()
        
        # Test custom length
        otp_custom = auth_service._generate_otp(8)
        assert len(otp_custom) == 8
        assert otp_custom.isdigit()