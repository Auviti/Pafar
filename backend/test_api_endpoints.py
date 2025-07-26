"""
Simple script to test authentication API endpoints.
"""
import asyncio
import httpx
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"


async def test_auth_endpoints():
    """Test authentication endpoints."""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Authentication API Endpoints\n")
        
        # Test 1: Register a new user
        print("1. Testing user registration...")
        register_data = {
            "email": "test@example.com",
            "password": "TestPass123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "role": "passenger"
        }
        
        try:
            response = await client.post(f"{API_BASE}/auth/register", json=register_data)
            if response.status_code == 201:
                user_data = response.json()
                print(f"✅ User registered successfully: {user_data['email']}")
                print(f"   User ID: {user_data['id']}")
                print(f"   Verified: {user_data['is_verified']}")
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return
        
        # Test 2: Try to register duplicate user
        print("\n2. Testing duplicate user registration...")
        try:
            response = await client.post(f"{API_BASE}/auth/register", json=register_data)
            if response.status_code == 400:
                print("✅ Duplicate registration properly rejected")
            else:
                print(f"❌ Expected 400, got {response.status_code}")
        except Exception as e:
            print(f"❌ Duplicate registration test error: {e}")
        
        # Test 3: Login with valid credentials
        print("\n3. Testing user login...")
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123"
        }
        
        try:
            response = await client.post(f"{API_BASE}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                refresh_token = token_data["refresh_token"]
                print("✅ Login successful")
                print(f"   Token type: {token_data['token_type']}")
                print(f"   Expires in: {token_data['expires_in']} seconds")
                print(f"   User: {token_data['user']['first_name']} {token_data['user']['last_name']}")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"❌ Login error: {e}")
            return
        
        # Test 4: Access protected endpoint
        print("\n4. Testing protected endpoint access...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = await client.get(f"{API_BASE}/auth/me", headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                print("✅ Protected endpoint access successful")
                print(f"   User: {user_info['first_name']} {user_info['last_name']}")
                print(f"   Email: {user_info['email']}")
                print(f"   Role: {user_info['role']}")
            else:
                print(f"❌ Protected endpoint failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Protected endpoint error: {e}")
        
        # Test 5: Update user profile
        print("\n5. Testing profile update...")
        update_data = {
            "first_name": "Jane",
            "last_name": "Smith"
        }
        
        try:
            response = await client.put(f"{API_BASE}/auth/me", json=update_data, headers=headers)
            if response.status_code == 200:
                updated_user = response.json()
                print("✅ Profile update successful")
                print(f"   Updated name: {updated_user['first_name']} {updated_user['last_name']}")
            else:
                print(f"❌ Profile update failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Profile update error: {e}")
        
        # Test 6: Refresh token
        print("\n6. Testing token refresh...")
        refresh_data = {"refresh_token": refresh_token}
        
        try:
            response = await client.post(f"{API_BASE}/auth/refresh", json=refresh_data)
            if response.status_code == 200:
                new_token_data = response.json()
                print("✅ Token refresh successful")
                print(f"   New token type: {new_token_data['token_type']}")
                print(f"   Expires in: {new_token_data['expires_in']} seconds")
            else:
                print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # Test 7: Logout
        print("\n7. Testing logout...")
        try:
            response = await client.post(f"{API_BASE}/auth/logout", headers=headers)
            if response.status_code == 200:
                print("✅ Logout successful")
            else:
                print(f"❌ Logout failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Logout error: {e}")
        
        # Test 8: Try to access protected endpoint after logout
        print("\n8. Testing access after logout...")
        try:
            response = await client.get(f"{API_BASE}/auth/me", headers=headers)
            if response.status_code == 200:
                print("⚠️  Still able to access protected endpoint (access token not invalidated)")
            else:
                print("✅ Access properly denied after logout")
        except Exception as e:
            print(f"❌ Post-logout test error: {e}")
        
        print("\n🎉 Authentication API testing completed!")


if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: uvicorn app.main:app --reload\n")
    asyncio.run(test_auth_endpoints())