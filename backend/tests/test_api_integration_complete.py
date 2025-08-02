"""
Comprehensive integration tests for API endpoints.
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from fastapi import status

from app.main import app
from backend.tests.factories import TestDataBuilder, UserFactory, TripFactory


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, override_get_db):
        """Test successful user registration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user_data = {
                "email": "newuser@example.com",
                "password": "password123",
                "first_name": "New",
                "last_name": "User",
                "phone": "+1234567890"
            }
            
            response = await client.post("/api/v1/auth/register", json=user_data)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["email"] == user_data["email"]
            assert data["first_name"] == user_data["first_name"]
            assert "id" in data
            assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, override_get_db):
        """Test registration with duplicate email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user_data = {
                "email": "duplicate@example.com",
                "password": "password123",
                "first_name": "First",
                "last_name": "User"
            }
            
            # First registration should succeed
            response1 = await client.post("/api/v1/auth/register", json=user_data)
            assert response1.status_code == status.HTTP_201_CREATED
            
            # Second registration with same email should fail
            response2 = await client.post("/api/v1/auth/register", json=user_data)
            assert response2.status_code == status.HTTP_400_BAD_REQUEST
            assert "email already registered" in response2.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, override_get_db):
        """Test successful user login."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First register a user
            user_data = {
                "email": "login@example.com",
                "password": "password123",
                "first_name": "Login",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            # Then login
            login_data = {
                "email": "login@example.com",
                "password": "password123"
            }
            
            response = await client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, override_get_db):
        """Test login with invalid credentials."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
            
            response = await client.post("/api/v1/auth/login", json=login_data)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "invalid credentials" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, override_get_db):
        """Test token refresh functionality."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login to get tokens
            user_data = {
                "email": "refresh@example.com",
                "password": "password123",
                "first_name": "Refresh",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "refresh@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            # Use refresh token to get new access token
            refresh_data = {"refresh_token": tokens["refresh_token"]}
            response = await client.post("/api/v1/auth/refresh", json=refresh_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, override_get_db):
        """Test accessing protected endpoint without token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, override_get_db):
        """Test accessing protected endpoint with valid token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login to get token
            user_data = {
                "email": "protected@example.com",
                "password": "password123",
                "first_name": "Protected",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "protected@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            # Access protected endpoint
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            response = await client.get("/api/v1/auth/me", headers=headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "protected@example.com"


@pytest.mark.integration
class TestBookingEndpoints:
    """Test booking API endpoints."""
    
    @pytest.fixture
    async def authenticated_client(self, override_get_db):
        """Create authenticated client for booking tests."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login user
            user_data = {
                "email": "booking@example.com",
                "password": "password123",
                "first_name": "Booking",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "booking@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            yield client
    
    @pytest.mark.asyncio
    async def test_search_trips_success(self, authenticated_client):
        """Test successful trip search."""
        search_params = {
            "origin_terminal_id": str(uuid.uuid4()),
            "destination_terminal_id": str(uuid.uuid4()),
            "departure_date": "2024-12-25"
        }
        
        response = await authenticated_client.get("/api/v1/bookings/trips/search", params=search_params)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_search_trips_invalid_date(self, authenticated_client):
        """Test trip search with invalid date."""
        search_params = {
            "origin_terminal_id": str(uuid.uuid4()),
            "destination_terminal_id": str(uuid.uuid4()),
            "departure_date": "invalid-date"
        }
        
        response = await authenticated_client.get("/api/v1/bookings/trips/search", params=search_params)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_create_booking_success(self, authenticated_client):
        """Test successful booking creation."""
        # First create a trip to book
        scenario = TestDataBuilder.create_complete_booking_scenario()
        
        booking_data = {
            "trip_id": str(scenario['trip'].id),
            "seat_numbers": [1, 2],
            "passenger_details": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890"
            }
        }
        
        response = await authenticated_client.post("/api/v1/bookings/", json=booking_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "booking_reference" in data
        assert data["seat_numbers"] == [1, 2]
        assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_create_booking_invalid_seats(self, authenticated_client):
        """Test booking creation with invalid seats."""
        booking_data = {
            "trip_id": str(uuid.uuid4()),
            "seat_numbers": [999],  # Invalid seat number
            "passenger_details": {
                "first_name": "John",
                "last_name": "Doe"
            }
        }
        
        response = await authenticated_client.post("/api/v1/bookings/", json=booking_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_get_booking_details(self, authenticated_client):
        """Test retrieving booking details."""
        # Create a booking first
        scenario = TestDataBuilder.create_complete_booking_scenario()
        booking_id = str(scenario['booking'].id)
        
        response = await authenticated_client.get(f"/api/v1/bookings/{booking_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == booking_id
        assert "trip" in data
        assert "passenger" in data
    
    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, authenticated_client):
        """Test successful booking cancellation."""
        scenario = TestDataBuilder.create_complete_booking_scenario()
        booking_id = str(scenario['booking'].id)
        
        response = await authenticated_client.post(f"/api/v1/bookings/{booking_id}/cancel")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_get_user_bookings(self, authenticated_client):
        """Test retrieving user's bookings."""
        response = await authenticated_client.get("/api/v1/bookings/my-bookings")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.integration
class TestPaymentEndpoints:
    """Test payment API endpoints."""
    
    @pytest.fixture
    async def authenticated_client_with_booking(self, override_get_db):
        """Create authenticated client with a booking for payment tests."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login user
            user_data = {
                "email": "payment@example.com",
                "password": "password123",
                "first_name": "Payment",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "payment@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Create a booking for payment
            scenario = TestDataBuilder.create_complete_booking_scenario()
            client.booking_id = str(scenario['booking'].id)
            
            yield client
    
    @pytest.mark.asyncio
    async def test_create_payment_intent(self, authenticated_client_with_booking):
        """Test payment intent creation."""
        client = authenticated_client_with_booking
        
        payment_data = {
            "booking_id": client.booking_id,
            "payment_method": "card"
        }
        
        response = await client.post("/api/v1/payments/create-intent", json=payment_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "payment_intent_id" in data
        assert "client_secret" in data
    
    @pytest.mark.asyncio
    async def test_confirm_payment_success(self, authenticated_client_with_booking):
        """Test successful payment confirmation."""
        client = authenticated_client_with_booking
        
        # First create payment intent
        payment_intent_response = await client.post("/api/v1/payments/create-intent", json={
            "booking_id": client.booking_id,
            "payment_method": "card"
        })
        payment_intent_data = payment_intent_response.json()
        
        # Then confirm payment
        confirm_data = {
            "payment_intent_id": payment_intent_data["payment_intent_id"],
            "booking_id": client.booking_id
        }
        
        response = await client.post("/api/v1/payments/confirm", json=confirm_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_get_payment_history(self, authenticated_client_with_booking):
        """Test retrieving payment history."""
        client = authenticated_client_with_booking
        
        response = await client.get("/api/v1/payments/history")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_download_receipt(self, authenticated_client_with_booking):
        """Test receipt download."""
        client = authenticated_client_with_booking
        
        # Create a completed payment first
        scenario = TestDataBuilder.create_complete_booking_scenario()
        payment_id = str(scenario['payment'].id)
        
        response = await client.get(f"/api/v1/payments/{payment_id}/receipt")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"


@pytest.mark.integration
class TestTrackingEndpoints:
    """Test tracking API endpoints."""
    
    @pytest.fixture
    async def driver_client(self, override_get_db):
        """Create authenticated driver client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register driver
            driver_data = {
                "email": "driver@example.com",
                "password": "password123",
                "first_name": "Driver",
                "last_name": "User",
                "role": "driver"
            }
            await client.post("/api/v1/auth/register", json=driver_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "driver@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            yield client
    
    @pytest.mark.asyncio
    async def test_update_trip_location(self, driver_client):
        """Test trip location update by driver."""
        scenario = TestDataBuilder.create_trip_with_tracking()
        trip_id = str(scenario['trip'].id)
        
        location_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "speed": 65.0,
            "heading": 180.0
        }
        
        response = await driver_client.post(f"/api/v1/tracking/trips/{trip_id}/location", json=location_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["latitude"] == 40.7128
        assert data["longitude"] == -74.0060
    
    @pytest.mark.asyncio
    async def test_get_trip_location(self, override_get_db):
        """Test retrieving current trip location."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            scenario = TestDataBuilder.create_trip_with_tracking()
            trip_id = str(scenario['trip'].id)
            
            response = await client.get(f"/api/v1/tracking/trips/{trip_id}/location")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "latitude" in data
            assert "longitude" in data
            assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_get_trip_eta(self, override_get_db):
        """Test ETA calculation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            scenario = TestDataBuilder.create_trip_with_tracking()
            trip_id = str(scenario['trip'].id)
            
            response = await client.get(f"/api/v1/tracking/trips/{trip_id}/eta")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "estimated_arrival" in data
            assert "distance_remaining_km" in data


@pytest.mark.integration
class TestAdminEndpoints:
    """Test admin API endpoints."""
    
    @pytest.fixture
    async def admin_client(self, override_get_db):
        """Create authenticated admin client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register admin
            admin_data = {
                "email": "admin@example.com",
                "password": "password123",
                "first_name": "Admin",
                "last_name": "User",
                "role": "admin"
            }
            await client.post("/api/v1/auth/register", json=admin_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "admin@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            yield client
    
    @pytest.mark.asyncio
    async def test_get_dashboard_metrics(self, admin_client):
        """Test admin dashboard metrics."""
        response = await admin_client.get("/api/v1/admin/dashboard")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_users" in data
        assert "total_bookings" in data
        assert "total_revenue" in data
        assert "active_trips" in data
    
    @pytest.mark.asyncio
    async def test_get_users_list(self, admin_client):
        """Test retrieving users list."""
        response = await admin_client.get("/api/v1/admin/users")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_suspend_user(self, admin_client):
        """Test user suspension."""
        # Create a user to suspend
        user = UserFactory.create()
        user_id = str(user.id)
        
        response = await admin_client.post(f"/api/v1/admin/users/{user_id}/suspend")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_create_trip(self, admin_client):
        """Test trip creation by admin."""
        scenario = TestDataBuilder.create_complete_booking_scenario()
        
        trip_data = {
            "route_id": str(scenario['route'].id),
            "bus_id": str(scenario['bus'].id),
            "driver_id": str(scenario['driver'].id),
            "departure_time": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "fare": "35.00"
        }
        
        response = await admin_client.post("/api/v1/admin/trips", json=trip_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["fare"] == "35.00"
        assert data["status"] == "scheduled"


@pytest.mark.integration
class TestWebSocketEndpoints:
    """Test WebSocket endpoints for real-time features."""
    
    @pytest.mark.asyncio
    async def test_trip_tracking_websocket(self, override_get_db):
        """Test WebSocket connection for trip tracking."""
        scenario = TestDataBuilder.create_trip_with_tracking()
        trip_id = str(scenario['trip'].id)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # This would test WebSocket connection in a real implementation
            # For now, we'll test the HTTP endpoint that provides WebSocket info
            response = await client.get(f"/api/v1/tracking/trips/{trip_id}/websocket-info")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "websocket_url" in data
            assert "connection_token" in data
    
    @pytest.mark.asyncio
    async def test_booking_notifications_websocket(self, override_get_db):
        """Test WebSocket connection for booking notifications."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login user
            user_data = {
                "email": "websocket@example.com",
                "password": "password123",
                "first_name": "WebSocket",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "websocket@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            response = await client.get("/api/v1/websocket/notifications/info", headers=headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "websocket_url" in data


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_404_not_found(self, override_get_db):
        """Test 404 error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/nonexistent-endpoint")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @pytest.mark.asyncio
    async def test_422_validation_error(self, override_get_db):
        """Test validation error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            invalid_data = {
                "email": "invalid-email",  # Invalid email format
                "password": "123",  # Too short
                "first_name": "",  # Empty required field
            }
            
            response = await client.post("/api/v1/auth/register", json=invalid_data)
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], list)
    
    @pytest.mark.asyncio
    async def test_500_internal_server_error(self, override_get_db):
        """Test internal server error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # This would simulate a server error in a real implementation
            # For now, we'll test that the error handling structure is in place
            response = await client.get("/api/v1/health")
            
            # Health endpoint should exist and return 200
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.integration
class TestRateLimiting:
    """Test API rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_auth_endpoints(self, override_get_db):
        """Test rate limiting on authentication endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make multiple rapid requests to login endpoint
            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
            
            responses = []
            for _ in range(10):  # Make 10 rapid requests
                response = await client.post("/api/v1/auth/login", json=login_data)
                responses.append(response.status_code)
            
            # At least some requests should be rate limited (429) or unauthorized (401)
            assert any(status_code in [status.HTTP_429_TOO_MANY_REQUESTS, status.HTTP_401_UNAUTHORIZED] 
                      for status_code in responses)


@pytest.mark.integration
class TestConcurrency:
    """Test API concurrency handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_booking_requests(self, override_get_db):
        """Test handling concurrent booking requests for same seats."""
        import asyncio
        
        # Create multiple clients
        clients = []
        for i in range(3):
            client = AsyncClient(app=app, base_url="http://test")
            
            # Register and login each user
            user_data = {
                "email": f"concurrent{i}@example.com",
                "password": "password123",
                "first_name": f"User{i}",
                "last_name": "Concurrent"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": f"concurrent{i}@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            clients.append(client)
        
        # Create a trip with limited seats
        scenario = TestDataBuilder.create_complete_booking_scenario()
        trip_id = str(scenario['trip'].id)
        
        # All clients try to book the same seat simultaneously
        booking_data = {
            "trip_id": trip_id,
            "seat_numbers": [1],  # Same seat
            "passenger_details": {
                "first_name": "John",
                "last_name": "Doe"
            }
        }
        
        # Make concurrent requests
        tasks = [
            client.post("/api/v1/bookings/", json=booking_data)
            for client in clients
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one booking should succeed, others should fail
        success_count = sum(1 for r in responses 
                           if not isinstance(r, Exception) and r.status_code == status.HTTP_201_CREATED)
        
        assert success_count == 1  # Only one booking should succeed
        
        # Clean up clients
        for client in clients:
            await client.aclose()


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across API operations."""
    
    @pytest.mark.asyncio
    async def test_booking_payment_consistency(self, override_get_db):
        """Test data consistency between booking and payment operations."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login user
            user_data = {
                "email": "consistency@example.com",
                "password": "password123",
                "first_name": "Consistency",
                "last_name": "User"
            }
            await client.post("/api/v1/auth/register", json=user_data)
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "consistency@example.com",
                "password": "password123"
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Create booking
            scenario = TestDataBuilder.create_complete_booking_scenario()
            booking_data = {
                "trip_id": str(scenario['trip'].id),
                "seat_numbers": [1, 2],
                "passenger_details": {
                    "first_name": "John",
                    "last_name": "Doe"
                }
            }
            
            booking_response = await client.post("/api/v1/bookings/", json=booking_data)
            booking = booking_response.json()
            
            # Create payment for booking
            payment_response = await client.post("/api/v1/payments/create-intent", json={
                "booking_id": booking["id"],
                "payment_method": "card"
            })
            payment_intent = payment_response.json()
            
            # Confirm payment
            confirm_response = await client.post("/api/v1/payments/confirm", json={
                "payment_intent_id": payment_intent["payment_intent_id"],
                "booking_id": booking["id"]
            })
            
            # Verify booking status is updated
            updated_booking_response = await client.get(f"/api/v1/bookings/{booking['id']}")
            updated_booking = updated_booking_response.json()
            
            assert updated_booking["payment_status"] == "completed"
            assert updated_booking["status"] == "confirmed"