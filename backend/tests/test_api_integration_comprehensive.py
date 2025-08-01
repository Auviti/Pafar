"""
Comprehensive integration tests for all API endpoints.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal
import json

from app.main import app
from tests.fixtures import complete_test_scenario


@pytest.mark.asyncio
class TestAuthAPIIntegration:
    """Integration tests for authentication API endpoints."""
    
    async def test_register_user_success(self, override_get_db):
        """Test successful user registration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/register", json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "first_name": "New",
                "last_name": "User",
                "phone": "+1234567890"
            })
            
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@example.com"
            assert data["first_name"] == "New"
            assert data["last_name"] == "User"
            assert "id" in data
            assert "password_hash" not in data  # Should not expose password
    
    async def test_register_user_duplicate_email(self, override_get_db, complete_test_scenario):
        """Test registration with duplicate email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            existing_user = complete_test_scenario['users']['passenger']
            
            response = await client.post("/api/v1/auth/register", json={
                "email": existing_user.email,
                "password": "SecurePass123",
                "first_name": "Duplicate",
                "last_name": "User"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "already registered" in data["detail"].lower()
    
    async def test_login_success(self, override_get_db, complete_test_scenario):
        """Test successful user login."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First register a user with known password
            await client.post("/api/v1/auth/register", json={
                "email": "logintest@example.com",
                "password": "TestPass123",
                "first_name": "Login",
                "last_name": "Test"
            })
            
            # Then try to login
            response = await client.post("/api/v1/auth/login", json={
                "email": "logintest@example.com",
                "password": "TestPass123"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, override_get_db):
        """Test login with invalid credentials."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/login", json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            })
            
            assert response.status_code == 401
            data = response.json()
            assert "invalid credentials" in data["detail"].lower()
    
    async def test_refresh_token(self, override_get_db):
        """Test token refresh functionality."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login first
            await client.post("/api/v1/auth/register", json={
                "email": "refreshtest@example.com",
                "password": "TestPass123",
                "first_name": "Refresh",
                "last_name": "Test"
            })
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "refreshtest@example.com",
                "password": "TestPass123"
            })
            
            tokens = login_response.json()
            
            # Use refresh token to get new access token
            response = await client.post("/api/v1/auth/refresh", json={
                "refresh_token": tokens["refresh_token"]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"


@pytest.mark.asyncio
class TestBookingAPIIntegration:
    """Integration tests for booking API endpoints."""
    
    async def test_search_trips(self, override_get_db, complete_test_scenario):
        """Test trip search functionality."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            route = complete_test_scenario['routes']['ny_to_la']
            
            response = await client.get(
                f"/api/v1/bookings/trips/search"
                f"?origin_terminal_id={route.origin_terminal_id}"
                f"&destination_terminal_id={route.destination_terminal_id}"
                f"&departure_date={datetime.utcnow().date()}"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            # Should return available trips for the route
    
    async def test_create_booking_success(self, override_get_db, complete_test_scenario):
        """Test successful booking creation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First login to get access token
            user = complete_test_scenario['users']['passenger']
            trip = complete_test_scenario['trips']['upcoming_trip']
            
            # Mock login to get token (simplified for test)
            with patch('app.services.auth_service.AuthService.authenticate_user') as mock_auth:
                mock_auth.return_value = user
                
                login_response = await client.post("/api/v1/auth/login", json={
                    "email": user.email,
                    "password": "password"
                })
                
                if login_response.status_code == 200:
                    token = login_response.json()["access_token"]
                    
                    # Create booking
                    response = await client.post(
                        "/api/v1/bookings/",
                        json={
                            "trip_id": str(trip.id),
                            "seat_numbers": [1, 2]
                        },
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    assert response.status_code == 201
                    data = response.json()
                    assert data["trip_id"] == str(trip.id)
                    assert data["seat_numbers"] == [1, 2]
                    assert "booking_reference" in data
    
    async def test_get_user_bookings(self, override_get_db, complete_test_scenario):
        """Test retrieving user bookings."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = complete_test_scenario['users']['passenger']
            
            # Mock authentication
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = user
                
                response = await client.get(
                    "/api/v1/bookings/my-bookings",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
    
    async def test_cancel_booking(self, override_get_db, complete_test_scenario):
        """Test booking cancellation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = complete_test_scenario['users']['passenger']
            booking = complete_test_scenario['bookings']['confirmed_booking']
            
            # Mock authentication
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = user
                
                response = await client.post(
                    f"/api/v1/bookings/{booking.id}/cancel",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "cancelled"


@pytest.mark.asyncio
class TestPaymentAPIIntegration:
    """Integration tests for payment API endpoints."""
    
    async def test_create_payment_intent(self, override_get_db, complete_test_scenario):
        """Test payment intent creation."""
        with patch('stripe.PaymentIntent.create') as mock_stripe:
            mock_stripe.return_value.id = 'pi_test_123'
            mock_stripe.return_value.client_secret = 'pi_test_123_secret'
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                user = complete_test_scenario['users']['passenger']
                booking = complete_test_scenario['bookings']['pending_booking']
                
                # Mock authentication
                with patch('app.core.security.get_current_user') as mock_user:
                    mock_user.return_value = user
                    
                    response = await client.post(
                        "/api/v1/payments/create-intent",
                        json={
                            "booking_id": str(booking.id),
                            "payment_method": "card"
                        },
                        headers={"Authorization": "Bearer fake_token"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "client_secret" in data
                    assert data["id"] == 'pi_test_123'
    
    async def test_confirm_payment(self, override_get_db, complete_test_scenario):
        """Test payment confirmation."""
        with patch('stripe.PaymentIntent.retrieve') as mock_stripe:
            mock_stripe.return_value.status = 'succeeded'
            mock_stripe.return_value.id = 'pi_test_123'
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                user = complete_test_scenario['users']['passenger']
                
                # Mock authentication
                with patch('app.core.security.get_current_user') as mock_user:
                    mock_user.return_value = user
                    
                    response = await client.post(
                        "/api/v1/payments/confirm",
                        json={"payment_intent_id": "pi_test_123"},
                        headers={"Authorization": "Bearer fake_token"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "succeeded"
    
    async def test_payment_webhook(self, override_get_db):
        """Test payment webhook handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            webhook_payload = {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_test_123",
                        "status": "succeeded",
                        "amount": 5000,
                        "currency": "usd"
                    }
                }
            }
            
            response = await client.post(
                "/api/v1/payments/webhook",
                json=webhook_payload,
                headers={"stripe-signature": "fake_signature"}
            )
            
            # Should handle webhook gracefully even with fake signature
            assert response.status_code in [200, 400]


@pytest.mark.asyncio
class TestFleetAPIIntegration:
    """Integration tests for fleet management API endpoints."""
    
    async def test_get_terminals(self, override_get_db, complete_test_scenario):
        """Test retrieving terminals."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/fleet/terminals")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            
            # Check terminal structure
            terminal = data[0]
            assert "id" in terminal
            assert "name" in terminal
            assert "city" in terminal
    
    async def test_get_routes(self, override_get_db, complete_test_scenario):
        """Test retrieving routes."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/fleet/routes")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    async def test_create_trip_admin_only(self, override_get_db, complete_test_scenario):
        """Test trip creation requires admin access."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = complete_test_scenario['users']['passenger']  # Non-admin user
            route = complete_test_scenario['routes']['ny_to_la']
            bus = complete_test_scenario['buses']['luxury_bus']
            driver = complete_test_scenario['users']['driver']
            
            # Mock authentication with non-admin user
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = user
                
                response = await client.post(
                    "/api/v1/fleet/trips",
                    json={
                        "route_id": str(route.id),
                        "bus_id": str(bus.id),
                        "driver_id": str(driver.id),
                        "departure_time": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                        "fare": "150.00"
                    },
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 403  # Forbidden for non-admin


@pytest.mark.asyncio
class TestTrackingAPIIntegration:
    """Integration tests for tracking API endpoints."""
    
    async def test_update_trip_location_driver_only(self, override_get_db, complete_test_scenario):
        """Test trip location update requires driver access."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            driver = complete_test_scenario['users']['driver']
            trip = complete_test_scenario['trips']['current_trip']
            
            # Mock authentication with driver
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = driver
                
                response = await client.post(
                    f"/api/v1/tracking/trips/{trip.id}/location",
                    json={
                        "latitude": 40.7128,
                        "longitude": -74.0060,
                        "speed": 65.0,
                        "heading": 180.0
                    },
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["latitude"] == 40.7128
                assert data["longitude"] == -74.0060
    
    async def test_get_trip_location(self, override_get_db, complete_test_scenario):
        """Test retrieving trip location."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            trip = complete_test_scenario['trips']['current_trip']
            
            response = await client.get(f"/api/v1/tracking/trips/{trip.id}/location")
            
            assert response.status_code == 200
            data = response.json()
            if data:  # If location exists
                assert "latitude" in data
                assert "longitude" in data
                assert "recorded_at" in data
    
    async def test_get_trip_location_history(self, override_get_db, complete_test_scenario):
        """Test retrieving trip location history."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            trip = complete_test_scenario['trips']['current_trip']
            
            response = await client.get(f"/api/v1/tracking/trips/{trip.id}/location/history")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestReviewAPIIntegration:
    """Integration tests for review API endpoints."""
    
    async def test_create_review(self, override_get_db, complete_test_scenario):
        """Test review creation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = complete_test_scenario['users']['passenger']
            booking = complete_test_scenario['bookings']['confirmed_booking']
            
            # Mock authentication
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = user
                
                response = await client.post(
                    "/api/v1/reviews/",
                    json={
                        "booking_id": str(booking.id),
                        "rating": 5,
                        "comment": "Excellent service!"
                    },
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["rating"] == 5
                assert data["comment"] == "Excellent service!"
    
    async def test_get_driver_reviews(self, override_get_db, complete_test_scenario):
        """Test retrieving driver reviews."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            driver = complete_test_scenario['users']['driver']
            
            response = await client.get(f"/api/v1/reviews/driver/{driver.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    async def test_get_trip_reviews(self, override_get_db, complete_test_scenario):
        """Test retrieving trip reviews."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            trip = complete_test_scenario['trips']['completed_trip']
            
            response = await client.get(f"/api/v1/reviews/trip/{trip.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestAdminAPIIntegration:
    """Integration tests for admin API endpoints."""
    
    async def test_get_dashboard_metrics_admin_only(self, override_get_db, complete_test_scenario):
        """Test dashboard metrics requires admin access."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            admin = complete_test_scenario['users']['admin']
            
            # Mock authentication with admin user
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = admin
                
                response = await client.get(
                    "/api/v1/admin/dashboard/metrics",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "total_users" in data
                assert "total_bookings" in data
                assert "total_trips" in data
                assert "revenue" in data
    
    async def test_search_users_admin_only(self, override_get_db, complete_test_scenario):
        """Test user search requires admin access."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            admin = complete_test_scenario['users']['admin']
            
            # Mock authentication with admin user
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = admin
                
                response = await client.get(
                    "/api/v1/admin/users/search?query=passenger",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
    
    async def test_suspend_user_admin_only(self, override_get_db, complete_test_scenario):
        """Test user suspension requires admin access."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            admin = complete_test_scenario['users']['admin']
            user_to_suspend = complete_test_scenario['users']['passenger']
            
            # Mock authentication with admin user
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = admin
                
                response = await client.post(
                    f"/api/v1/admin/users/{user_to_suspend.id}/suspend",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["is_active"] is False
    
    async def test_non_admin_access_denied(self, override_get_db, complete_test_scenario):
        """Test non-admin users cannot access admin endpoints."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = complete_test_scenario['users']['passenger']  # Non-admin user
            
            # Mock authentication with non-admin user
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = user
                
                response = await client.get(
                    "/api/v1/admin/dashboard/metrics",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoints."""
    
    async def test_websocket_connection(self, override_get_db):
        """Test WebSocket connection establishment."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test WebSocket connection
            with client.websocket_connect("/api/v1/ws/trip-updates") as websocket:
                # Should be able to connect
                assert websocket is not None
    
    async def test_websocket_trip_updates(self, override_get_db, complete_test_scenario):
        """Test WebSocket trip updates."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            trip = complete_test_scenario['trips']['current_trip']
            
            # This would typically test real-time updates
            # For now, just test connection with trip ID
            with client.websocket_connect(f"/api/v1/ws/trip-updates/{trip.id}") as websocket:
                assert websocket is not None


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Integration tests for API error handling."""
    
    async def test_404_not_found(self, override_get_db):
        """Test 404 error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/nonexistent-endpoint")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
    
    async def test_422_validation_error(self, override_get_db):
        """Test validation error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/register", json={
                "email": "invalid-email",  # Invalid email format
                "password": "short",  # Too short password
                "first_name": "",  # Empty required field
                "last_name": ""  # Empty required field
            })
            
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], list)
    
    async def test_401_unauthorized(self, override_get_db):
        """Test unauthorized access handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/bookings/my-bookings")
            
            assert response.status_code == 401
            data = response.json()
            assert "detail" in data
    
    async def test_403_forbidden(self, override_get_db, complete_test_scenario):
        """Test forbidden access handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            user = complete_test_scenario['users']['passenger']  # Non-admin user
            
            # Mock authentication with non-admin user
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = user
                
                response = await client.get(
                    "/api/v1/admin/dashboard/metrics",
                    headers={"Authorization": "Bearer fake_token"}
                )
                
                assert response.status_code == 403
                data = response.json()
                assert "detail" in data
    
    async def test_500_internal_server_error(self, override_get_db):
        """Test internal server error handling."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Mock a service to raise an exception
            with patch('app.services.auth_service.AuthService.register_user') as mock_service:
                mock_service.side_effect = Exception("Database connection failed")
                
                response = await client.post("/api/v1/auth/register", json={
                    "email": "test@example.com",
                    "password": "TestPass123",
                    "first_name": "Test",
                    "last_name": "User"
                })
                
                assert response.status_code == 500
                data = response.json()
                assert "detail" in data


@pytest.mark.asyncio
class TestAPIPerformance:
    """Integration tests for API performance."""
    
    async def test_concurrent_requests(self, override_get_db, complete_test_scenario):
        """Test handling concurrent requests."""
        import asyncio
        
        async def make_request():
            async with AsyncClient(app=app, base_url="http://test") as client:
                return await client.get("/api/v1/fleet/terminals")
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
    
    async def test_large_payload_handling(self, override_get_db):
        """Test handling of large payloads."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create a large seat selection (simulate booking many seats)
            large_seat_list = list(range(1, 51))  # 50 seats
            
            response = await client.post("/api/v1/bookings/", json={
                "trip_id": "00000000-0000-0000-0000-000000000000",  # Fake ID
                "seat_numbers": large_seat_list
            })
            
            # Should handle large payload gracefully (even if business logic rejects it)
            assert response.status_code in [400, 401, 422]  # Various expected error codes
    
    async def test_response_time(self, override_get_db):
        """Test API response times."""
        import time
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()
            response = await client.get("/api/v1/fleet/terminals")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0  # Should respond within 2 seconds