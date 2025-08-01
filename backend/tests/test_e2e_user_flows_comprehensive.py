"""
Comprehensive end-to-end tests for critical user flows.
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
class TestCompleteBookingFlow:
    """End-to-end test for complete booking flow."""
    
    async def test_complete_booking_journey_success(self, override_get_db, complete_test_scenario):
        """Test complete user journey from registration to booking completion."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: User Registration
            registration_data = {
                "email": "e2e_user@example.com",
                "password": "SecurePass123",
                "first_name": "E2E",
                "last_name": "User",
                "phone": "+1234567890"
            }
            
            register_response = await client.post("/api/v1/auth/register", json=registration_data)
            assert register_response.status_code == 201
            user_data = register_response.json()
            
            # Step 2: User Login
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "e2e_user@example.com",
                "password": "SecurePass123"
            })
            assert login_response.status_code == 200
            tokens = login_response.json()
            access_token = tokens["access_token"]
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Step 3: Search for trips
            route = complete_test_scenario['routes']['ny_to_la']
            search_response = await client.get(
                f"/api/v1/bookings/trips/search"
                f"?origin_terminal_id={route.origin_terminal_id}"
                f"&destination_terminal_id={route.destination_terminal_id}"
                f"&departure_date={(datetime.utcnow() + timedelta(days=1)).date()}"
            )
            assert search_response.status_code == 200
            trips = search_response.json()
            assert len(trips) > 0
            
            selected_trip = trips[0]
            
            # Step 4: Create booking
            booking_response = await client.post(
                "/api/v1/bookings/",
                json={
                    "trip_id": selected_trip["id"],
                    "seat_numbers": [1, 2]
                },
                headers=headers
            )
            assert booking_response.status_code == 201
            booking_data = booking_response.json()
            booking_id = booking_data["id"]
            
            # Step 5: Create payment intent
            with patch('stripe.PaymentIntent.create') as mock_stripe:
                mock_stripe.return_value.id = 'pi_test_123'
                mock_stripe.return_value.client_secret = 'pi_test_123_secret'
                
                payment_intent_response = await client.post(
                    "/api/v1/payments/create-intent",
                    json={
                        "booking_id": booking_id,
                        "payment_method": "card"
                    },
                    headers=headers
                )
                assert payment_intent_response.status_code == 200
                payment_intent = payment_intent_response.json()
                
            # Step 6: Confirm payment
            with patch('stripe.PaymentIntent.retrieve') as mock_stripe:
                mock_stripe.return_value.status = 'succeeded'
                mock_stripe.return_value.id = 'pi_test_123'
                
                payment_confirm_response = await client.post(
                    "/api/v1/payments/confirm",
                    json={"payment_intent_id": "pi_test_123"},
                    headers=headers
                )
                assert payment_confirm_response.status_code == 200
                
            # Step 7: Verify booking is confirmed
            booking_check_response = await client.get(
                f"/api/v1/bookings/{booking_id}",
                headers=headers
            )
            assert booking_check_response.status_code == 200
            final_booking = booking_check_response.json()
            assert final_booking["status"] == "confirmed"
            assert final_booking["payment_status"] == "completed"
            
            # Step 8: Get user's bookings
            user_bookings_response = await client.get(
                "/api/v1/bookings/my-bookings",
                headers=headers
            )
            assert user_bookings_response.status_code == 200
            user_bookings = user_bookings_response.json()
            assert len(user_bookings) == 1
            assert user_bookings[0]["id"] == booking_id
    
    async def test_booking_flow_with_payment_failure(self, override_get_db, complete_test_scenario):
        """Test booking flow when payment fails."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Register and login user
            await client.post("/api/v1/auth/register", json={
                "email": "payment_fail_user@example.com",
                "password": "SecurePass123",
                "first_name": "Payment",
                "last_name": "Fail"
            })
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "payment_fail_user@example.com",
                "password": "SecurePass123"
            })
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Create booking
            trip = complete_test_scenario['trips']['upcoming_trip']
            booking_response = await client.post(
                "/api/v1/bookings/",
                json={
                    "trip_id": str(trip.id),
                    "seat_numbers": [3]
                },
                headers=headers
            )
            booking_id = booking_response.json()["id"]
            
            # Create payment intent
            with patch('stripe.PaymentIntent.create') as mock_stripe:
                mock_stripe.return_value.id = 'pi_fail_123'
                mock_stripe.return_value.client_secret = 'pi_fail_123_secret'
                
                await client.post(
                    "/api/v1/payments/create-intent",
                    json={
                        "booking_id": booking_id,
                        "payment_method": "card"
                    },
                    headers=headers
                )
            
            # Simulate payment failure
            with patch('stripe.PaymentIntent.retrieve') as mock_stripe:
                mock_stripe.return_value.status = 'failed'
                mock_stripe.return_value.id = 'pi_fail_123'
                
                payment_confirm_response = await client.post(
                    "/api/v1/payments/confirm",
                    json={"payment_intent_id": "pi_fail_123"},
                    headers=headers
                )
                assert payment_confirm_response.status_code == 400
            
            # Verify booking status remains pending
            booking_check_response = await client.get(
                f"/api/v1/bookings/{booking_id}",
                headers=headers
            )
            final_booking = booking_check_response.json()
            assert final_booking["status"] == "pending"
            assert final_booking["payment_status"] == "failed"
    
    async def test_booking_cancellation_flow(self, override_get_db, complete_test_scenario):
        """Test complete booking cancellation flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Setup user and booking
            await client.post("/api/v1/auth/register", json={
                "email": "cancel_user@example.com",
                "password": "SecurePass123",
                "first_name": "Cancel",
                "last_name": "User"
            })
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "cancel_user@example.com",
                "password": "SecurePass123"
            })
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Create and confirm booking
            trip = complete_test_scenario['trips']['upcoming_trip']
            booking_response = await client.post(
                "/api/v1/bookings/",
                json={
                    "trip_id": str(trip.id),
                    "seat_numbers": [4]
                },
                headers=headers
            )
            booking_id = booking_response.json()["id"]
            
            # Simulate successful payment
            with patch('stripe.PaymentIntent.create') as mock_create, \
                 patch('stripe.PaymentIntent.retrieve') as mock_retrieve:
                
                mock_create.return_value.id = 'pi_cancel_123'
                mock_create.return_value.client_secret = 'pi_cancel_123_secret'
                mock_retrieve.return_value.status = 'succeeded'
                mock_retrieve.return_value.id = 'pi_cancel_123'
                
                await client.post(
                    "/api/v1/payments/create-intent",
                    json={"booking_id": booking_id, "payment_method": "card"},
                    headers=headers
                )
                
                await client.post(
                    "/api/v1/payments/confirm",
                    json={"payment_intent_id": "pi_cancel_123"},
                    headers=headers
                )
            
            # Cancel booking
            with patch('stripe.Refund.create') as mock_refund:
                mock_refund.return_value.id = 're_cancel_123'
                mock_refund.return_value.status = 'succeeded'
                
                cancel_response = await client.post(
                    f"/api/v1/bookings/{booking_id}/cancel",
                    headers=headers
                )
                assert cancel_response.status_code == 200
                cancelled_booking = cancel_response.json()
                assert cancelled_booking["status"] == "cancelled"
                
            # Verify refund was processed
            booking_check_response = await client.get(
                f"/api/v1/bookings/{booking_id}",
                headers=headers
            )
            final_booking = booking_check_response.json()
            assert final_booking["payment_status"] == "refunded"


@pytest.mark.asyncio
class TestDriverTripManagementFlow:
    """End-to-end test for driver trip management flow."""
    
    async def test_driver_trip_lifecycle(self, override_get_db, complete_test_scenario):
        """Test complete driver trip management lifecycle."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            driver = complete_test_scenario['users']['driver']
            trip = complete_test_scenario['trips']['current_trip']
            
            # Mock driver authentication
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = driver
                headers = {"Authorization": "Bearer fake_driver_token"}
                
                # Step 1: Driver starts trip
                start_response = await client.post(
                    f"/api/v1/fleet/trips/{trip.id}/start",
                    headers=headers
                )
                assert start_response.status_code == 200
                
                # Step 2: Driver updates location multiple times
                locations = [
                    {"latitude": 40.7128, "longitude": -74.0060, "speed": 0.0, "heading": 0.0},
                    {"latitude": 40.7500, "longitude": -74.0200, "speed": 65.0, "heading": 315.0},
                    {"latitude": 40.8000, "longitude": -74.0400, "speed": 70.0, "heading": 320.0},
                ]
                
                for location in locations:
                    location_response = await client.post(
                        f"/api/v1/tracking/trips/{trip.id}/location",
                        json=location,
                        headers=headers
                    )
                    assert location_response.status_code == 200
                
                # Step 3: Get trip location history
                history_response = await client.get(
                    f"/api/v1/tracking/trips/{trip.id}/location/history",
                    headers=headers
                )
                assert history_response.status_code == 200
                location_history = history_response.json()
                assert len(location_history) >= 3
                
                # Step 4: Driver completes trip
                complete_response = await client.post(
                    f"/api/v1/fleet/trips/{trip.id}/complete",
                    headers=headers
                )
                assert complete_response.status_code == 200
                completed_trip = complete_response.json()
                assert completed_trip["status"] == "completed"
    
    async def test_driver_emergency_flow(self, override_get_db, complete_test_scenario):
        """Test driver emergency reporting flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            driver = complete_test_scenario['users']['driver']
            trip = complete_test_scenario['trips']['current_trip']
            
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = driver
                headers = {"Authorization": "Bearer fake_driver_token"}
                
                # Report emergency
                emergency_response = await client.post(
                    f"/api/v1/tracking/trips/{trip.id}/emergency",
                    json={
                        "type": "breakdown",
                        "description": "Engine failure",
                        "location": {
                            "latitude": 40.7500,
                            "longitude": -74.0200
                        }
                    },
                    headers=headers
                )
                assert emergency_response.status_code == 200
                
                # Verify trip status is updated
                trip_response = await client.get(
                    f"/api/v1/fleet/trips/{trip.id}",
                    headers=headers
                )
                trip_data = trip_response.json()
                assert trip_data["status"] == "emergency"


@pytest.mark.asyncio
class TestAdminManagementFlow:
    """End-to-end test for admin management flow."""
    
    async def test_admin_user_management_flow(self, override_get_db, complete_test_scenario):
        """Test complete admin user management flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            admin = complete_test_scenario['users']['admin']
            passenger = complete_test_scenario['users']['passenger']
            
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = admin
                headers = {"Authorization": "Bearer fake_admin_token"}
                
                # Step 1: Get dashboard metrics
                metrics_response = await client.get(
                    "/api/v1/admin/dashboard/metrics",
                    headers=headers
                )
                assert metrics_response.status_code == 200
                metrics = metrics_response.json()
                assert "total_users" in metrics
                assert "total_bookings" in metrics
                
                # Step 2: Search for users
                search_response = await client.get(
                    "/api/v1/admin/users/search?query=passenger",
                    headers=headers
                )
                assert search_response.status_code == 200
                users = search_response.json()
                assert len(users) > 0
                
                # Step 3: Suspend user
                suspend_response = await client.post(
                    f"/api/v1/admin/users/{passenger.id}/suspend",
                    headers=headers
                )
                assert suspend_response.status_code == 200
                suspended_user = suspend_response.json()
                assert suspended_user["is_active"] is False
                
                # Step 4: Reactivate user
                activate_response = await client.post(
                    f"/api/v1/admin/users/{passenger.id}/activate",
                    headers=headers
                )
                assert activate_response.status_code == 200
                activated_user = activate_response.json()
                assert activated_user["is_active"] is True
    
    async def test_admin_fleet_management_flow(self, override_get_db, complete_test_scenario):
        """Test admin fleet management flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            admin = complete_test_scenario['users']['admin']
            route = complete_test_scenario['routes']['ny_to_la']
            bus = complete_test_scenario['buses']['luxury_bus']
            driver = complete_test_scenario['users']['driver']
            
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = admin
                headers = {"Authorization": "Bearer fake_admin_token"}
                
                # Step 1: Create new trip
                trip_data = {
                    "route_id": str(route.id),
                    "bus_id": str(bus.id),
                    "driver_id": str(driver.id),
                    "departure_time": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
                    "fare": "175.00"
                }
                
                create_trip_response = await client.post(
                    "/api/v1/fleet/trips",
                    json=trip_data,
                    headers=headers
                )
                assert create_trip_response.status_code == 201
                new_trip = create_trip_response.json()
                trip_id = new_trip["id"]
                
                # Step 2: Update trip details
                update_response = await client.put(
                    f"/api/v1/fleet/trips/{trip_id}",
                    json={"fare": "180.00"},
                    headers=headers
                )
                assert update_response.status_code == 200
                updated_trip = update_response.json()
                assert float(updated_trip["fare"]) == 180.00
                
                # Step 3: Cancel trip
                cancel_response = await client.post(
                    f"/api/v1/fleet/trips/{trip_id}/cancel",
                    headers=headers
                )
                assert cancel_response.status_code == 200
                cancelled_trip = cancel_response.json()
                assert cancelled_trip["status"] == "cancelled"


@pytest.mark.asyncio
class TestReviewAndRatingFlow:
    """End-to-end test for review and rating flow."""
    
    async def test_complete_review_flow(self, override_get_db, complete_test_scenario):
        """Test complete review and rating flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Setup completed booking
            passenger = complete_test_scenario['users']['passenger']
            booking = complete_test_scenario['bookings']['confirmed_booking']
            driver = complete_test_scenario['users']['driver']
            
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = passenger
                headers = {"Authorization": "Bearer fake_passenger_token"}
                
                # Step 1: Submit review
                review_data = {
                    "booking_id": str(booking.id),
                    "rating": 5,
                    "comment": "Excellent service! Driver was very professional and the bus was comfortable."
                }
                
                review_response = await client.post(
                    "/api/v1/reviews/",
                    json=review_data,
                    headers=headers
                )
                assert review_response.status_code == 201
                review = review_response.json()
                review_id = review["id"]
                
                # Step 2: Get driver reviews
                driver_reviews_response = await client.get(
                    f"/api/v1/reviews/driver/{driver.id}"
                )
                assert driver_reviews_response.status_code == 200
                driver_reviews = driver_reviews_response.json()
                assert len(driver_reviews) > 0
                
                # Step 3: Get trip reviews
                trip_reviews_response = await client.get(
                    f"/api/v1/reviews/trip/{booking.trip_id}"
                )
                assert trip_reviews_response.status_code == 200
                trip_reviews = trip_reviews_response.json()
                assert len(trip_reviews) > 0
                
                # Step 4: Update review
                update_review_response = await client.put(
                    f"/api/v1/reviews/{review_id}",
                    json={
                        "rating": 4,
                        "comment": "Good service, but could be improved."
                    },
                    headers=headers
                )
                assert update_review_response.status_code == 200
                updated_review = update_review_response.json()
                assert updated_review["rating"] == 4
    
    async def test_admin_review_moderation_flow(self, override_get_db, complete_test_scenario):
        """Test admin review moderation flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            admin = complete_test_scenario['users']['admin']
            passenger = complete_test_scenario['users']['passenger']
            booking = complete_test_scenario['bookings']['confirmed_booking']
            
            # First, create a review as passenger
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = passenger
                passenger_headers = {"Authorization": "Bearer fake_passenger_token"}
                
                review_response = await client.post(
                    "/api/v1/reviews/",
                    json={
                        "booking_id": str(booking.id),
                        "rating": 1,
                        "comment": "This is inappropriate content that should be moderated."
                    },
                    headers=passenger_headers
                )
                review_id = review_response.json()["id"]
            
            # Now moderate as admin
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = admin
                admin_headers = {"Authorization": "Bearer fake_admin_token"}
                
                # Step 1: Get pending reviews for moderation
                pending_reviews_response = await client.get(
                    "/api/v1/admin/reviews/pending",
                    headers=admin_headers
                )
                assert pending_reviews_response.status_code == 200
                pending_reviews = pending_reviews_response.json()
                assert len(pending_reviews) > 0
                
                # Step 2: Moderate review (hide inappropriate content)
                moderate_response = await client.post(
                    f"/api/v1/admin/reviews/{review_id}/moderate",
                    json={
                        "action": "hide",
                        "reason": "Inappropriate content"
                    },
                    headers=admin_headers
                )
                assert moderate_response.status_code == 200
                
                # Step 3: Verify review is hidden
                review_check_response = await client.get(
                    f"/api/v1/reviews/{review_id}",
                    headers=admin_headers
                )
                assert review_check_response.status_code == 200
                moderated_review = review_check_response.json()
                assert moderated_review["is_hidden"] is True


@pytest.mark.asyncio
class TestRealTimeTrackingFlow:
    """End-to-end test for real-time tracking flow."""
    
    async def test_real_time_tracking_flow(self, override_get_db, complete_test_scenario):
        """Test real-time tracking flow with WebSocket connections."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            passenger = complete_test_scenario['users']['passenger']
            driver = complete_test_scenario['users']['driver']
            trip = complete_test_scenario['trips']['current_trip']
            
            # Test WebSocket connection for trip updates
            with client.websocket_connect(f"/api/v1/ws/trip-updates/{trip.id}") as websocket:
                # Simulate driver updating location
                with patch('app.core.security.get_current_user') as mock_user:
                    mock_user.return_value = driver
                    headers = {"Authorization": "Bearer fake_driver_token"}
                    
                    # Update location
                    location_response = await client.post(
                        f"/api/v1/tracking/trips/{trip.id}/location",
                        json={
                            "latitude": 40.7500,
                            "longitude": -74.0200,
                            "speed": 65.0,
                            "heading": 315.0
                        },
                        headers=headers
                    )
                    assert location_response.status_code == 200
                
                # Verify WebSocket receives update
                update_message = websocket.receive_json()
                assert update_message["type"] == "location_update"
                assert update_message["data"]["latitude"] == 40.7500
                assert update_message["data"]["longitude"] == -74.0200
    
    async def test_trip_status_notifications_flow(self, override_get_db, complete_test_scenario):
        """Test trip status notification flow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            driver = complete_test_scenario['users']['driver']
            trip = complete_test_scenario['trips']['upcoming_trip']
            
            with patch('app.core.security.get_current_user') as mock_user:
                mock_user.return_value = driver
                headers = {"Authorization": "Bearer fake_driver_token"}
                
                # Test WebSocket connection for status updates
                with client.websocket_connect(f"/api/v1/ws/trip-updates/{trip.id}") as websocket:
                    # Start trip
                    start_response = await client.post(
                        f"/api/v1/fleet/trips/{trip.id}/start",
                        headers=headers
                    )
                    assert start_response.status_code == 200
                    
                    # Verify status update notification
                    status_message = websocket.receive_json()
                    assert status_message["type"] == "status_update"
                    assert status_message["data"]["status"] == "in_progress"
                    
                    # Update trip to approaching terminal
                    approach_response = await client.post(
                        f"/api/v1/fleet/trips/{trip.id}/approaching",
                        json={"terminal_id": str(trip.route.destination_terminal_id)},
                        headers=headers
                    )
                    assert approach_response.status_code == 200
                    
                    # Verify approaching notification
                    approach_message = websocket.receive_json()
                    assert approach_message["type"] == "approaching_terminal"
                    
                    # Complete trip
                    complete_response = await client.post(
                        f"/api/v1/fleet/trips/{trip.id}/complete",
                        headers=headers
                    )
                    assert complete_response.status_code == 200
                    
                    # Verify completion notification
                    complete_message = websocket.receive_json()
                    assert complete_message["type"] == "trip_completed"


@pytest.mark.asyncio
class TestErrorRecoveryFlows:
    """End-to-end tests for error recovery scenarios."""
    
    async def test_payment_retry_flow(self, override_get_db, complete_test_scenario):
        """Test payment retry flow after initial failure."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Setup user and booking
            await client.post("/api/v1/auth/register", json={
                "email": "retry_user@example.com",
                "password": "SecurePass123",
                "first_name": "Retry",
                "last_name": "User"
            })
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "retry_user@example.com",
                "password": "SecurePass123"
            })
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            trip = complete_test_scenario['trips']['upcoming_trip']
            booking_response = await client.post(
                "/api/v1/bookings/",
                json={
                    "trip_id": str(trip.id),
                    "seat_numbers": [5]
                },
                headers=headers
            )
            booking_id = booking_response.json()["id"]
            
            # First payment attempt fails
            with patch('stripe.PaymentIntent.create') as mock_create, \
                 patch('stripe.PaymentIntent.retrieve') as mock_retrieve:
                
                mock_create.return_value.id = 'pi_retry_123'
                mock_create.return_value.client_secret = 'pi_retry_123_secret'
                mock_retrieve.return_value.status = 'failed'
                mock_retrieve.return_value.id = 'pi_retry_123'
                
                # Create payment intent
                await client.post(
                    "/api/v1/payments/create-intent",
                    json={"booking_id": booking_id, "payment_method": "card"},
                    headers=headers
                )
                
                # First payment attempt fails
                payment_response = await client.post(
                    "/api/v1/payments/confirm",
                    json={"payment_intent_id": "pi_retry_123"},
                    headers=headers
                )
                assert payment_response.status_code == 400
            
            # Retry payment with new payment method
            with patch('stripe.PaymentIntent.create') as mock_create, \
                 patch('stripe.PaymentIntent.retrieve') as mock_retrieve:
                
                mock_create.return_value.id = 'pi_retry_456'
                mock_create.return_value.client_secret = 'pi_retry_456_secret'
                mock_retrieve.return_value.status = 'succeeded'
                mock_retrieve.return_value.id = 'pi_retry_456'
                
                # Create new payment intent
                retry_intent_response = await client.post(
                    "/api/v1/payments/create-intent",
                    json={"booking_id": booking_id, "payment_method": "card"},
                    headers=headers
                )
                assert retry_intent_response.status_code == 200
                
                # Retry payment succeeds
                retry_payment_response = await client.post(
                    "/api/v1/payments/confirm",
                    json={"payment_intent_id": "pi_retry_456"},
                    headers=headers
                )
                assert retry_payment_response.status_code == 200
            
            # Verify booking is now confirmed
            final_booking_response = await client.get(
                f"/api/v1/bookings/{booking_id}",
                headers=headers
            )
            final_booking = final_booking_response.json()
            assert final_booking["status"] == "confirmed"
            assert final_booking["payment_status"] == "completed"
    
    async def test_network_interruption_recovery(self, override_get_db, complete_test_scenario):
        """Test recovery from network interruptions during booking."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Setup user
            await client.post("/api/v1/auth/register", json={
                "email": "network_user@example.com",
                "password": "SecurePass123",
                "first_name": "Network",
                "last_name": "User"
            })
            
            login_response = await client.post("/api/v1/auth/login", json={
                "email": "network_user@example.com",
                "password": "SecurePass123"
            })
            access_token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            trip = complete_test_scenario['trips']['upcoming_trip']
            
            # Simulate network interruption during booking creation
            with patch('app.services.booking_service.BookingService.create_booking') as mock_booking:
                mock_booking.side_effect = Exception("Network timeout")
                
                booking_response = await client.post(
                    "/api/v1/bookings/",
                    json={
                        "trip_id": str(trip.id),
                        "seat_numbers": [6]
                    },
                    headers=headers
                )
                assert booking_response.status_code == 500
            
            # Retry booking after network recovery
            booking_retry_response = await client.post(
                "/api/v1/bookings/",
                json={
                    "trip_id": str(trip.id),
                    "seat_numbers": [6]
                },
                headers=headers
            )
            assert booking_retry_response.status_code == 201
            
            # Verify booking was created successfully
            booking_data = booking_retry_response.json()
            assert booking_data["seat_numbers"] == [6]
            assert booking_data["status"] == "pending"


@pytest.mark.asyncio
class TestConcurrentUserFlows:
    """End-to-end tests for concurrent user scenarios."""
    
    async def test_concurrent_seat_booking(self, override_get_db, complete_test_scenario):
        """Test concurrent users trying to book the same seats."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            trip = complete_test_scenario['trips']['upcoming_trip']
            
            # Create two users
            users = []
            for i in range(2):
                await client.post("/api/v1/auth/register", json={
                    "email": f"concurrent_user_{i}@example.com",
                    "password": "SecurePass123",
                    "first_name": f"User{i}",
                    "last_name": "Concurrent"
                })
                
                login_response = await client.post("/api/v1/auth/login", json={
                    "email": f"concurrent_user_{i}@example.com",
                    "password": "SecurePass123"
                })
                access_token = login_response.json()["access_token"]
                users.append({"Authorization": f"Bearer {access_token}"})
            
            # Both users try to book the same seat simultaneously
            import asyncio
            
            async def book_seat(headers, seat_number):
                return await client.post(
                    "/api/v1/bookings/",
                    json={
                        "trip_id": str(trip.id),
                        "seat_numbers": [seat_number]
                    },
                    headers=headers
                )
            
            # Execute concurrent booking requests
            results = await asyncio.gather(
                book_seat(users[0], 7),
                book_seat(users[1], 7),
                return_exceptions=True
            )
            
            # One should succeed, one should fail
            success_count = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 201)
            failure_count = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 409)
            
            assert success_count == 1
            assert failure_count == 1
    
    async def test_high_load_booking_scenario(self, override_get_db, complete_test_scenario):
        """Test system behavior under high booking load."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            trip = complete_test_scenario['trips']['upcoming_trip']
            
            # Create multiple users
            users = []
            for i in range(10):
                await client.post("/api/v1/auth/register", json={
                    "email": f"load_user_{i}@example.com",
                    "password": "SecurePass123",
                    "first_name": f"Load{i}",
                    "last_name": "Test"
                })
                
                login_response = await client.post("/api/v1/auth/login", json={
                    "email": f"load_user_{i}@example.com",
                    "password": "SecurePass123"
                })
                access_token = login_response.json()["access_token"]
                users.append({"Authorization": f"Bearer {access_token}"})
            
            # All users try to book different seats simultaneously
            import asyncio
            
            async def book_seat(headers, seat_number):
                try:
                    response = await client.post(
                        "/api/v1/bookings/",
                        json={
                            "trip_id": str(trip.id),
                            "seat_numbers": [seat_number]
                        },
                        headers=headers
                    )
                    return response.status_code
                except Exception as e:
                    return str(e)
            
            # Execute concurrent booking requests
            tasks = [book_seat(users[i], i + 10) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Most bookings should succeed (assuming enough seats available)
            success_count = sum(1 for r in results if r == 201)
            assert success_count >= 8  # Allow for some failures due to load