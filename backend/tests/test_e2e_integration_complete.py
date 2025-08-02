"""
Complete End-to-End Integration Tests for Pafar Transport Management System
Tests all platforms and real-time features with concurrent users
"""
import pytest
import asyncio
import uuid
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import AsyncClient
from fastapi import status
from unittest.mock import patch, AsyncMock
import websockets
import concurrent.futures
from typing import List, Dict, Any

from app.main import app
from backend.tests.factories import TestDataBuilder


@pytest.mark.e2e
class TestCompleteSystemIntegration:
    """Complete system integration tests across all platforms."""
    
    @pytest.mark.asyncio
    async def test_complete_booking_flow_integration(self, override_get_db):
        """Test complete booking flow from registration to payment confirmation."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: User Registration
            user_data = {
                "email": "e2e_user@example.com",
                "password": "SecurePass123!",
                "first_name": "E2E",
                "last_name": "TestUser",
                "phone": "+1234567890"
            }
            
            register_response = await client.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == status.HTTP_201_CREATED
            user_id = register_response.json()["id"]
            
            # Step 2: User Login
            login_response = await client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            assert login_response.status_code == status.HTTP_200_OK
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Step 3: Create test data
            scenario = TestDataBuilder.create_complete_booking_scenario()
            
            # Step 4: Search for trips
            search_params = {
                "origin_terminal_id": str(scenario['origin_terminal'].id),
                "destination_terminal_id": str(scenario['destination_terminal'].id),
                "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
            }
            
            search_response = await client.get("/api/v1/bookings/trips/search", params=search_params)
            assert search_response.status_code == status.HTTP_200_OK
            trips = search_response.json()
            assert len(trips) > 0
            
            selected_trip = trips[0]
            
            # Step 5: Create booking with seat selection
            booking_data = {
                "trip_id": selected_trip["id"],
                "seat_numbers": [1, 2],
                "passenger_details": {
                    "first_name": "E2E",
                    "last_name": "TestUser",
                    "phone": "+1234567890"
                }
            }
            
            booking_response = await client.post("/api/v1/bookings/", json=booking_data)
            assert booking_response.status_code == status.HTTP_201_CREATED
            booking = booking_response.json()
            assert booking["status"] == "pending"
            assert booking["seat_numbers"] == [1, 2]
            
            # Step 6: Create payment intent
            payment_intent_response = await client.post("/api/v1/payments/create-intent", json={
                "booking_id": booking["id"],
                "payment_method": "card"
            })
            assert payment_intent_response.status_code == status.HTTP_200_OK
            payment_intent = payment_intent_response.json()
            
            # Step 7: Confirm payment
            payment_confirm_response = await client.post("/api/v1/payments/confirm", json={
                "payment_intent_id": payment_intent["payment_intent_id"],
                "booking_id": booking["id"]
            })
            assert payment_confirm_response.status_code == status.HTTP_200_OK
            payment = payment_confirm_response.json()
            assert payment["status"] == "completed"
            
            # Step 8: Verify booking is confirmed
            booking_details_response = await client.get(f"/api/v1/bookings/{booking['id']}")
            assert booking_details_response.status_code == status.HTTP_200_OK
            updated_booking = booking_details_response.json()
            assert updated_booking["status"] == "confirmed"
            assert updated_booking["payment_status"] == "completed"
            
            # Step 9: Download receipt
            receipt_response = await client.get(f"/api/v1/payments/{payment['id']}/receipt")
            assert receipt_response.status_code == status.HTTP_200_OK
            assert receipt_response.headers["content-type"] == "application/pdf"
            
            return {
                "user_id": user_id,
                "booking": updated_booking,
                "payment": payment,
                "tokens": tokens
            }

    @pytest.mark.asyncio
    async def test_concurrent_booking_attempts(self, override_get_db):
        """Test system behavior with multiple concurrent booking attempts."""
        scenario = TestDataBuilder.create_complete_booking_scenario()
        trip_id = str(scenario['trip'].id)
        
        # Create multiple users
        users = []
        for i in range(5):
            async with AsyncClient(app=app, base_url="http://test") as client:
                user_data = {
                    "email": f"concurrent_user_{i}@example.com",
                    "password": "SecurePass123!",
                    "first_name": f"User{i}",
                    "last_name": "Concurrent"
                }
                
                register_response = await client.post("/api/v1/auth/register", json=user_data)
                assert register_response.status_code == status.HTTP_201_CREATED
                
                login_response = await client.post("/api/v1/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                tokens = login_response.json()
                users.append({
                    "client": client,
                    "tokens": tokens,
                    "user_data": user_data
                })
        
        # All users attempt to book the same seats simultaneously
        async def attempt_booking(user_info):
            client = user_info["client"]
            client.headers.update({"Authorization": f"Bearer {user_info['tokens']['access_token']}"})
            
            booking_data = {
                "trip_id": trip_id,
                "seat_numbers": [1, 2],  # Same seats for all users
                "passenger_details": {
                    "first_name": user_info["user_data"]["first_name"],
                    "last_name": user_info["user_data"]["last_name"]
                }
            }
            
            try:
                response = await client.post("/api/v1/bookings/", json=booking_data)
                return {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code < 500 else None,
                    "user": user_info["user_data"]["email"]
                }
            except Exception as e:
                return {
                    "status_code": 500,
                    "error": str(e),
                    "user": user_info["user_data"]["email"]
                }
        
        # Execute concurrent booking attempts
        results = await asyncio.gather(*[attempt_booking(user) for user in users])
        
        # Verify only one booking succeeded
        successful_bookings = [r for r in results if r["status_code"] == status.HTTP_201_CREATED]
        failed_bookings = [r for r in results if r["status_code"] != status.HTTP_201_CREATED]
        
        assert len(successful_bookings) == 1, f"Expected 1 successful booking, got {len(successful_bookings)}"
        assert len(failed_bookings) == 4, f"Expected 4 failed bookings, got {len(failed_bookings)}"
        
        # Verify failed bookings have appropriate error messages
        for failed in failed_bookings:
            assert failed["status_code"] in [status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST]

    @pytest.mark.asyncio
    async def test_real_time_tracking_integration(self, override_get_db):
        """Test real-time tracking features with WebSocket connections."""
        scenario = TestDataBuilder.create_trip_with_tracking()
        trip_id = str(scenario['trip'].id)
        
        # Create passenger and driver clients
        async with AsyncClient(app=app, base_url="http://test") as passenger_client, \
                   AsyncClient(app=app, base_url="http://test") as driver_client:
            
            # Register passenger
            passenger_data = {
                "email": "passenger@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "Passenger"
            }
            await passenger_client.post("/api/v1/auth/register", json=passenger_data)
            passenger_login = await passenger_client.post("/api/v1/auth/login", json={
                "email": passenger_data["email"],
                "password": passenger_data["password"]
            })
            passenger_tokens = passenger_login.json()
            passenger_client.headers.update({"Authorization": f"Bearer {passenger_tokens['access_token']}"})
            
            # Register driver
            driver_data = {
                "email": "driver@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
                "last_name": "Driver",
                "role": "driver"
            }
            await driver_client.post("/api/v1/auth/register", json=driver_data)
            driver_login = await driver_client.post("/api/v1/auth/login", json={
                "email": driver_data["email"],
                "password": driver_data["password"]
            })
            driver_tokens = driver_login.json()
            driver_client.headers.update({"Authorization": f"Bearer {driver_tokens['access_token']}"})
            
            # Create booking for passenger
            booking_data = {
                "trip_id": trip_id,
                "seat_numbers": [1],
                "passenger_details": passenger_data
            }
            booking_response = await passenger_client.post("/api/v1/bookings/", json=booking_data)
            booking = booking_response.json()
            
            # Simulate driver location updates
            locations = [
                {"latitude": 40.7128, "longitude": -74.0060, "speed": 60.0, "heading": 90.0},
                {"latitude": 40.7130, "longitude": -74.0058, "speed": 65.0, "heading": 95.0},
                {"latitude": 40.7132, "longitude": -74.0056, "speed": 70.0, "heading": 100.0}
            ]
            
            for location in locations:
                location_response = await driver_client.post(
                    f"/api/v1/tracking/trips/{trip_id}/location",
                    json=location
                )
                assert location_response.status_code == status.HTTP_200_OK
                
                # Verify passenger can get updated location
                passenger_location_response = await passenger_client.get(
                    f"/api/v1/tracking/trips/{trip_id}/location"
                )
                assert passenger_location_response.status_code == status.HTTP_200_OK
                location_data = passenger_location_response.json()
                assert location_data["latitude"] == location["latitude"]
                assert location_data["longitude"] == location["longitude"]
                
                # Small delay to simulate real-time updates
                await asyncio.sleep(0.1)
            
            # Test ETA calculation
            eta_response = await passenger_client.get(f"/api/v1/tracking/trips/{trip_id}/eta")
            assert eta_response.status_code == status.HTTP_200_OK
            eta_data = eta_response.json()
            assert "estimated_arrival" in eta_data
            assert "distance_remaining_km" in eta_data

    @pytest.mark.asyncio
    async def test_payment_processing_with_failures_and_retries(self, override_get_db):
        """Test payment processing with various failure scenarios and retry logic."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Setup user and booking
            user_data = {
                "email": "payment_test@example.com",
                "password": "SecurePass123!",
                "first_name": "Payment",
                "last_name": "TestUser"
            }
            
            await client.post("/api/v1/auth/register", json=user_data)
            login_response = await client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            scenario = TestDataBuilder.create_complete_booking_scenario()
            booking_data = {
                "trip_id": str(scenario['trip'].id),
                "seat_numbers": [1],
                "passenger_details": user_data
            }
            
            booking_response = await client.post("/api/v1/bookings/", json=booking_data)
            booking = booking_response.json()
            
            # Test 1: Payment with insufficient funds
            with patch('app.services.payment_service.stripe.PaymentIntent.create') as mock_create:
                mock_create.side_effect = Exception("insufficient_funds")
                
                payment_intent_response = await client.post("/api/v1/payments/create-intent", json={
                    "booking_id": booking["id"],
                    "payment_method": "card"
                })
                
                # Should handle error gracefully
                assert payment_intent_response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
            
            # Test 2: Successful payment after retry
            with patch('app.services.payment_service.stripe.PaymentIntent.create') as mock_create, \
                 patch('app.services.payment_service.stripe.PaymentIntent.confirm') as mock_confirm:
                
                mock_create.return_value = type('MockPaymentIntent', (), {
                    'id': 'pi_test_123',
                    'client_secret': 'pi_test_123_secret',
                    'status': 'requires_confirmation'
                })()
                
                mock_confirm.return_value = type('MockPaymentIntent', (), {
                    'id': 'pi_test_123',
                    'status': 'succeeded'
                })()
                
                # Create payment intent
                payment_intent_response = await client.post("/api/v1/payments/create-intent", json={
                    "booking_id": booking["id"],
                    "payment_method": "card"
                })
                assert payment_intent_response.status_code == status.HTTP_200_OK
                payment_intent = payment_intent_response.json()
                
                # Confirm payment
                payment_confirm_response = await client.post("/api/v1/payments/confirm", json={
                    "payment_intent_id": payment_intent["payment_intent_id"],
                    "booking_id": booking["id"]
                })
                assert payment_confirm_response.status_code == status.HTTP_200_OK
                payment = payment_confirm_response.json()
                assert payment["status"] == "completed"
            
            # Test 3: Webhook handling for payment status updates
            webhook_data = {
                "type": "payment_intent.succeeded",
                "data": {
                    "object": {
                        "id": "pi_test_123",
                        "status": "succeeded",
                        "metadata": {
                            "booking_id": booking["id"]
                        }
                    }
                }
            }
            
            webhook_response = await client.post("/api/v1/payments/webhook", json=webhook_data)
            assert webhook_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_admin_system_integration(self, override_get_db):
        """Test complete admin system functionality."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create admin user
            admin_data = {
                "email": "admin@example.com",
                "password": "AdminPass123!",
                "first_name": "System",
                "last_name": "Admin",
                "role": "admin"
            }
            
            await client.post("/api/v1/auth/register", json=admin_data)
            login_response = await client.post("/api/v1/auth/login", json={
                "email": admin_data["email"],
                "password": admin_data["password"]
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Test dashboard metrics
            dashboard_response = await client.get("/api/v1/admin/dashboard")
            assert dashboard_response.status_code == status.HTTP_200_OK
            dashboard_data = dashboard_response.json()
            assert "total_users" in dashboard_data
            assert "total_bookings" in dashboard_data
            assert "total_revenue" in dashboard_data
            assert "active_trips" in dashboard_data
            
            # Test user management
            users_response = await client.get("/api/v1/admin/users")
            assert users_response.status_code == status.HTTP_200_OK
            users = users_response.json()
            assert isinstance(users, list)
            
            # Test fleet management
            scenario = TestDataBuilder.create_complete_booking_scenario()
            
            # Create new trip
            trip_data = {
                "route_id": str(scenario['route'].id),
                "bus_id": str(scenario['bus'].id),
                "driver_id": str(scenario['driver'].id),
                "departure_time": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "fare": "45.00"
            }
            
            trip_response = await client.post("/api/v1/admin/trips", json=trip_data)
            assert trip_response.status_code == status.HTTP_201_CREATED
            trip = trip_response.json()
            assert trip["fare"] == "45.00"
            assert trip["status"] == "scheduled"
            
            # Test trip monitoring
            trips_response = await client.get("/api/v1/admin/trips")
            assert trips_response.status_code == status.HTTP_200_OK
            trips = trips_response.json()
            assert len(trips) > 0
            
            # Test review moderation
            reviews_response = await client.get("/api/v1/admin/reviews")
            assert reviews_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, override_get_db):
        """Test data consistency across all system operations."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create user and complete booking flow
            result = await self.test_complete_booking_flow_integration(override_get_db)
            
            booking_id = result["booking"]["id"]
            user_id = result["user_id"]
            
            # Verify data consistency across different endpoints
            
            # 1. Check booking appears in user's booking history
            client.headers.update({"Authorization": f"Bearer {result['tokens']['access_token']}"})
            bookings_response = await client.get("/api/v1/bookings/my-bookings")
            assert bookings_response.status_code == status.HTTP_200_OK
            user_bookings = bookings_response.json()
            
            booking_found = any(b["id"] == booking_id for b in user_bookings)
            assert booking_found, "Booking not found in user's booking history"
            
            # 2. Check payment record exists and matches booking
            payment_history_response = await client.get("/api/v1/payments/history")
            assert payment_history_response.status_code == status.HTTP_200_OK
            payments = payment_history_response.json()
            
            payment_found = any(p["booking_id"] == booking_id for p in payments)
            assert payment_found, "Payment not found in payment history"
            
            # 3. Check seat availability is updated
            trip_id = result["booking"]["trip"]["id"]
            trip_response = await client.get(f"/api/v1/bookings/trips/{trip_id}")
            assert trip_response.status_code == status.HTTP_200_OK
            trip_data = trip_response.json()
            
            # Seats should be marked as occupied
            occupied_seats = trip_data.get("occupied_seats", [])
            booked_seats = result["booking"]["seat_numbers"]
            for seat in booked_seats:
                assert seat in occupied_seats, f"Seat {seat} not marked as occupied"
            
            # 4. Test booking cancellation and data consistency
            cancel_response = await client.post(f"/api/v1/bookings/{booking_id}/cancel")
            assert cancel_response.status_code == status.HTTP_200_OK
            
            # Verify booking status is updated
            updated_booking_response = await client.get(f"/api/v1/bookings/{booking_id}")
            updated_booking = updated_booking_response.json()
            assert updated_booking["status"] == "cancelled"
            
            # Verify seats are released
            updated_trip_response = await client.get(f"/api/v1/bookings/trips/{trip_id}")
            updated_trip_data = updated_trip_response.json()
            updated_occupied_seats = updated_trip_data.get("occupied_seats", [])
            
            for seat in booked_seats:
                assert seat not in updated_occupied_seats, f"Seat {seat} still marked as occupied after cancellation"

    @pytest.mark.asyncio
    async def test_load_testing_critical_endpoints(self, override_get_db):
        """Perform load testing on critical system endpoints."""
        scenario = TestDataBuilder.create_complete_booking_scenario()
        
        # Test concurrent trip searches
        async def search_trips():
            async with AsyncClient(app=app, base_url="http://test") as client:
                search_params = {
                    "origin_terminal_id": str(scenario['origin_terminal'].id),
                    "destination_terminal_id": str(scenario['destination_terminal'].id),
                    "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
                }
                
                start_time = time.time()
                response = await client.get("/api/v1/bookings/trips/search", params=search_params)
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "endpoint": "trip_search"
                }
        
        # Test concurrent authentication requests
        async def authenticate_user(user_index):
            async with AsyncClient(app=app, base_url="http://test") as client:
                user_data = {
                    "email": f"load_test_user_{user_index}@example.com",
                    "password": "LoadTest123!",
                    "first_name": f"LoadTest{user_index}",
                    "last_name": "User"
                }
                
                # Register
                register_start = time.time()
                register_response = await client.post("/api/v1/auth/register", json=user_data)
                register_end = time.time()
                
                if register_response.status_code != status.HTTP_201_CREATED:
                    return {
                        "status_code": register_response.status_code,
                        "response_time": register_end - register_start,
                        "endpoint": "register",
                        "error": "registration_failed"
                    }
                
                # Login
                login_start = time.time()
                login_response = await client.post("/api/v1/auth/login", json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                })
                login_end = time.time()
                
                return {
                    "status_code": login_response.status_code,
                    "response_time": login_end - login_start,
                    "endpoint": "login"
                }
        
        # Execute load tests
        num_concurrent_requests = 50
        
        # Test trip search load
        search_tasks = [search_trips() for _ in range(num_concurrent_requests)]
        search_results = await asyncio.gather(*search_tasks)
        
        # Analyze search results
        successful_searches = [r for r in search_results if r["status_code"] == status.HTTP_200_OK]
        avg_search_time = sum(r["response_time"] for r in successful_searches) / len(successful_searches)
        
        assert len(successful_searches) >= num_concurrent_requests * 0.95, "Less than 95% of search requests succeeded"
        assert avg_search_time < 2.0, f"Average search response time {avg_search_time:.2f}s exceeds 2s threshold"
        
        # Test authentication load
        auth_tasks = [authenticate_user(i) for i in range(num_concurrent_requests)]
        auth_results = await asyncio.gather(*auth_tasks)
        
        # Analyze authentication results
        successful_auths = [r for r in auth_results if r["status_code"] == status.HTTP_200_OK]
        avg_auth_time = sum(r["response_time"] for r in successful_auths) / len(successful_auths) if successful_auths else 0
        
        assert len(successful_auths) >= num_concurrent_requests * 0.90, "Less than 90% of auth requests succeeded"
        assert avg_auth_time < 1.0, f"Average auth response time {avg_auth_time:.2f}s exceeds 1s threshold"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, override_get_db):
        """Test comprehensive error handling and system recovery."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test 1: Database connection failure simulation
            with patch('app.core.database.get_db') as mock_db:
                mock_db.side_effect = Exception("Database connection failed")
                
                response = await client.get("/api/v1/bookings/trips/search", params={
                    "origin_terminal_id": str(uuid.uuid4()),
                    "destination_terminal_id": str(uuid.uuid4()),
                    "departure_date": "2024-12-25"
                })
                
                # Should return appropriate error response
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Test 2: External service failure (payment gateway)
            user_data = {
                "email": "error_test@example.com",
                "password": "ErrorTest123!",
                "first_name": "Error",
                "last_name": "TestUser"
            }
            
            await client.post("/api/v1/auth/register", json=user_data)
            login_response = await client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            scenario = TestDataBuilder.create_complete_booking_scenario()
            booking_data = {
                "trip_id": str(scenario['trip'].id),
                "seat_numbers": [1],
                "passenger_details": user_data
            }
            
            booking_response = await client.post("/api/v1/bookings/", json=booking_data)
            booking = booking_response.json()
            
            # Simulate payment gateway failure
            with patch('app.services.payment_service.stripe.PaymentIntent.create') as mock_create:
                mock_create.side_effect = Exception("Payment gateway unavailable")
                
                payment_intent_response = await client.post("/api/v1/payments/create-intent", json={
                    "booking_id": booking["id"],
                    "payment_method": "card"
                })
                
                # Should handle gracefully with fallback
                assert payment_intent_response.status_code in [
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ]
            
            # Test 3: Invalid data handling
            invalid_booking_data = {
                "trip_id": "invalid-uuid",
                "seat_numbers": [999],  # Invalid seat number
                "passenger_details": {
                    "first_name": "",  # Empty required field
                    "last_name": "Test"
                }
            }
            
            invalid_response = await client.post("/api/v1/bookings/", json=invalid_booking_data)
            assert invalid_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            error_data = invalid_response.json()
            assert "detail" in error_data
            assert isinstance(error_data["detail"], list)

    @pytest.mark.asyncio
    async def test_system_performance_under_load(self, override_get_db):
        """Test system performance under various load conditions."""
        # Create test data
        scenario = TestDataBuilder.create_complete_booking_scenario()
        
        # Performance test metrics
        performance_metrics = {
            "response_times": [],
            "error_rates": [],
            "throughput": []
        }
        
        # Test 1: Gradual load increase
        for load_level in [10, 25, 50, 100]:
            start_time = time.time()
            
            async def make_request():
                async with AsyncClient(app=app, base_url="http://test") as client:
                    try:
                        response = await client.get("/api/v1/bookings/trips/search", params={
                            "origin_terminal_id": str(scenario['origin_terminal'].id),
                            "destination_terminal_id": str(scenario['destination_terminal'].id),
                            "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
                        })
                        return {
                            "success": response.status_code == status.HTTP_200_OK,
                            "response_time": time.time() - start_time
                        }
                    except Exception:
                        return {
                            "success": False,
                            "response_time": time.time() - start_time
                        }
            
            # Execute requests for current load level
            tasks = [make_request() for _ in range(load_level)]
            results = await asyncio.gather(*tasks)
            
            # Calculate metrics
            successful_requests = [r for r in results if r["success"]]
            success_rate = len(successful_requests) / len(results)
            avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
            
            performance_metrics["response_times"].append(avg_response_time)
            performance_metrics["error_rates"].append(1 - success_rate)
            performance_metrics["throughput"].append(len(successful_requests) / (time.time() - start_time))
            
            # Performance assertions
            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% at load level {load_level}"
            assert avg_response_time < 3.0, f"Average response time {avg_response_time:.2f}s exceeds 3s at load level {load_level}"
        
        # Verify performance doesn't degrade significantly with increased load
        initial_response_time = performance_metrics["response_times"][0]
        final_response_time = performance_metrics["response_times"][-1]
        
        # Response time shouldn't increase by more than 300%
        assert final_response_time <= initial_response_time * 3, "Response time degraded too much under load"

    @pytest.mark.asyncio
    async def test_cross_platform_data_synchronization(self, override_get_db):
        """Test data synchronization across web, mobile, and admin platforms."""
        # This test simulates actions from different platform types
        
        # Web platform user
        async with AsyncClient(app=app, base_url="http://test") as web_client:
            web_user_data = {
                "email": "web_user@example.com",
                "password": "WebUser123!",
                "first_name": "Web",
                "last_name": "User"
            }
            
            await web_client.post("/api/v1/auth/register", json=web_user_data)
            web_login = await web_client.post("/api/v1/auth/login", json={
                "email": web_user_data["email"],
                "password": web_user_data["password"]
            })
            web_tokens = web_login.json()
            web_client.headers.update({"Authorization": f"Bearer {web_tokens['access_token']}"})
            
            # Mobile platform user (simulated)
            async with AsyncClient(app=app, base_url="http://test") as mobile_client:
                mobile_user_data = {
                    "email": "mobile_user@example.com",
                    "password": "MobileUser123!",
                    "first_name": "Mobile",
                    "last_name": "User"
                }
                
                await mobile_client.post("/api/v1/auth/register", json=mobile_user_data)
                mobile_login = await mobile_client.post("/api/v1/auth/login", json={
                    "email": mobile_user_data["email"],
                    "password": mobile_user_data["password"]
                })
                mobile_tokens = mobile_login.json()
                mobile_client.headers.update({"Authorization": f"Bearer {mobile_tokens['access_token']}"})
                
                # Admin platform user
                async with AsyncClient(app=app, base_url="http://test") as admin_client:
                    admin_user_data = {
                        "email": "cross_platform_admin@example.com",
                        "password": "AdminUser123!",
                        "first_name": "Admin",
                        "last_name": "User",
                        "role": "admin"
                    }
                    
                    await admin_client.post("/api/v1/auth/register", json=admin_user_data)
                    admin_login = await admin_client.post("/api/v1/auth/login", json={
                        "email": admin_user_data["email"],
                        "password": admin_user_data["password"]
                    })
                    admin_tokens = admin_login.json()
                    admin_client.headers.update({"Authorization": f"Bearer {admin_tokens['access_token']}"})
                    
                    # Test scenario: Web user creates booking, mobile user views it, admin monitors it
                    scenario = TestDataBuilder.create_complete_booking_scenario()
                    
                    # 1. Web user creates booking
                    web_booking_data = {
                        "trip_id": str(scenario['trip'].id),
                        "seat_numbers": [1, 2],
                        "passenger_details": web_user_data
                    }
                    
                    web_booking_response = await web_client.post("/api/v1/bookings/", json=web_booking_data)
                    assert web_booking_response.status_code == status.HTTP_201_CREATED
                    web_booking = web_booking_response.json()
                    
                    # 2. Mobile user searches for same trip and sees updated seat availability
                    mobile_search_response = await mobile_client.get("/api/v1/bookings/trips/search", params={
                        "origin_terminal_id": str(scenario['origin_terminal'].id),
                        "destination_terminal_id": str(scenario['destination_terminal'].id),
                        "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
                    })
                    assert mobile_search_response.status_code == status.HTTP_200_OK
                    mobile_trips = mobile_search_response.json()
                    
                    # Find the same trip and verify seat availability is updated
                    mobile_trip = next((t for t in mobile_trips if t["id"] == str(scenario['trip'].id)), None)
                    assert mobile_trip is not None
                    assert mobile_trip["available_seats"] == scenario['trip'].capacity - 2  # 2 seats booked
                    
                    # 3. Admin views booking in dashboard
                    admin_dashboard_response = await admin_client.get("/api/v1/admin/dashboard")
                    assert admin_dashboard_response.status_code == status.HTTP_200_OK
                    dashboard_data = admin_dashboard_response.json()
                    
                    # Verify booking count is updated
                    assert dashboard_data["total_bookings"] > 0
                    
                    # 4. Admin views specific booking details
                    admin_booking_response = await admin_client.get(f"/api/v1/admin/bookings/{web_booking['id']}")
                    assert admin_booking_response.status_code == status.HTTP_200_OK
                    admin_booking_view = admin_booking_response.json()
                    
                    # Verify data consistency across platforms
                    assert admin_booking_view["id"] == web_booking["id"]
                    assert admin_booking_view["seat_numbers"] == web_booking["seat_numbers"]
                    assert admin_booking_view["status"] == web_booking["status"]
                    
                    # 5. Test real-time updates: Admin updates trip status
                    trip_update_data = {
                        "status": "delayed",
                        "delay_minutes": 30
                    }
                    
                    admin_trip_update_response = await admin_client.patch(
                        f"/api/v1/admin/trips/{scenario['trip'].id}",
                        json=trip_update_data
                    )
                    assert admin_trip_update_response.status_code == status.HTTP_200_OK
                    
                    # 6. Verify web and mobile users see updated trip status
                    web_trip_response = await web_client.get(f"/api/v1/bookings/trips/{scenario['trip'].id}")
                    mobile_trip_response = await mobile_client.get(f"/api/v1/bookings/trips/{scenario['trip'].id}")
                    
                    assert web_trip_response.status_code == status.HTTP_200_OK
                    assert mobile_trip_response.status_code == status.HTTP_200_OK
                    
                    web_trip_data = web_trip_response.json()
                    mobile_trip_data = mobile_trip_response.json()
                    
                    assert web_trip_data["status"] == "delayed"
                    assert mobile_trip_data["status"] == "delayed"
                    assert web_trip_data["delay_minutes"] == 30
                    assert mobile_trip_data["delay_minutes"] == 30


@pytest.mark.e2e
class TestUserAcceptanceScenarios:
    """User acceptance test scenarios covering complete user journeys."""
    
    @pytest.mark.asyncio
    async def test_passenger_complete_journey(self, override_get_db):
        """Test complete passenger journey from registration to trip completion."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # User Story: As a passenger, I want to book a trip, track it, and rate my experience
            
            # Step 1: User discovers the platform and registers
            passenger_data = {
                "email": "passenger_journey@example.com",
                "password": "PassengerJourney123!",
                "first_name": "Journey",
                "last_name": "Passenger",
                "phone": "+1234567890"
            }
            
            register_response = await client.post("/api/v1/auth/register", json=passenger_data)
            assert register_response.status_code == status.HTTP_201_CREATED
            
            # Step 2: User logs in
            login_response = await client.post("/api/v1/auth/login", json={
                "email": passenger_data["email"],
                "password": passenger_data["password"]
            })
            assert login_response.status_code == status.HTTP_200_OK
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Step 3: User searches for trips
            scenario = TestDataBuilder.create_complete_booking_scenario()
            search_params = {
                "origin_terminal_id": str(scenario['origin_terminal'].id),
                "destination_terminal_id": str(scenario['destination_terminal'].id),
                "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
            }
            
            search_response = await client.get("/api/v1/bookings/trips/search", params=search_params)
            assert search_response.status_code == status.HTTP_200_OK
            trips = search_response.json()
            assert len(trips) > 0
            
            # Step 4: User selects a trip and books seats
            selected_trip = trips[0]
            booking_data = {
                "trip_id": selected_trip["id"],
                "seat_numbers": [5, 6],  # Preferred seats
                "passenger_details": passenger_data
            }
            
            booking_response = await client.post("/api/v1/bookings/", json=booking_data)
            assert booking_response.status_code == status.HTTP_201_CREATED
            booking = booking_response.json()
            
            # Step 5: User completes payment
            payment_intent_response = await client.post("/api/v1/payments/create-intent", json={
                "booking_id": booking["id"],
                "payment_method": "card"
            })
            assert payment_intent_response.status_code == status.HTTP_200_OK
            payment_intent = payment_intent_response.json()
            
            payment_confirm_response = await client.post("/api/v1/payments/confirm", json={
                "payment_intent_id": payment_intent["payment_intent_id"],
                "booking_id": booking["id"]
            })
            assert payment_confirm_response.status_code == status.HTTP_200_OK
            
            # Step 6: User receives confirmation and downloads receipt
            booking_details_response = await client.get(f"/api/v1/bookings/{booking['id']}")
            confirmed_booking = booking_details_response.json()
            assert confirmed_booking["status"] == "confirmed"
            
            # Step 7: User tracks trip in real-time (day of travel)
            trip_location_response = await client.get(f"/api/v1/tracking/trips/{selected_trip['id']}/location")
            assert trip_location_response.status_code == status.HTTP_200_OK
            
            eta_response = await client.get(f"/api/v1/tracking/trips/{selected_trip['id']}/eta")
            assert eta_response.status_code == status.HTTP_200_OK
            
            # Step 8: Trip completes, user rates experience
            review_data = {
                "booking_id": booking["id"],
                "rating": 5,
                "comment": "Excellent service! Very comfortable and on time."
            }
            
            review_response = await client.post("/api/v1/reviews/", json=review_data)
            assert review_response.status_code == status.HTTP_201_CREATED
            
            # Step 9: User views booking history
            history_response = await client.get("/api/v1/bookings/my-bookings")
            assert history_response.status_code == status.HTTP_200_OK
            bookings = history_response.json()
            
            completed_booking = next((b for b in bookings if b["id"] == booking["id"]), None)
            assert completed_booking is not None
            assert completed_booking["status"] == "completed"

    @pytest.mark.asyncio
    async def test_driver_operational_workflow(self, override_get_db):
        """Test driver's operational workflow during trip execution."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # User Story: As a driver, I want to manage my assigned trips and update locations
            
            # Step 1: Driver logs in
            driver_data = {
                "email": "driver_workflow@example.com",
                "password": "DriverWorkflow123!",
                "first_name": "Workflow",
                "last_name": "Driver",
                "role": "driver"
            }
            
            await client.post("/api/v1/auth/register", json=driver_data)
            login_response = await client.post("/api/v1/auth/login", json={
                "email": driver_data["email"],
                "password": driver_data["password"]
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Step 2: Driver views assigned trips
            assigned_trips_response = await client.get("/api/v1/drivers/my-trips")
            assert assigned_trips_response.status_code == status.HTTP_200_OK
            
            # Step 3: Driver starts trip and updates location
            scenario = TestDataBuilder.create_trip_with_tracking()
            trip_id = str(scenario['trip'].id)
            
            # Start trip
            start_trip_response = await client.post(f"/api/v1/drivers/trips/{trip_id}/start")
            assert start_trip_response.status_code == status.HTTP_200_OK
            
            # Update location during trip
            locations = [
                {"latitude": 40.7128, "longitude": -74.0060, "speed": 60.0, "heading": 90.0},
                {"latitude": 40.7130, "longitude": -74.0058, "speed": 65.0, "heading": 95.0},
                {"latitude": 40.7132, "longitude": -74.0056, "speed": 70.0, "heading": 100.0}
            ]
            
            for location in locations:
                location_response = await client.post(
                    f"/api/v1/tracking/trips/{trip_id}/location",
                    json=location
                )
                assert location_response.status_code == status.HTTP_200_OK
                await asyncio.sleep(0.1)  # Simulate real-time updates
            
            # Step 4: Driver completes trip
            complete_trip_response = await client.post(f"/api/v1/drivers/trips/{trip_id}/complete")
            assert complete_trip_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_admin_management_scenarios(self, override_get_db):
        """Test admin management scenarios for system oversight."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # User Story: As an admin, I want to monitor and manage the entire system
            
            # Step 1: Admin logs in
            admin_data = {
                "email": "admin_management@example.com",
                "password": "AdminManagement123!",
                "first_name": "Management",
                "last_name": "Admin",
                "role": "admin"
            }
            
            await client.post("/api/v1/auth/register", json=admin_data)
            login_response = await client.post("/api/v1/auth/login", json={
                "email": admin_data["email"],
                "password": admin_data["password"]
            })
            tokens = login_response.json()
            client.headers.update({"Authorization": f"Bearer {tokens['access_token']}"})
            
            # Step 2: Admin reviews dashboard metrics
            dashboard_response = await client.get("/api/v1/admin/dashboard")
            assert dashboard_response.status_code == status.HTTP_200_OK
            dashboard = dashboard_response.json()
            
            # Verify key metrics are present
            required_metrics = ["total_users", "total_bookings", "total_revenue", "active_trips"]
            for metric in required_metrics:
                assert metric in dashboard
            
            # Step 3: Admin manages fleet operations
            scenario = TestDataBuilder.create_complete_booking_scenario()
            
            # Create new route
            route_data = {
                "origin_terminal_id": str(scenario['origin_terminal'].id),
                "destination_terminal_id": str(scenario['destination_terminal'].id),
                "distance_km": 250.5,
                "estimated_duration_minutes": 300,
                "base_fare": 55.00
            }
            
            route_response = await client.post("/api/v1/admin/routes", json=route_data)
            assert route_response.status_code == status.HTTP_201_CREATED
            
            # Schedule new trip
            trip_data = {
                "route_id": str(scenario['route'].id),
                "bus_id": str(scenario['bus'].id),
                "driver_id": str(scenario['driver'].id),
                "departure_time": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
                "fare": "60.00"
            }
            
            trip_response = await client.post("/api/v1/admin/trips", json=trip_data)
            assert trip_response.status_code == status.HTTP_201_CREATED
            
            # Step 4: Admin monitors user activity
            users_response = await client.get("/api/v1/admin/users")
            assert users_response.status_code == status.HTTP_200_OK
            
            # Step 5: Admin handles customer service issues
            reviews_response = await client.get("/api/v1/admin/reviews")
            assert reviews_response.status_code == status.HTTP_200_OK
            
            # Step 6: Admin generates reports
            revenue_report_response = await client.get("/api/v1/admin/reports/revenue", params={
                "start_date": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": datetime.utcnow().strftime("%Y-%m-%d")
            })
            assert revenue_report_response.status_code == status.HTTP_200_OK


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__,
        "-v",
        "-m", "e2e",
        "--tb=short"
    ])