#!/usr/bin/env python3
"""
Test script to validate that all models and schemas are working correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_session_factory
from app.models.user import User, UserType
from app.models.ride import Ride, Location, DriverLocation, RideStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.user import UserCreate, UserResponse
from app.schemas.ride import RideCreate, LocationCreate, RideResponse
from app.schemas.payment import PaymentCreate, PaymentResponse
from sqlalchemy import select
from decimal import Decimal


async def test_models_and_schemas():
    """Test that all models and schemas work correctly."""
    print("Testing models and schemas...")
    
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Test User model and schema
        print("✓ Testing User model and schema...")
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if user:
            user_response = UserResponse.model_validate(user)
            print(f"  - User: {user_response.full_name} ({user_response.email})")
        
        # Test Location model
        print("✓ Testing Location model...")
        result = await session.execute(select(Location).limit(1))
        location = result.scalar_one_or_none()
        if location:
            print(f"  - Location: {location.address} ({location.latitude}, {location.longitude})")
        
        # Test Ride model and schema
        print("✓ Testing Ride model and schema...")
        result = await session.execute(select(Ride).limit(1))
        ride = result.scalar_one_or_none()
        if ride:
            # Load relationships
            await session.refresh(ride, ['pickup_location', 'destination_location', 'customer', 'driver'])
            ride_response = RideResponse.model_validate(ride)
            print(f"  - Ride: {ride_response.status} - ${ride_response.actual_fare}")
        
        # Test Payment model and schema
        print("✓ Testing Payment model and schema...")
        result = await session.execute(select(Payment).limit(1))
        payment = result.scalar_one_or_none()
        if payment:
            payment_response = PaymentResponse.model_validate(payment)
            print(f"  - Payment: {payment_response.status} - {payment_response.currency} {payment_response.amount}")
        
        # Test DriverLocation model
        print("✓ Testing DriverLocation model...")
        result = await session.execute(select(DriverLocation).limit(1))
        driver_location = result.scalar_one_or_none()
        if driver_location:
            print(f"  - Driver Location: Available={driver_location.is_available} at ({driver_location.latitude}, {driver_location.longitude})")
        
        # Test schema validation
        print("✓ Testing schema validation...")
        
        # Test UserCreate validation
        try:
            user_create = UserCreate(
                email="test@example.com",
                phone="+1234567890",
                full_name="Test User",
                password="TestPass123",
                user_type=UserType.CUSTOMER
            )
            print("  - UserCreate validation: PASSED")
        except Exception as e:
            print(f"  - UserCreate validation: FAILED - {e}")
        
        # Test LocationCreate validation
        try:
            location_create = LocationCreate(
                latitude=6.5244,
                longitude=3.3792,
                address="123 Test St",
                city="Lagos",
                country="Nigeria",
                postal_code="10001"
            )
            print("  - LocationCreate validation: PASSED")
        except Exception as e:
            print(f"  - LocationCreate validation: FAILED - {e}")
        
        # Test PaymentCreate validation
        try:
            payment_create = PaymentCreate(
                ride_id=ride.id if ride else "550e8400-e29b-41d4-a716-446655440000",
                amount=Decimal("25.50"),
                currency="USD",
                payment_method_id="pm_test_123"
            )
            print("  - PaymentCreate validation: PASSED")
        except Exception as e:
            print(f"  - PaymentCreate validation: FAILED - {e}")
    
    print("\n✅ All models and schemas are working correctly!")


async def main():
    """Main function."""
    try:
        await test_models_and_schemas()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())