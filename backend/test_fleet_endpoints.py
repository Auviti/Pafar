"""
Test script for fleet management API endpoints.
"""
import asyncio
import httpx
import json
from typing import Dict, Any
from datetime import datetime, timedelta


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def get_admin_token(client: httpx.AsyncClient) -> str:
    """Get admin token for testing protected endpoints."""
    # First register an admin user
    admin_data = {
        "email": "admin@test.com",
        "password": "AdminPass123",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "+1234567891",
        "role": "admin"
    }
    
    try:
        # Try to register (might fail if already exists)
        await client.post(f"{API_BASE}/auth/register", json=admin_data)
    except:
        pass
    
    # Login to get token
    login_data = {
        "email": "admin@test.com",
        "password": "AdminPass123"
    }
    
    response = await client.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get admin token: {response.text}")


async def get_driver_token(client: httpx.AsyncClient) -> str:
    """Get driver token for testing trip creation."""
    # First register a driver user
    driver_data = {
        "email": "driver@test.com",
        "password": "DriverPass123",
        "first_name": "Driver",
        "last_name": "User",
        "phone": "+1234567892",
        "role": "driver"
    }
    
    try:
        # Try to register (might fail if already exists)
        await client.post(f"{API_BASE}/auth/register", json=driver_data)
    except:
        pass
    
    # Login to get token
    login_data = {
        "email": "driver@test.com",
        "password": "DriverPass123"
    }
    
    response = await client.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get driver token: {response.text}")


async def test_fleet_endpoints():
    """Test fleet management endpoints."""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Fleet Management API Endpoints\n")
        
        # Get admin token for protected operations
        try:
            admin_token = await get_admin_token(client)
            driver_token = await get_driver_token(client)
            admin_headers = {"Authorization": f"Bearer {admin_token}"}
            print("✅ Admin and driver tokens obtained")
        except Exception as e:
            print(f"❌ Failed to get tokens: {e}")
            return
        
        # Test Terminal Management
        print("\n📍 Testing Terminal Management")
        
        # Create terminals
        terminal1_data = {
            "name": "Central Station",
            "city": "New York",
            "address": "123 Main St",
            "latitude": 40.7128,
            "longitude": -74.0060
        }
        
        terminal2_data = {
            "name": "Downtown Terminal",
            "city": "Boston",
            "address": "456 Oak Ave",
            "latitude": 42.3601,
            "longitude": -71.0589
        }
        
        terminal1_id = None
        terminal2_id = None
        
        # Create terminal 1
        try:
            response = await client.post(f"{API_BASE}/fleet/terminals", json=terminal1_data, headers=admin_headers)
            if response.status_code == 201:
                terminal1 = response.json()
                terminal1_id = terminal1["id"]
                print(f"✅ Terminal 1 created: {terminal1['name']} in {terminal1['city']}")
            else:
                print(f"❌ Terminal 1 creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Terminal 1 creation error: {e}")
            return
        
        # Create terminal 2
        try:
            response = await client.post(f"{API_BASE}/fleet/terminals", json=terminal2_data, headers=admin_headers)
            if response.status_code == 201:
                terminal2 = response.json()
                terminal2_id = terminal2["id"]
                print(f"✅ Terminal 2 created: {terminal2['name']} in {terminal2['city']}")
            else:
                print(f"❌ Terminal 2 creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Terminal 2 creation error: {e}")
            return
        
        # Get terminals
        try:
            response = await client.get(f"{API_BASE}/fleet/terminals")
            if response.status_code == 200:
                terminals_data = response.json()
                print(f"✅ Retrieved {terminals_data['total']} terminals")
            else:
                print(f"❌ Get terminals failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Get terminals error: {e}")
        
        # Test Route Management
        print("\n🛣️  Testing Route Management")
        
        route_data = {
            "origin_terminal_id": terminal1_id,
            "destination_terminal_id": terminal2_id,
            "distance_km": 215.5,
            "estimated_duration_minutes": 240,
            "base_fare": 45.00
        }
        
        route_id = None
        
        # Create route
        try:
            response = await client.post(f"{API_BASE}/fleet/routes", json=route_data, headers=admin_headers)
            if response.status_code == 201:
                route = response.json()
                route_id = route["id"]
                print(f"✅ Route created: {route['distance_km']}km, ${route['base_fare']}")
            else:
                print(f"❌ Route creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Route creation error: {e}")
            return
        
        # Get routes
        try:
            response = await client.get(f"{API_BASE}/fleet/routes")
            if response.status_code == 200:
                routes_data = response.json()
                print(f"✅ Retrieved {routes_data['total']} routes")
            else:
                print(f"❌ Get routes failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Get routes error: {e}")
        
        # Test Bus Management
        print("\n🚌 Testing Bus Management")
        
        bus_data = {
            "license_plate": "NYC-BUS-001",
            "model": "Mercedes Sprinter",
            "capacity": 50,
            "amenities": {
                "wifi": True,
                "ac": True,
                "usb_charging": True
            }
        }
        
        bus_id = None
        
        # Create bus
        try:
            response = await client.post(f"{API_BASE}/fleet/buses", json=bus_data, headers=admin_headers)
            if response.status_code == 201:
                bus = response.json()
                bus_id = bus["id"]
                print(f"✅ Bus created: {bus['license_plate']}, capacity: {bus['capacity']}")
            else:
                print(f"❌ Bus creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Bus creation error: {e}")
            return
        
        # Get buses
        try:
            response = await client.get(f"{API_BASE}/fleet/buses")
            if response.status_code == 200:
                buses_data = response.json()
                print(f"✅ Retrieved {buses_data['total']} buses")
            else:
                print(f"❌ Get buses failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Get buses error: {e}")
        
        # Test Trip Management
        print("\n🚍 Testing Trip Management")
        
        # Get driver user ID from token
        try:
            response = await client.get(f"{API_BASE}/auth/me", headers={"Authorization": f"Bearer {driver_token}"})
            if response.status_code == 200:
                driver_user = response.json()
                driver_id = driver_user["id"]
                print(f"✅ Driver user ID obtained: {driver_id}")
            else:
                print(f"❌ Failed to get driver user: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Driver user error: {e}")
            return
        
        departure_time = (datetime.now() + timedelta(hours=2)).isoformat()
        trip_data = {
            "route_id": route_id,
            "bus_id": bus_id,
            "driver_id": driver_id,
            "departure_time": departure_time,
            "fare": 50.00
        }
        
        trip_id = None
        
        # Create trip
        try:
            response = await client.post(f"{API_BASE}/fleet/trips", json=trip_data, headers=admin_headers)
            if response.status_code == 201:
                trip = response.json()
                trip_id = trip["id"]
                print(f"✅ Trip created: ${trip['fare']}, departure: {trip['departure_time']}")
                print(f"   Available seats: {trip['available_seats']}")
            else:
                print(f"❌ Trip creation failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Trip creation error: {e}")
            return
        
        # Get trips
        try:
            response = await client.get(f"{API_BASE}/fleet/trips")
            if response.status_code == 200:
                trips_data = response.json()
                print(f"✅ Retrieved {trips_data['total']} trips")
            else:
                print(f"❌ Get trips failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Get trips error: {e}")
        
        # Test Update Operations
        print("\n✏️  Testing Update Operations")
        
        # Update terminal
        try:
            update_data = {"name": "Central Station Updated"}
            response = await client.put(f"{API_BASE}/fleet/terminals/{terminal1_id}", json=update_data, headers=admin_headers)
            if response.status_code == 200:
                updated_terminal = response.json()
                print(f"✅ Terminal updated: {updated_terminal['name']}")
            else:
                print(f"❌ Terminal update failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Terminal update error: {e}")
        
        # Update bus
        try:
            update_data = {"model": "Mercedes Sprinter Updated"}
            response = await client.put(f"{API_BASE}/fleet/buses/{bus_id}", json=update_data, headers=admin_headers)
            if response.status_code == 200:
                updated_bus = response.json()
                print(f"✅ Bus updated: {updated_bus['model']}")
            else:
                print(f"❌ Bus update failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Bus update error: {e}")
        
        # Test Filtering
        print("\n🔍 Testing Filtering")
        
        # Filter terminals by city
        try:
            response = await client.get(f"{API_BASE}/fleet/terminals?city=New York")
            if response.status_code == 200:
                filtered_terminals = response.json()
                print(f"✅ Filtered terminals by city: {filtered_terminals['total']} found")
            else:
                print(f"❌ Terminal filtering failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Terminal filtering error: {e}")
        
        # Filter routes by origin terminal
        try:
            response = await client.get(f"{API_BASE}/fleet/routes?origin_terminal_id={terminal1_id}")
            if response.status_code == 200:
                filtered_routes = response.json()
                print(f"✅ Filtered routes by origin: {filtered_routes['total']} found")
            else:
                print(f"❌ Route filtering failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Route filtering error: {e}")
        
        # Test Error Cases
        print("\n❌ Testing Error Cases")
        
        # Try to create route with non-existent terminals
        try:
            invalid_route_data = {
                "origin_terminal_id": "00000000-0000-0000-0000-000000000000",
                "destination_terminal_id": "00000000-0000-0000-0000-000000000001",
                "base_fare": 25.00
            }
            response = await client.post(f"{API_BASE}/fleet/routes", json=invalid_route_data, headers=admin_headers)
            if response.status_code == 404:
                print("✅ Invalid route creation properly rejected")
            else:
                print(f"❌ Expected 404, got {response.status_code}")
        except Exception as e:
            print(f"❌ Invalid route test error: {e}")
        
        # Try to create duplicate bus license plate
        try:
            duplicate_bus_data = {
                "license_plate": "NYC-BUS-001",  # Same as before
                "capacity": 40
            }
            response = await client.post(f"{API_BASE}/fleet/buses", json=duplicate_bus_data, headers=admin_headers)
            if response.status_code == 400:
                print("✅ Duplicate bus license plate properly rejected")
            else:
                print(f"❌ Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"❌ Duplicate bus test error: {e}")
        
        print("\n🎉 Fleet Management API testing completed!")


if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: uvicorn app.main:app --reload\n")
    asyncio.run(test_fleet_endpoints())