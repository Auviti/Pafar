#!/usr/bin/env python3
"""
Test script for admin endpoints functionality.
"""
import asyncio
import httpx
from datetime import datetime, timedelta


async def get_admin_token(client: httpx.AsyncClient) -> str:
    """Get admin token for testing protected endpoints."""
    # First register an admin user
    admin_data = {
        "email": "admin@test.com",
        "password": "AdminPass123!",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "+1234567890"
    }
    
    # Register admin user
    response = await client.post("/api/v1/auth/register", json=admin_data)
    if response.status_code not in [200, 201, 409]:  # 409 if user already exists
        print(f"Admin registration failed: {response.status_code} - {response.text}")
        return None
    
    # Login to get token
    login_data = {
        "email": admin_data["email"],
        "password": admin_data["password"]
    }
    
    response = await client.post("/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"Admin login failed: {response.status_code} - {response.text}")
        return None
    
    token_data = response.json()
    return token_data["access_token"]


async def test_admin_endpoints():
    """Test admin endpoints functionality."""
    print("🔧 Testing Admin Endpoints...")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            # Get admin token
            admin_token = await get_admin_token(client)
            if not admin_token:
                print("❌ Failed to get admin token")
                return False
            
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            # Test 1: Dashboard metrics
            print("\n1. Testing dashboard metrics...")
            response = await client.get("/api/v1/admin/dashboard", headers=headers)
            if response.status_code == 200:
                metrics = response.json()
                print(f"  ✓ Dashboard metrics retrieved")
                print(f"    - Total users: {metrics.get('total_users', 0)}")
                print(f"    - Active users: {metrics.get('active_users', 0)}")
                print(f"    - Total bookings: {metrics.get('total_bookings', 0)}")
                print(f"    - Total revenue: ${metrics.get('total_revenue', 0)}")
            else:
                print(f"  ❌ Dashboard metrics failed: {response.status_code}")
                return False
            
            # Test 2: User search
            print("\n2. Testing user search...")
            response = await client.get("/api/v1/admin/users/search", headers=headers)
            if response.status_code == 200:
                users = response.json()
                print(f"  ✓ User search successful")
                print(f"    - Found {users.get('total_count', 0)} users")
            else:
                print(f"  ❌ User search failed: {response.status_code}")
                return False
            
            # Test 3: System health
            print("\n3. Testing system health...")
            response = await client.get("/api/v1/admin/system/health", headers=headers)
            if response.status_code == 200:
                health = response.json()
                print(f"  ✓ System health retrieved")
                print(f"    - Database: {health.get('database_status', 'unknown')}")
                print(f"    - Redis: {health.get('redis_status', 'unknown')}")
                print(f"    - API response time: {health.get('api_response_time', 0)}s")
            else:
                print(f"  ❌ System health failed: {response.status_code}")
                return False
            
            # Test 4: Fraud alerts
            print("\n4. Testing fraud alerts...")
            response = await client.get("/api/v1/admin/fraud-alerts", headers=headers)
            if response.status_code == 200:
                alerts = response.json()
                print(f"  ✓ Fraud alerts retrieved")
                print(f"    - Found {alerts.get('total_count', 0)} alerts")
            else:
                print(f"  ❌ Fraud alerts failed: {response.status_code}")
                return False
            
            # Test 5: Live trip data
            print("\n5. Testing live trip data...")
            response = await client.get("/api/v1/admin/trips/live", headers=headers)
            if response.status_code == 200:
                trips = response.json()
                print(f"  ✓ Live trip data retrieved")
                print(f"    - Found {len(trips)} active trips")
            else:
                print(f"  ❌ Live trip data failed: {response.status_code}")
                return False
            
            # Test 6: Create fraud alert (test endpoint)
            print("\n6. Testing fraud alert creation...")
            alert_data = {
                "alert_type": "test_alert",
                "severity": "medium",
                "description": "Test fraud alert for admin endpoint testing"
            }
            response = await client.post("/api/v1/admin/fraud-alerts/create", 
                                       params=alert_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Fraud alert created successfully")
                print(f"    - Alert ID: {result.get('alert_id')}")
            else:
                print(f"  ❌ Fraud alert creation failed: {response.status_code}")
                return False
            
            print("\n✅ All admin endpoint tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Admin endpoint test failed with error: {e}")
            return False


async def main():
    """Main test function."""
    print("🚀 Starting Admin Endpoint Tests")
    print("=" * 50)
    
    success = await test_admin_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All admin endpoint tests completed successfully!")
    else:
        print("💥 Some admin endpoint tests failed!")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())