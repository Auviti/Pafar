"""
Integration tests for API endpoints.
"""
import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.fleet import Terminal, Route, Bus, Trip
from app.models.booking import Booking
from app.core.security import create_access_token
from tests.factories import TestDataBuilder, UserFactory, TerminalFactory, RouteFactory, BusFactory, TripFactory


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""
    
    async def test_register_user_success(self, db_session, override_get_db):
        """Test successful user registration via API."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "TestPass123",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone": "+1234567890"
                }
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["role"] == "passenger"
        assert data["is_verified"] is False
    
    async def test_register_user_duplicate_email(self, db_session, override_get_db):
        """Test registration with duplicate email."""
        # Create existing user
        user = UserFactory.create(email="test@example.com")
        db_session.add(user)
        await db_session.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "TestPass123",
                    "first_name": "John",
                    "last_name": "Doe"
                }
            )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]
    
    async def test_login_user_success(self, db_session, override_get_db):
        """Test successful user login via API."""
        # Create verified user
        user = UserFactory.create(
            email="test@example.com",
            password_hash="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"
        )
        db_session.add(user)
        await db_session.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "secret"
                }
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_user_invalid_credentials(self, db_session, override_get_db):
        """Test login with invalid credentials."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "wrongpassword"
                }
            )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid" in response.json()["detail"]
    
    async def test_get_current_user(self, db_session, override_get_db):
        """Test getting current user with valid token."""
        # Create user
        user = UserFactory.create()
        db_session.add(user)
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(user.id)
        assert data["email"] == user.email


@pytest.mark.asyncio
class TestFleetEndpoints:
    """Integration tests for fleet management endpoints."""
    
    async def test_get_terminals(self, db_session, override_get_db):
        """Test getting list of terminals."""
        # Create terminals
        terminal1 = TerminalFactory.create(name="Terminal 1", city="City 1")
        terminal2 = TerminalFactory.create(name="Terminal 2", city="City 2")
        db_session.add_all([terminal1, terminal2])
        await db_session.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/fleet/terminals")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] in ["Terminal 1", "Terminal 2"]
        assert data[1]["name"] in ["Terminal 1", "Terminal 2"]
    
    async def test_get_routes(self, db_session, override_get_db):
        """Test getting list of routes."""
        # Create terminals and route
        origin, destination = TerminalFactory.create_pair()
        route = RouteFactory.create(
            origin_terminal_id=origin.id,
            destination_terminal_id=destination.id
        )
        db_session.add_all([origin, destination, route])
        await db_session.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/fleet/routes")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(route.id)
    
    async def test_search_trips(self, db_session, override_get_db):
        """Test searching for trips."""
        # Create complete trip scenario
        scenario = TestDataBuilder.create_complete_booking_scenario()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip']
        ])
        await db_session.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/fleet/trips/search",
                params={
                    "origin_terminal_id": str(scenario['origin'].id),
                    "destination_terminal_id": str(scenario['destination'].id),
                    "departure_date": scenario['trip'].departure_time.date().isoformat()
                }
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["id"] == str(scenario['trip'].id)


@pytest.mark.asyncio
class TestBookingEndpoints:
    """Integration tests for booking endpoints."""
    
    async def test_create_booking_success(self, db_session, override_get_db):
        """Test successful booking creation."""
        # Create complete scenario
        scenario = TestDataBuilder.create_complete_booking_scenario()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip'], scenario['passenger']
        ])
        await db_session.commit()
        
        # Create access token for passenger
        access_token = create_access_token(data={"sub": str(scenario['passenger'].id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/bookings/",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "trip_id": str(scenario['trip'].id),
                    "seat_numbers": [1, 2]
                }
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["trip_id"] == str(scenario['trip'].id)
        assert data["seat_numbers"] == [1, 2]
        assert data["status"] == "pending"
    
    async def test_get_user_bookings(self, db_session, override_get_db):
        """Test getting user's bookings."""
        # Create scenario with booking
        scenario = TestDataBuilder.create_complete_booking_scenario()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip'], 
            scenario['passenger'], scenario['booking']
        ])
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(scenario['passenger'].id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/bookings/my-bookings",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(scenario['booking'].id)
    
    async def test_cancel_booking(self, db_session, override_get_db):
        """Test booking cancellation."""
        # Create scenario with booking
        scenario = TestDataBuilder.create_complete_booking_scenario()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip'], 
            scenario['passenger'], scenario['booking']
        ])
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(scenario['passenger'].id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/bookings/{scenario['booking'].id}/cancel",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"reason": "Change of plans"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"


@pytest.mark.asyncio
class TestPaymentEndpoints:
    """Integration tests for payment endpoints."""
    
    async def test_create_payment_intent(self, db_session, override_get_db):
        """Test creating payment intent."""
        # Create scenario with booking
        scenario = TestDataBuilder.create_complete_booking_scenario()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip'], 
            scenario['passenger'], scenario['booking']
        ])
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(scenario['passenger'].id)})
        
        with pytest.mock.patch('app.services.payment_service.stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value = {
                'id': 'pi_test123',
                'client_secret': 'pi_test123_secret',
                'amount': 3000,
                'currency': 'usd'
            }
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/payments/create-intent",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "booking_id": str(scenario['booking'].id),
                        "payment_method": "card"
                    }
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "client_secret" in data
        assert "payment_intent_id" in data


@pytest.mark.asyncio
class TestTrackingEndpoints:
    """Integration tests for tracking endpoints."""
    
    async def test_get_trip_location(self, db_session, override_get_db):
        """Test getting trip location."""
        # Create scenario with tracking
        scenario = TestDataBuilder.create_trip_with_tracking()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip']
        ] + scenario['locations'])
        await db_session.commit()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/location"
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "latitude" in data
        assert "longitude" in data
        assert "recorded_at" in data
    
    async def test_update_trip_location_as_driver(self, db_session, override_get_db):
        """Test updating trip location as driver."""
        # Create scenario
        scenario = TestDataBuilder.create_complete_booking_scenario()
        db_session.add_all([
            scenario['origin'], scenario['destination'], scenario['route'],
            scenario['bus'], scenario['driver'], scenario['trip']
        ])
        await db_session.commit()
        
        # Create access token for driver
        access_token = create_access_token(data={"sub": str(scenario['driver'].id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/location",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "speed": 65.0,
                    "heading": 180.0
                }
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["latitude"] == 40.7128
        assert data["longitude"] == -74.0060


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Integration tests for admin endpoints."""
    
    async def test_admin_dashboard_access(self, db_session, override_get_db):
        """Test admin dashboard access."""
        # Create admin user
        admin = UserFactory.create_admin()
        db_session.add(admin)
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(admin.id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/admin/dashboard",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_users" in data
        assert "total_trips" in data
        assert "total_bookings" in data
    
    async def test_admin_dashboard_unauthorized(self, db_session, override_get_db):
        """Test admin dashboard access with non-admin user."""
        # Create regular user
        user = UserFactory.create()
        db_session.add(user)
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user.id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/admin/dashboard",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_admin_manage_users(self, db_session, override_get_db):
        """Test admin user management."""
        # Create admin and regular users
        admin = UserFactory.create_admin()
        user1 = UserFactory.create(email="user1@example.com")
        user2 = UserFactory.create(email="user2@example.com")
        db_session.add_all([admin, user1, user2])
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(admin.id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/admin/users",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2  # At least the two regular users
    
    async def test_admin_suspend_user(self, db_session, override_get_db):
        """Test admin user suspension."""
        # Create admin and regular user
        admin = UserFactory.create_admin()
        user = UserFactory.create()
        db_session.add_all([admin, user])
        await db_session.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": str(admin.id)})
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/admin/users/{user.id}/suspend",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"reason": "Policy violation"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False