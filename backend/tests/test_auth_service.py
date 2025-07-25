"""
Tests for authentication service functionality.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.user import User, UserType
from app.services.auth_service import auth_service
from app.schemas.user import UserCreate, UserUpdate


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


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(wrong_password, hashed) is False


class TestJWTTokens:
    """Test JWT token functionality."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        user_id = str(uuid4())
        token = auth_service.create_access_token({"sub": user_id})
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT format has dots
    
    def test_verify_token_valid(self):
        """Test JWT token verification with valid token."""
        user_id = str(uuid4())
        token = auth_service.create_access_token({"sub": user_id})
        
        payload = auth_service.verify_token(token)
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException
            auth_service.verify_token("invalid_token")
    
    def test_token_expiration(self):
        """Test token with custom expiration."""
        user_id = str(uuid4())
        short_expiry = timedelta(seconds=1)
        token = auth_service.create_access_token({"sub": user_id}, short_expiry)
        
        # Token should be valid immediately
        payload = auth_service.verify_token(token)
        assert payload["sub"] == user_id


class TestUserOperations:
    """Test user database operations."""
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session, created_user):
        """Test getting user by email."""
        user = await auth_service.get_user_by_email(db_session, created_user.email)
        assert user is not None
        assert user.email == created_user.email
        assert user.id == created_user.id
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, db_session):
        """Test getting user by email when user doesn't exist."""
        user = await auth_service.get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session, created_user):
        """Test getting user by ID."""
        user = await auth_service.get_user_by_id(db_session, created_user.id)
        assert user is not None
        assert user.id == created_user.id
        assert user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session):
        """Test getting user by ID when user doesn't exist."""
        user = await auth_service.get_user_by_id(db_session, uuid4())
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session, test_user_data):
        """Test successful user creation."""
        user_create = UserCreate(**test_user_data)
        user = await auth_service.create_user(db_session, user_create)
        
        assert user.email == test_user_data["email"]
        assert user.full_name == test_user_data["full_name"]
        assert user.phone == test_user_data["phone"]
        assert user.user_type == UserType.CUSTOMER
        assert user.is_verified is False  # Should require verification
        assert user.is_active is True
        assert user.id is not None
        
        # Password should be hashed
        assert user.password_hash != test_user_data["password"]
        assert auth_service.verify_password(test_user_data["password"], user.password_hash)
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session, test_user_data, created_user):
        """Test user creation with duplicate email."""
        user_create = UserCreate(**test_user_data)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.create_user(db_session, user_create)
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_phone(self, db_session, test_user_data, created_user):
        """Test user creation with duplicate phone."""
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        user_create = UserCreate(**duplicate_data)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.create_user(db_session, user_create)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session, test_user_data, created_user):
        """Test successful user authentication."""
        user = await auth_service.authenticate_user(
            db_session, test_user_data["email"], test_user_data["password"]
        )
        assert user is not None
        assert user.id == created_user.id
        assert user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session, test_user_data, created_user):
        """Test user authentication with wrong password."""
        user = await auth_service.authenticate_user(
            db_session, test_user_data["email"], "wrongpassword"
        )
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session):
        """Test user authentication with non-existent email."""
        user = await auth_service.authenticate_user(
            db_session, "nonexistent@example.com", "password"
        )
        assert user is None
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, db_session, created_user):
        """Test successful user update."""
        update_data = UserUpdate(
            full_name="Updated Name",
            phone="+9876543210"
        )
        
        updated_user = await auth_service.update_user(db_session, created_user, update_data)
        assert updated_user.full_name == "Updated Name"
        assert updated_user.phone == "+9876543210"
        assert updated_user.email == created_user.email  # Should remain unchanged
    
    @pytest.mark.asyncio
    async def test_update_user_duplicate_phone(self, db_session, created_user, test_user_data):
        """Test user update with duplicate phone number."""
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
        
        # Try to update first user with second user's phone
        update_data = UserUpdate(phone="+1111111111")
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.update_user(db_session, created_user, update_data)
    
    @pytest.mark.asyncio
    async def test_update_password_success(self, db_session, test_user_data, created_user):
        """Test successful password update."""
        new_password = "NewPassword123"
        success = await auth_service.update_password(
            db_session, created_user, test_user_data["password"], new_password
        )
        
        assert success is True
        
        # Verify old password no longer works
        assert auth_service.verify_password(test_user_data["password"], created_user.password_hash) is False
        
        # Verify new password works
        assert auth_service.verify_password(new_password, created_user.password_hash) is True
    
    @pytest.mark.asyncio
    async def test_update_password_wrong_current(self, db_session, created_user):
        """Test password update with wrong current password."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.update_password(
                db_session, created_user, "wrongpassword", "NewPassword123"
            )


class TestVerificationTokens:
    """Test email verification token functionality."""
    
    def test_generate_verification_token(self):
        """Test verification token generation."""
        user_id = uuid4()
        token = auth_service.generate_verification_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token in auth_service.verification_tokens
    
    def test_verify_verification_token_valid(self):
        """Test verification token validation with valid token."""
        user_id = uuid4()
        token = auth_service.generate_verification_token(user_id)
        
        verified_user_id = auth_service.verify_verification_token(token)
        assert verified_user_id == user_id
    
    def test_verify_verification_token_invalid(self):
        """Test verification token validation with invalid token."""
        verified_user_id = auth_service.verify_verification_token("invalid_token")
        assert verified_user_id is None
    
    def test_verification_token_single_use(self):
        """Test that verification tokens are single-use."""
        user_id = uuid4()
        token = auth_service.generate_verification_token(user_id)
        
        # First use should work
        verified_user_id = auth_service.verify_verification_token(token)
        assert verified_user_id == user_id
        
        # Second use should fail
        verified_user_id = auth_service.verify_verification_token(token)
        assert verified_user_id is None
    
    @pytest.mark.asyncio
    async def test_verify_user_email_success(self, db_session, test_user_data):
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
        
        # Generate and verify token
        token = auth_service.generate_verification_token(user.id)
        success = await auth_service.verify_user_email(db_session, token)
        
        assert success is True
        
        # Check user is now verified
        await db_session.refresh(user)
        assert user.is_verified is True
    
    @pytest.mark.asyncio
    async def test_verify_user_email_invalid_token(self, db_session):
        """Test email verification with invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.verify_user_email(db_session, "invalid_token")


class TestResetTokens:
    """Test password reset token functionality."""
    
    def test_generate_reset_token(self):
        """Test reset token generation."""
        user_id = uuid4()
        token = auth_service.generate_reset_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert token in auth_service.reset_tokens
    
    def test_verify_reset_token_valid(self):
        """Test reset token validation with valid token."""
        user_id = uuid4()
        token = auth_service.generate_reset_token(user_id)
        
        verified_user_id = auth_service.verify_reset_token(token)
        assert verified_user_id == user_id
    
    def test_verify_reset_token_invalid(self):
        """Test reset token validation with invalid token."""
        verified_user_id = auth_service.verify_reset_token("invalid_token")
        assert verified_user_id is None
    
    def test_reset_token_reusable(self):
        """Test that reset tokens can be used multiple times until consumed."""
        user_id = uuid4()
        token = auth_service.generate_reset_token(user_id)
        
        # Multiple verifications should work
        verified_user_id = auth_service.verify_reset_token(token)
        assert verified_user_id == user_id
        
        verified_user_id = auth_service.verify_reset_token(token)
        assert verified_user_id == user_id
    
    @pytest.mark.asyncio
    async def test_reset_password_with_token_success(self, db_session, test_user_data, created_user):
        """Test successful password reset with token."""
        token = auth_service.generate_reset_token(created_user.id)
        new_password = "NewPassword123"
        
        success = await auth_service.reset_password_with_token(db_session, token, new_password)
        assert success is True
        
        # Verify old password no longer works
        assert auth_service.verify_password(test_user_data["password"], created_user.password_hash) is False
        
        # Verify new password works
        await db_session.refresh(created_user)
        assert auth_service.verify_password(new_password, created_user.password_hash) is True
        
        # Token should be consumed
        assert token not in auth_service.reset_tokens
    
    @pytest.mark.asyncio
    async def test_reset_password_with_invalid_token(self, db_session):
        """Test password reset with invalid token."""
        with pytest.raises(Exception):  # Should raise HTTPException
            await auth_service.reset_password_with_token(db_session, "invalid_token", "NewPassword123")


class TestEmailFunctions:
    """Test email sending functions."""
    
    def test_send_verification_email(self):
        """Test verification email sending (mock)."""
        success = auth_service.send_verification_email("test@example.com", "test_token")
        assert success is True  # Should always return True in development mode
    
    def test_send_password_reset_email(self):
        """Test password reset email sending (mock)."""
        success = auth_service.send_password_reset_email("test@example.com", "test_token")
        assert success is True  # Should always return True in development mode