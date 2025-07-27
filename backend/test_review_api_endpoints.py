"""
Integration test for review API endpoints.
"""
import asyncio
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from app.main import app
from app.models.user import User, UserRole
from app.models.fleet import Terminal, Route, Bus, Trip, TripStatus
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.core.security import create_access_token
from app.core.database import get_db
from tests.conftest import TestSessionLocal, test_engine
from sqlalchemy.ext.asyncio import AsyncSession


async def test_review_endpoints():
    """Test review API endpoints."""
    
    # Override database dependency
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        # Create tables
        async with test_engine.begin() as conn:
            from app.core.database import Base
            await conn.run_sync(Base.metadata.create_all)
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Create test data
        async with TestSessionLocal() as db:
                # Create user
                user = User(
                    id=uuid4(),
                    email="test@example.com",
                    phone="+1234567890",
                    password_hash="hashed",
                    first_name="Test",
                    last_name="User",
                    role=UserRole.PASSENGER,
                    is_verified=True,
                    is_active=True
                )
                
                # Create driver
                driver = User(
                    id=uuid4(),
                    email="driver@example.com",
                    phone="+1234567891",
                    password_hash="hashed",
                    first_name="Test",
                    last_name="Driver",
                    role=UserRole.DRIVER,
                    is_verified=True,
                    is_active=True
                )
                
                # Create admin
                admin = User(
                    id=uuid4(),
                    email="admin@example.com",
                    phone="+1234567892",
                    password_hash="hashed",
                    first_name="Admin",
                    last_name="User",
                    role=UserRole.ADMIN,
                    is_verified=True,
                    is_active=True
                )
                
                # Create terminals
                origin = Terminal(
                    id=uuid4(),
                    name="Origin Terminal",
                    city="Origin City",
                    is_active=True
                )
                
                destination = Terminal(
                    id=uuid4(),
                    name="Destination Terminal",
                    city="Destination City",
                    is_active=True
                )
                
                # Create route
                route = Route(
                    id=uuid4(),
                    origin_terminal_id=origin.id,
                    destination_terminal_id=destination.id,
                    base_fare=Decimal("50.00"),
                    is_active=True
                )
                
                # Create bus
                bus = Bus(
                    id=uuid4(),
                    license_plate="ABC-123",
                    capacity=50,
                    is_active=True
                )
                
                # Create trip
                trip = Trip(
                    id=uuid4(),
                    route_id=route.id,
                    bus_id=bus.id,
                    driver_id=driver.id,
                    departure_time=datetime.utcnow() + timedelta(hours=2),
                    status=TripStatus.COMPLETED,
                    fare=Decimal("50.00"),
                    available_seats=48
                )
                
                # Create booking
                booking = Booking(
                    id=uuid4(),
                    user_id=user.id,
                    trip_id=trip.id,
                    seat_numbers=[1, 2],
                    total_amount=Decimal("100.00"),
                    status=BookingStatus.COMPLETED,
                    booking_reference="BK123456",
                    payment_status=PaymentStatus.COMPLETED
                )
                
                # Add all to database
                db.add_all([user, driver, admin, origin, destination, route, bus, trip, booking])
                await db.commit()
                
                # Create access tokens
                user_token = create_access_token({"sub": str(user.id)})
                admin_token = create_access_token({"sub": str(admin.id)})
                
                # Test creating a review
                review_data = {
                    "booking_id": str(booking.id),
                    "rating": 5,
                    "comment": "Excellent service!"
                }
                
                response = client.post(
                    "/api/v1/reviews",
                    json=review_data,
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                
                print(f"Create review response: {response.status_code}")
                if response.status_code != 201:
                    print(f"Response content: {response.text}")
                
                assert response.status_code == 201
                review_response = response.json()
                review_id = review_response["id"]
                
                # Test getting the review
                response = client.get(f"/api/v1/reviews/{review_id}")
                print(f"Get review response: {response.status_code}")
                assert response.status_code == 200
                
                # Test getting driver reviews
                response = client.get(f"/api/v1/drivers/{driver.id}/reviews")
                print(f"Get driver reviews response: {response.status_code}")
                assert response.status_code == 200
                
                # Test getting driver rating stats
                response = client.get(f"/api/v1/drivers/{driver.id}/rating-stats")
                print(f"Get driver stats response: {response.status_code}")
                assert response.status_code == 200
                
                # Test admin endpoints - get unmoderated reviews
                response = client.get(
                    "/api/v1/admin/reviews/unmoderated",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                print(f"Get unmoderated reviews response: {response.status_code}")
                assert response.status_code == 200
                
                # Test moderating a review
                moderation_data = {
                    "is_moderated": True,
                    "action_reason": "Approved after review"
                }
                
                response = client.put(
                    f"/api/v1/admin/reviews/{review_id}/moderate",
                    json=moderation_data,
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                print(f"Moderate review response: {response.status_code}")
                assert response.status_code == 200
                
                print("All review API endpoints working correctly!")
                
    finally:
        # Clean up
        app.dependency_overrides.clear()
        async with test_engine.begin() as conn:
            from app.core.database import Base
            await conn.run_sync(Base.metadata.drop_all)


if __name__ == "__main__":
    asyncio.run(test_review_endpoints())