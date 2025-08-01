"""
Performance tests using Locust.
"""
import json
import random
from locust import HttpUser, task, between
from datetime import datetime, timedelta


class PafarUser(HttpUser):
    """Simulated user for performance testing."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Set up user session."""
        self.access_token = None
        self.user_id = None
        self.booking_id = None
        
        # Register and login user
        self.register_and_login()
    
    def register_and_login(self):
        """Register and login a test user."""
        # Generate unique user data
        user_id = random.randint(10000, 99999)
        email = f"loadtest{user_id}@example.com"
        
        # Register user
        registration_data = {
            "email": email,
            "password": "LoadTest123",
            "first_name": "Load",
            "last_name": f"Test{user_id}",
            "phone": f"+1{random.randint(1000000000, 9999999999)}"
        }
        
        response = self.client.post("/api/v1/auth/register", json=registration_data)
        if response.status_code == 201:
            user_data = response.json()
            self.user_id = user_data["id"]
            
            # Simulate email verification
            self.client.post(f"/api/v1/auth/verify-email", json={
                "email": email,
                "code": "123456"  # Mock verification code
            })
            
            # Login
            login_data = {
                "email": email,
                "password": "LoadTest123"
            }
            
            login_response = self.client.post("/api/v1/auth/login", json=login_data)
            if login_response.status_code == 200:
                tokens = login_response.json()
                self.access_token = tokens["access_token"]
    
    @property
    def headers(self):
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(3)
    def search_trips(self):
        """Search for available trips."""
        # Get terminals first
        terminals_response = self.client.get("/api/v1/fleet/terminals")
        if terminals_response.status_code == 200:
            terminals = terminals_response.json()
            if len(terminals) >= 2:
                origin = random.choice(terminals)
                destination = random.choice([t for t in terminals if t["id"] != origin["id"]])
                
                # Search for trips
                tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
                params = {
                    "origin_terminal_id": origin["id"],
                    "destination_terminal_id": destination["id"],
                    "departure_date": tomorrow
                }
                
                with self.client.get("/api/v1/fleet/trips/search", params=params, 
                                   catch_response=True) as response:
                    if response.status_code == 200:
                        trips = response.json()
                        response.success()
                        return trips
                    else:
                        response.failure(f"Search failed: {response.status_code}")
        return []
    
    @task(2)
    def create_booking(self):
        """Create a booking."""
        if not self.access_token:
            return
        
        # Search for trips first
        trips = self.search_trips()
        if trips:
            trip = random.choice(trips)
            if trip.get("available_seats", 0) > 0:
                booking_data = {
                    "trip_id": trip["id"],
                    "seat_numbers": [random.randint(1, min(trip.get("available_seats", 50), 10))]
                }
                
                with self.client.post("/api/v1/bookings/", json=booking_data, 
                                    headers=self.headers, catch_response=True) as response:
                    if response.status_code == 201:
                        booking = response.json()
                        self.booking_id = booking["id"]
                        response.success()
                    else:
                        response.failure(f"Booking failed: {response.status_code}")
    
    @task(1)
    def get_user_bookings(self):
        """Get user's bookings."""
        if not self.access_token:
            return
        
        with self.client.get("/api/v1/bookings/my-bookings", headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get bookings failed: {response.status_code}")
    
    @task(1)
    def get_user_profile(self):
        """Get user profile."""
        if not self.access_token:
            return
        
        with self.client.get("/api/v1/auth/me", headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get profile failed: {response.status_code}")
    
    @task(1)
    def create_payment_intent(self):
        """Create payment intent."""
        if not self.access_token or not self.booking_id:
            return
        
        payment_data = {
            "booking_id": self.booking_id,
            "payment_method": "card"
        }
        
        with self.client.post("/api/v1/payments/create-intent", json=payment_data,
                            headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Payment intent failed: {response.status_code}")


class AdminUser(HttpUser):
    """Simulated admin user for performance testing."""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight than regular users
    
    def on_start(self):
        """Set up admin session."""
        self.access_token = None
        self.login_admin()
    
    def login_admin(self):
        """Login as admin user."""
        login_data = {
            "email": "admin@example.com",
            "password": "AdminPass123"
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
    
    @property
    def headers(self):
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(2)
    def get_admin_dashboard(self):
        """Get admin dashboard data."""
        if not self.access_token:
            return
        
        with self.client.get("/api/v1/admin/dashboard", headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Admin dashboard failed: {response.status_code}")
    
    @task(1)
    def get_users_list(self):
        """Get users list."""
        if not self.access_token:
            return
        
        with self.client.get("/api/v1/admin/users", headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get users failed: {response.status_code}")
    
    @task(1)
    def get_trips_list(self):
        """Get trips list."""
        if not self.access_token:
            return
        
        with self.client.get("/api/v1/admin/trips", headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get trips failed: {response.status_code}")


class DriverUser(HttpUser):
    """Simulated driver user for performance testing."""
    
    wait_time = between(5, 10)
    weight = 1  # Lower weight than regular users
    
    def on_start(self):
        """Set up driver session."""
        self.access_token = None
        self.trip_id = None
        self.login_driver()
    
    def login_driver(self):
        """Login as driver user."""
        login_data = {
            "email": "driver@example.com",
            "password": "DriverPass123"
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
    
    @property
    def headers(self):
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(3)
    def update_trip_location(self):
        """Update trip location."""
        if not self.access_token or not self.trip_id:
            # Get assigned trips first
            response = self.client.get("/api/v1/tracking/my-trips", headers=self.headers)
            if response.status_code == 200:
                trips = response.json()
                if trips:
                    self.trip_id = trips[0]["id"]
        
        if self.trip_id:
            location_data = {
                "latitude": 40.7128 + random.uniform(-0.1, 0.1),
                "longitude": -74.0060 + random.uniform(-0.1, 0.1),
                "speed": random.uniform(0, 80),
                "heading": random.uniform(0, 360)
            }
            
            with self.client.post(f"/api/v1/tracking/trips/{self.trip_id}/location",
                                json=location_data, headers=self.headers,
                                catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Location update failed: {response.status_code}")
    
    @task(1)
    def get_trip_status(self):
        """Get trip status."""
        if not self.access_token:
            return
        
        with self.client.get("/api/v1/tracking/my-trips", headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get trip status failed: {response.status_code}")


# Configure user classes
PafarUser.weight = 10  # Most common user type
AdminUser.weight = 1   # Few admin users
DriverUser.weight = 2  # Some driver users