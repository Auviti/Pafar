"""
End-to-end tests for critical user flows.
"""
import pytest
import asyncio
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
class TestCompleteBookingFlow:
    """End-to-end tests for complete booking flow."""
    
    async def test_complete_booking_journey_success(self, db_session, override_get_db):
        """Test complete user journey from registration to booking completion."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: User Registration
            registration_data = {
                "email": "passenger@example.com",
                "password": "TestPass123",
                "first_name": "John",
                "last_name": "Passenger",
                "phone": "+1234567890"
            }
            
            response = await client.post("/api/v1/auth/register", json=registration_data)
            assert response.status_code == status.HTTP_201_CREATED
            user_data = response.json()
            user_id = user_data["id"]
            
            # Step 2: Email Verification (simulate)
            user = await db_session.get(User, user_id)
            user.is_verified = True
            await db_session.commit()
            
            # Step 3: User Login
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": "passenger@example.com", "password": "TestPass123"}
            )
            assert login_response.status_code == status.HTTP_200_OK
            tokens = login_response.json()
            access_token = tokens["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Step 4: Create test data (terminals, routes, trips)
            scenario = TestDataBuilder.create_complete_booking_scenario()
            db_session.add_all([
                scenario['origin'], scenario['destination'], scenario['route'],
                scenario['bus'], scenario['driver'], scenario['trip']
            ])
            await db_session.commit()
            
            # Step 5: Search for trips
            search_response = await client.get(
                "/api/v1/fleet/trips/search",
                params={
                    "origin_terminal_id": str(scenario['origin'].id),
                    "destination_terminal_id": str(scenario['destination'].id),
                    "departure_date": scenario['trip'].departure_time.date().isoformat()
                }
            )
            assert search_response.status_code == status.HTTP_200_OK
            trips = search_response.json()
            assert len(trips) >= 1
            
            # Step 6: Create booking
            booking_response = await client.post(
                "/api/v1/bookings/",
                headers=headers,
                json={
                    "trip_id": str(scenario['trip'].id),
                    "seat_numbers": [1, 2]
                }
            )
            assert booking_response.status_code == status.HTTP_201_CREATED
            booking_data = booking_response.json()
            booking_id = booking_data["id"]
            
            # Step 7: Create payment intent
            payment_intent_response = await client.post(
                "/api/v1/payments/create-intent",
                headers=headers,
                json={
                    "booking_id": booking_id,
                    "payment_method": "card"
                }
            )
            assert payment_intent_response.status_code == status.HTTP_200_OK
            payment_intent = payment_intent_response.json()
            assert "client_secret" in payment_intent
            
            # Step 8: Confirm payment (simulate successful payment)
            payment_confirm_response = await client.post(
                "/api/v1/payments/confirm",
                headers=headers,
                json={
                    "payment_intent_id": payment_intent["payment_intent_id"],
                    "payment_method_id": "pm_card_visa"
                }
            )
            assert payment_confirm_response.status_code == status.HTTP_200_OK
            
            # Step 9: Verify booking is confirmed
            booking_check_response = await client.get(
                f"/api/v1/bookings/{booking_id}",
                headers=headers
            )
            assert booking_check_response.status_code == status.HTTP_200_OK
            final_booking = booking_check_response.json()
            assert final_booking["status"] == "confirmed"
            assert final_booking["payment_status"] == "completed"
            
            # Step 10: Get user's bookings
            user_bookings_response = await client.get(
                "/api/v1/bookings/my-bookings",
                headers=headers
            )
            assert user_bookings_response.status_code == status.HTTP_200_OK
            user_bookings = user_bookings_response.json()
            assert len(user_bookings) == 1
            assert user_bookings[0]["id"] == booking_id
    
    async def test_booking_flow_with_payment_failure(self, db_session, override_get_db):
        """Test booking flow when payment fails."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create and login user
            user = UserFactory.create(email="test@example.com", is_verified=True)
            db_session.add(user)
            await db_session.commit()
            
            access_token = create_access_token(data={"sub": str(user.id)})
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Create test scenario
            scenario = TestDataBuilder.create_complete_booking_scenario()
            db_session.add_all([
                scenario['origin'], scenario['destination'], scenario['route'],
                scenario['bus'], scenario['driver'], scenario['trip']
            ])
            await db_session.commit()
            
            # Create booking
            booking_response = await client.post(
                "/api/v1/bookings/",
                headers=headers,
                json={
                    "trip_id": str(scenario['trip'].id),
                    "seat_numbers": [1]
                }
            )
            assert booking_response.status_code == status.HTTP_201_CREATED
            booking_id = booking_response.json()["id"]
            
            # Create payment intent
            payment_intent_response = await client.post(
                "/api/v1/payments/create-intent",
                headers=headers,
                json={
                    "booking_id": booking_id,
                    "payment_method": "card"
                }
            )
            assert payment_intent_response.status_code == status.HTTP_200_OK
            
            # Simulate payment failure
            payment_confirm_response = await client.post(
                "/api/v1/payments/confirm",
                headers=headers,
                json={
                    "payment_intent_id": "pi_invalid",
                    "payment_method_id": "pm_card_chargeDeclined"
                }
            )
            assert payment_confirm_response.status_code == status.HTTP_400_BAD_REQUEST
            
            # Verify booking remains pending
            booking_check_response = await client.get(
                f"/api/v1/bookings/{booking_id}",
                headers=headers
            )
            assert booking_check_response.status_code == status.HTTP_200_OK
            booking_data = booking_check_response.json()
            assert booking_data["status"] == "pending"
            assert booking_data["payment_status"] == "failed"
    
    async def test_booking_cancellation_flow(self, db_session, override_get_db):
        """Test complete booking cancellation flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user and booking scenario
            user = UserFactory.create(email="test@example.com", is_verified=True)
            scenario = TestDataBuilder.create_complete_booking_scenario()
            scenario['passenger'] = user
            scenario['booking'].user_id = user.id
            
            db_session.add_all([
                user, scenario['origin'], scenario['destination'], scenario['route'],
                scenario['bus'], scenario['driver'], scenario['trip'], scenario['booking']
            ])
            await db_session.commit()
            
            access_token = create_access_token(data={"sub": str(user.id)})
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Cancel booking
            cancel_response = await client.post(
                f"/api/v1/bookings/{scenario['booking'].id}/cancel",
                headers=headers,
                json={"reason": "Change of plans"}
            )
            assert cancel_response.status_code == status.HTTP_200_OK
            
            # Verify booking is cancelled
            booking_check_response = await client.get(
                f"/api/v1/bookings/{scenario['booking'].id}",
                headers=headers
            )
            assert booking_check_response.status_code == status.HTTP_200_OK
            booking_data = booking_check_response.json()
            assert booking_data["status"] == "cancelled"


@pytest.mark.asyncio
class TestTripTrackingFlow:
    """End-to-end tests for trip tracking flow."""
    
    async def test_complete_trip_tracking_flow(self, db_session, override_get_db):
        """Test complete trip tracking from start to finish."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create scenario with driver and passenger
            scenario = TestDataBuilder.create_complete_booking_scenario()
            db_session.add_all([
                scenario['origin'], scenario['destination'], scenario['route'],
                scenario['bus'], scenario['driver'], scenario['trip'],
                scenario['passenger'], scenario['booking']
            ])
            await db_session.commit()
            
            # Driver login
            driver_token = create_access_token(data={"sub": str(scenario['driver'].id)})
            driver_headers = {"Authorization": f"Bearer {driver_token}"}
            
            # Passenger login
            passenger_token = create_access_token(data={"sub": str(scenario['passenger'].id)})
            passenger_headers = {"Authorization": f"Bearer {passenger_token}"}
            
            # Step 1: Driver starts trip
            start_trip_response = await client.post(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/start",
                headers=driver_headers
            )
            assert start_trip_response.status_code == status.HTTP_200_OK
            
            # Step 2: Driver updates location
            location_update_response = await client.post(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/location",
                headers=driver_headers,
                json={
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "speed": 45.5,
                    "heading": 180.0
                }
            )
            assert location_update_response.status_code == status.HTTP_200_OK
            
            # Step 3: Passenger gets trip location
            location_response = await client.get(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/location",
                headers=passenger_headers
            )
            assert location_response.status_code == status.HTTP_200_OK
            location_data = location_response.json()
            assert location_data["latitude"] == 40.7128
            assert location_data["longitude"] == -74.0060
            
            # Step 4: Driver updates trip status
            status_update_response = await client.post(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/status",
                headers=driver_headers,
                json={"status": "in_progress"}
            )
            assert status_update_response.status_code == status.HTTP_200_OK
            
            # Step 5: Passenger gets trip status
            trip_status_response = await client.get(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/status",
                headers=passenger_headers
            )
            assert trip_status_response.status_code == status.HTTP_200_OK
            status_data = trip_status_response.json()
            assert status_data["status"] == "in_progress"
            
            # Step 6: Driver completes trip
            complete_trip_response = await client.post(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/complete",
                headers=driver_headers
            )
            assert complete_trip_response.status_code == status.HTTP_200_OK
            
            # Step 7: Verify trip is completed
            final_status_response = await client.get(
                f"/api/v1/tracking/trips/{scenario['trip'].id}/status",
                headers=passenger_headers
            )
            assert final_status_response.status_code == status.HTTP_200_OK
            final_status = final_status_response.json()
            assert final_status["status"] == "completed"


@pytest.mark.asyncio
class TestAdminWorkflow:
    """End-to-end tests for admin workflows."""
    
    async def test_admin_user_management_flow(self, db_session, override_get_db):
        """Test complete admin user management workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create admin user
            admin = UserFactory.create_admin(email="admin@example.com")
            regular_user = UserFactory.create(email="user@example.com")
            db_session.add_all([admin, regular_user])
            await db_session.commit()
            
            admin_token = create_access_token(data={"sub": str(admin.id)})
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Step 1: Admin views dashboard
            dashboard_response = await client.get(
                "/api/v1/admin/dashboard",
                headers=admin_headers
            )
            assert dashboard_response.status_code == status.HTTP_200_OK
            dashboard_data = dashboard_response.json()
            assert "total_users" in dashboard_data
            
            # Step 2: Admin searches users
            users_response = await client.get(
                "/api/v1/admin/users",
                headers=admin_headers,
                params={"search": "user@example.com"}
            )
            assert users_response.status_code == status.HTTP_200_OK
            users_data = users_response.json()
            assert len(users_data) >= 1
            
            # Step 3: Admin suspends user
            suspend_response = await client.post(
                f"/api/v1/admin/users/{regular_user.id}/suspend",
                headers=admin_headers,
                json={"reason": "Policy violation"}
            )
            assert suspend_response.status_code == status.HTTP_200_OK
            
            # Step 4: Verify user is suspended
            user_check_response = await client.get(
                f"/api/v1/admin/users/{regular_user.id}",
                headers=admin_headers
            )
            assert user_check_response.status_code == status.HTTP_200_OK
            user_data = user_check_response.json()
            assert user_data["is_active"] is False
            
            # Step 5: Admin reactivates user
            reactivate_response = await client.post(
                f"/api/v1/admin/users/{regular_user.id}/activate",
                headers=admin_headers
            )
            assert reactivate_response.status_code == status.HTTP_200_OK
            
            # Step 6: Verify user is reactivated
            final_check_response = await client.get(
                f"/api/v1/admin/users/{regular_user.id}",
                headers=admin_headers
            )
            assert final_check_response.status_code == status.HTTP_200_OK
            final_user_data = final_check_response.json()
            assert final_user_data["is_active"] is True
    
    async def test_admin_fleet_management_flow(self, db_session, override_get_db):
        """Test admin fleet management workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create admin
            admin = UserFactory.create_admin()
            db_session.add(admin)
            await db_session.commit()
            
            admin_token = create_access_token(data={"sub": str(admin.id)})
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Step 1: Admin creates terminal
            terminal_response = await client.post(
                "/api/v1/admin/terminals",
                headers=admin_headers,
                json={
                    "name": "New Terminal",
                    "city": "Test City",
                    "address": "123 Test St",
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            )
            assert terminal_response.status_code == status.HTTP_201_CREATED
            terminal_data = terminal_response.json()
            terminal_id = terminal_data["id"]
            
            # Step 2: Admin creates bus
            bus_response = await client.post(
                "/api/v1/admin/buses",
                headers=admin_headers,
                json={
                    "license_plate": "TEST-123",
                    "model": "Test Bus",
                    "capacity": 50,
                    "amenities": {"wifi": True, "ac": True}
                }
            )
            assert bus_response.status_code == status.HTTP_201_CREATED
            bus_data = bus_response.json()
            bus_id = bus_data["id"]
            
            # Step 3: Admin creates route
            origin_terminal = TerminalFactory.create()
            destination_terminal = TerminalFactory.create()
            db_session.add_all([origin_terminal, destination_terminal])
            await db_session.commit()
            
            route_response = await client.post(
                "/api/v1/admin/routes",
                headers=admin_headers,
                json={
                    "origin_terminal_id": str(origin_terminal.id),
                    "destination_terminal_id": str(destination_terminal.id),
                    "distance_km": 100.0,
                    "estimated_duration_minutes": 120,
                    "base_fare": 25.0
                }
            )
            assert route_response.status_code == status.HTTP_201_CREATED
            route_data = route_response.json()
            route_id = route_data["id"]
            
            # Step 4: Admin creates trip
            driver = UserFactory.create_driver()
            db_session.add(driver)
            await db_session.commit()
            
            trip_response = await client.post(
                "/api/v1/admin/trips",
                headers=admin_headers,
                json={
                    "route_id": route_id,
                    "bus_id": bus_id,
                    "driver_id": str(driver.id),
                    "departure_time": "2024-12-01T10:00:00Z",
                    "fare": 30.0
                }
            )
            assert trip_response.status_code == status.HTTP_201_CREATED
            trip_data = trip_response.json()
            
            # Step 5: Admin views all trips
            trips_response = await client.get(
                "/api/v1/admin/trips",
                headers=admin_headers
            )
            assert trips_response.status_code == status.HTTP_200_OK
            trips_data = trips_response.json()
            assert len(trips_data) >= 1


@pytest.mark.asyncio
class TestErrorHandlingFlows:
    """End-to-end tests for error handling scenarios."""
    
    async def test_booking_with_insufficient_seats(self, db_session, override_get_db):
        """Test booking flow when insufficient seats are available."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create scenario with limited seats
            scenario = TestDataBuilder.create_complete_booking_scenario()
            scenario['trip'].available_seats = 1  # Only 1 seat available
            
            db_session.add_all([
                scenario['origin'], scenario['destination'], scenario['route'],
                scenario['bus'], scenario['driver'], scenario['trip'], scenario['passenger']
            ])
            await db_session.commit()
            
            access_token = create_access_token(data={"sub": str(scenario['passenger'].id)})
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Try to book 2 seats when only 1 is available
            booking_response = await client.post(
                "/api/v1/bookings/",
                headers=headers,
                json={
                    "trip_id": str(scenario['trip'].id),
                    "seat_numbers": [1, 2]
                }
            )
            assert booking_response.status_code == status.HTTP_400_BAD_REQUEST
            error_data = booking_response.json()
            assert "insufficient seats" in error_data["detail"].lower()
    
    async def test_unauthorized_access_flows(self, db_session, override_get_db):
        """Test various unauthorized access scenarios."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create test data
            user = UserFactory.create()
            admin = UserFactory.create_admin()
            scenario = TestDataBuilder.create_complete_booking_scenario()
            
            db_session.add_all([
                user, admin, scenario['origin'], scenario['destination'],
                scenario['route'], scenario['bus'], scenario['driver'], scenario['trip']
            ])
            await db_session.commit()
            
            user_token = create_access_token(data={"sub": str(user.id)})
            user_headers = {"Authorization": f"Bearer {user_token}"}
            
            # Test 1: Regular user trying to access admin endpoints
            admin_response = await client.get(
                "/api/v1/admin/dashboard",
                headers=user_headers
            )
            assert admin_response.status_code == status.HTTP_403_FORBIDDEN
            
            # Test 2: User trying to access another user's booking
            other_user = UserFactory.create(email="other@example.com")
            db_session.add(other_user)
            await db_session.commit()
            
            other_booking = scenario['booking']
            other_booking.user_id = other_user.id
            db_session.add(other_booking)
            await db_session.commit()
            
            booking_response = await client.get(
                f"/api/v1/bookings/{other_booking.id}",
                headers=user_headers
            )
            assert booking_response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test 3: Invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            invalid_response = await client.get(
                "/api/v1/auth/me",
                headers=invalid_headers
            )
            assert invalid_response.status_code == status.HTTP_401_UNAUTHORIZED