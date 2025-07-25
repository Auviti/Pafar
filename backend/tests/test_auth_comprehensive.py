"""
Comprehensive tests for authentication system.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User, UserType
from app.services.auth_service import auth_service


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def db_session():
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
        "phone": "+1234567890",
        "user_type": "customer"
    }


@pytest.fixture
async def created_user(db_session: AsyncSession, test_user_data):
    """Create a test user in the database."""
    user = User(
        id=uuid4(),
        email=test_user_data["email"],
        phone=test_user_data["phone"],
        full_name=test_user_data["full_name"],
        password_hash=auth_service.hash_password(test_user_data["password"]),
        user_type=UserType.CUSTOMER,
        is_verified=True,
        is_active=True,
        average_rating=0.0,
        total_rides=0,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestUserRegistration:
    """Test user registration functionality."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
        assert data["phone"] == test_user_data["phone"]
        assert data["user_type"] == test_user_data["user_type"]
        assert data["is_verified"] is False  # Should require email verification
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user_data, created_user):
        """Test registration with duplicate email."""
        response = client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, client, test_user_data, created_user):
        """Test registration with duplicate phone number."""
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        
        response = client.post("/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "Phone number already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client, test_user_data):
        """Test registration with invalid email."""
        invalid_data = test_user_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client, test_user_data):
        """Test registration with weak password."""
        weak_data = test_user_data.copy()
        weak_data["password"] = "weak"
        
        response = client.post("/auth/register", json=weak_data)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        incomplete_data = {
            "email": "test@example.com",
            "password": "TestPassword123"
            # Missing full_name and phone
        }
        
        response = client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422


class TestUserLogin:
    """Test user login functionality."""
    
    @pytest.mark.asyncio
    async def test_login_success_form_data(self, client, test_user_data, created_user):
        """Test successful login with form data."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_login_success_json(self, client, test_user_data, created_user):
        """Test successful login with JSON data."""
        response = client.post(
            "/auth/login-json",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, test_user_data, created_user):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password"
            }
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_unverified_user(self, client, test_user_data, db_session):
        """Test login with unverified user."""
        # Create unverified user
        user = User(
            id=uuid4(),
            email=test_user_data["email"],
            phone=test_user_data["phone"],
            full_name=test_user_data["full_name"],
            password_hash=auth_service.hash_password(test_user_data["password"]),
            user_type=UserType.CUSTOMER,
            is_verified=False,  # Not verified
            is_active=True,
            average_rating=0.0,
            total_rides=0,
        )
        db_session.add(user)
        await db_session.commit()
        
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert response.status_code == 403
        assert "Email not verified" in response.json()["detail"]


class TestUserProfile:
    """Test user profile management."""
    
    @pytest.mark.asyncio
    async def test_get_profile_success(self, client, test_user_data, created_user):
        """Test getting user profile."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Get profile
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["full_name"] == test_user_data["full_name"]
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client):
        """Test getting profile without authentication."""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_profile_success(self, client, test_user_data, created_user):
        """Test updating user profile."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Update profile
        update_data = {
            "full_name": "Updated Name",
            "phone": "+9876543210"
        }
        response = client.put(
            "/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["phone"] == "+9876543210"
    
    @pytest.mark.asyncio
    async def test_update_profile_duplicate_phone(self, client, test_user_data, created_user, db_session):
        """Test updating profile with duplicate phone number."""
        # Create another user
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            phone="+1111111111",
            full_name="Other User",
            password_hash=auth_service.hash_password("password123"),
            user_type=UserType.CUSTOMER,
            is_verified=True,
            is_active=True,
            average_rating=0.0,
            total_rides=0,
        )
        db_session.add(other_user)
        await db_session.commit()
        
        # Login as first user
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to update with other user's phone
        update_data = {"phone": "+1111111111"}
        response = client.put(
            "/auth/me",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Phone number already in use" in response.json()["detail"]


class TestEmailVerification:
    """Test email verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, client, test_user_data, db_session):
        """Test successful email verification."""
        # Create unverified user
        user = User(
            id=uuid4(),
            email=test_user_data["email"],
            phone=test_user_data["phone"],
            full_name=test_user_data["full_name"],
            password_hash=auth_service.hash_password(test_user_data["password"]),
            user_type=UserType.CUSTOMER,
            is_verified=False,
            is_active=True,
            average_rating=0.0,
            total_rides=0,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Generate verification token
        token = auth_service.generate_verification_token(user.id)
        
        # Verify email
        response = client.post(f"/auth/verify-email?token={token}")
        assert response.status_code == 200
        assert "Email verified successfully" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client):
        """Test email verification with invalid token."""
        response = client.post("/auth/verify-email?token=invalid_token")
        assert response.status_code == 400
        assert "Invalid or expired verification token" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_resend_verification(self, client, test_user_data, db_session):
        """Test resending verification email."""
        # Create unverified user
        user = User(
            id=uuid4(),
            email=test_user_data["email"],
            phone=test_user_data["phone"],
            full_name=test_user_data["full_name"],
            password_hash=auth_service.hash_password(test_user_data["password"]),
            user_type=UserType.CUSTOMER,
            is_verified=False,
            is_active=True,
            average_rating=0.0,
            total_rides=0,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Create token for login (even though unverified)
        token = auth_service.create_access_token({"sub": str(user.id)})
        
        # Resend verification
        response = client.post(
            "/auth/resend-verification",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "Verification email sent successfully" in response.json()["message"]


class TestPasswordReset:
    """Test password reset functionality."""
    
    @pytest.mark.asyncio
    async def test_password_reset_request(self, client, test_user_data, created_user):
        """Test password reset request."""
        response = client.post(
            "/auth/password-reset-request",
            json={"email": test_user_data["email"]}
        )
        assert response.status_code == 200
        assert "password reset link has been sent" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_password_reset_nonexistent_email(self, client):
        """Test password reset request for non-existent email."""
        response = client.post(
            "/auth/password-reset-request",
            json={"email": "nonexistent@example.com"}
        )
        # Should return success for security (don't reveal if email exists)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_password_reset_confirm(self, client, test_user_data, created_user):
        """Test password reset confirmation."""
        # Generate reset token
        token = auth_service.generate_reset_token(created_user.id)
        
        # Reset password
        new_password = "NewPassword123"
        response = client.post(
            f"/auth/password-reset-confirm?token={token}&new_password={new_password}"
        )
        assert response.status_code == 200
        assert "Password reset successfully" in response.json()["message"]
        
        # Verify can login with new password
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": new_password
            }
        )
        assert login_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_password_reset_invalid_token(self, client):
        """Test password reset with invalid token."""
        response = client.post(
            "/auth/password-reset-confirm?token=invalid_token&new_password=NewPassword123"
        )
        assert response.status_code == 400


class TestPasswordUpdate:
    """Test password update functionality."""
    
    @pytest.mark.asyncio
    async def test_password_update_success(self, client, test_user_data, created_user):
        """Test successful password update."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Update password
        new_password = "NewPassword123"
        response = client.post(
            "/auth/password-update",
            json={
                "current_password": test_user_data["password"],
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]
        
        # Verify can login with new password
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": new_password
            }
        )
        assert login_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_password_update_wrong_current(self, client, test_user_data, created_user):
        """Test password update with wrong current password."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to update with wrong current password
        response = client.post(
            "/auth/password-update",
            json={
                "current_password": "wrongpassword",
                "new_password": "NewPassword123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]


class TestTokenValidation:
    """Test JWT token validation."""
    
    @pytest.mark.asyncio
    async def test_verify_token_valid(self, client, test_user_data, created_user):
        """Test token verification with valid token."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Verify token
        response = client.get(
            "/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["email"] == test_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, client):
        """Test token verification with invalid token."""
        response = client.get(
            "/auth/verify-token",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout(self, client, test_user_data, created_user):
        """Test user logout."""
        # Login to get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "Logged out successfully" in response.json()["message"]


class TestAuthService:
    """Test authentication service methods directly."""
    
    @pytest.mark.asyncio
    async def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrongpassword", hashed) is False
    
    @pytest.mark.asyncio
    async def test_create_and_verify_token(self):
        """Test JWT token creation and verification."""
        user_id = str(uuid4())
        token = auth_service.create_access_token({"sub": user_id})
        
        payload = auth_service.verify_token(token)
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    @pytest.mark.asyncio
    async def test_verification_token_lifecycle(self):
        """Test verification token generation and validation."""
        user_id = uuid4()
        token = auth_service.generate_verification_token(user_id)
        
        # Token should be valid
        verified_user_id = auth_service.verify_verification_token(token)
        assert verified_user_id == user_id
        
        # Token should be consumed (single use)
        verified_user_id = auth_service.verify_verification_token(token)
        assert verified_user_id is None
    
    @pytest.mark.asyncio
    async def test_reset_token_lifecycle(self):
        """Test reset token generation and validation."""
        user_id = uuid4()
        token = auth_service.generate_reset_token(user_id)
        
        # Token should be valid
        verified_user_id = auth_service.verify_reset_token(token)
        assert verified_user_id == user_id
        
        # Token should still be valid (not consumed until password reset)
        verified_user_id = auth_service.verify_reset_token(token)
        assert verified_user_id == user_id