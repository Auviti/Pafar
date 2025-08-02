"""
Comprehensive Load Testing for Pafar Transport Management System
Tests system performance under various load conditions
"""
import asyncio
import time
import statistics
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
import aiohttp
import pytest
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Data class for load test results."""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: List[str]


class LoadTestRunner:
    """Load test runner for API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a single HTTP request and measure response time."""
        start_time = time.time()
        try:
            async with self.session.request(method, f"{self.base_url}{endpoint}", **kwargs) as response:
                end_time = time.time()
                response_data = await response.text()
                
                return {
                    "success": response.status < 400,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "response_data": response_data,
                    "error": None
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "status_code": 0,
                "response_time": end_time - start_time,
                "response_data": None,
                "error": str(e)
            }
    
    async def run_load_test(
        self,
        method: str,
        endpoint: str,
        concurrent_users: int,
        requests_per_user: int,
        **request_kwargs
    ) -> LoadTestResult:
        """Run load test for a specific endpoint."""
        logger.info(f"Starting load test: {method} {endpoint} with {concurrent_users} users, {requests_per_user} requests each")
        
        async def user_session():
            """Simulate a user making multiple requests."""
            results = []
            for _ in range(requests_per_user):
                result = await self.make_request(method, endpoint, **request_kwargs)
                results.append(result)
                # Small delay between requests from same user
                await asyncio.sleep(0.1)
            return results
        
        # Start load test
        start_time = time.time()
        tasks = [user_session() for _ in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Flatten results
        all_results = [result for user_result in user_results for result in user_result]
        
        # Calculate metrics
        total_requests = len(all_results)
        successful_requests = len([r for r in all_results if r["success"]])
        failed_requests = total_requests - successful_requests
        
        response_times = [r["response_time"] for r in all_results if r["success"]]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0
        
        total_duration = end_time - start_time
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0
        error_rate = failed_requests / total_requests if total_requests > 0 else 0
        
        errors = [r["error"] for r in all_results if r["error"]]
        
        result = LoadTestResult(
            endpoint=endpoint,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors[:10]  # Keep only first 10 errors
        )
        
        logger.info(f"Load test completed: {successful_requests}/{total_requests} successful, "
                   f"avg response time: {avg_response_time:.3f}s, RPS: {requests_per_second:.2f}")
        
        return result


@pytest.mark.load_test
class TestSystemLoadPerformance:
    """Load testing for critical system endpoints."""
    
    @pytest.mark.asyncio
    async def test_authentication_load(self):
        """Test authentication endpoints under load."""
        async with LoadTestRunner() as runner:
            # Test user registration load
            registration_data = {
                "json": {
                    "email": f"load_test_user_{int(time.time())}@example.com",
                    "password": "LoadTest123!",
                    "first_name": "Load",
                    "last_name": "Test"
                }
            }
            
            register_result = await runner.run_load_test(
                "POST",
                "/api/v1/auth/register",
                concurrent_users=20,
                requests_per_user=5,
                **registration_data
            )
            
            # Assertions for registration performance
            assert register_result.error_rate < 0.05, f"Registration error rate {register_result.error_rate:.2%} too high"
            assert register_result.avg_response_time < 2.0, f"Registration avg response time {register_result.avg_response_time:.3f}s too slow"
            assert register_result.p95_response_time < 5.0, f"Registration 95th percentile {register_result.p95_response_time:.3f}s too slow"
            
            # Test login load
            login_data = {
                "json": {
                    "email": "existing_user@example.com",
                    "password": "ExistingUser123!"
                }
            }
            
            login_result = await runner.run_load_test(
                "POST",
                "/api/v1/auth/login",
                concurrent_users=50,
                requests_per_user=10,
                **login_data
            )
            
            # Assertions for login performance
            assert login_result.error_rate < 0.10, f"Login error rate {login_result.error_rate:.2%} too high"
            assert login_result.avg_response_time < 1.0, f"Login avg response time {login_result.avg_response_time:.3f}s too slow"
            assert login_result.requests_per_second > 20, f"Login RPS {login_result.requests_per_second:.2f} too low"
    
    @pytest.mark.asyncio
    async def test_trip_search_load(self):
        """Test trip search endpoint under heavy load."""
        async with LoadTestRunner() as runner:
            search_params = {
                "params": {
                    "origin_terminal_id": "550e8400-e29b-41d4-a716-446655440000",
                    "destination_terminal_id": "550e8400-e29b-41d4-a716-446655440001",
                    "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
                }
            }
            
            # Test with increasing load
            load_levels = [10, 25, 50, 100]
            results = []
            
            for concurrent_users in load_levels:
                result = await runner.run_load_test(
                    "GET",
                    "/api/v1/bookings/trips/search",
                    concurrent_users=concurrent_users,
                    requests_per_user=5,
                    **search_params
                )
                results.append(result)
                
                # Performance assertions for each load level
                assert result.error_rate < 0.05, f"Search error rate {result.error_rate:.2%} too high at {concurrent_users} users"
                assert result.avg_response_time < 3.0, f"Search avg response time {result.avg_response_time:.3f}s too slow at {concurrent_users} users"
                
                # Log results
                logger.info(f"Search load test at {concurrent_users} users: "
                           f"RPS={result.requests_per_second:.2f}, "
                           f"avg_time={result.avg_response_time:.3f}s, "
                           f"error_rate={result.error_rate:.2%}")
            
            # Verify performance doesn't degrade too much with increased load
            initial_response_time = results[0].avg_response_time
            final_response_time = results[-1].avg_response_time
            
            degradation_factor = final_response_time / initial_response_time if initial_response_time > 0 else 1
            assert degradation_factor < 3.0, f"Response time degraded by {degradation_factor:.2f}x under load"
    
    @pytest.mark.asyncio
    async def test_booking_creation_load(self):
        """Test booking creation under concurrent load."""
        async with LoadTestRunner() as runner:
            # First, create authentication token
            auth_response = await runner.make_request(
                "POST",
                "/api/v1/auth/login",
                json={
                    "email": "load_test_user@example.com",
                    "password": "LoadTest123!"
                }
            )
            
            if not auth_response["success"]:
                # Create user first
                await runner.make_request(
                    "POST",
                    "/api/v1/auth/register",
                    json={
                        "email": "load_test_user@example.com",
                        "password": "LoadTest123!",
                        "first_name": "Load",
                        "last_name": "Test"
                    }
                )
                
                auth_response = await runner.make_request(
                    "POST",
                    "/api/v1/auth/login",
                    json={
                        "email": "load_test_user@example.com",
                        "password": "LoadTest123!"
                    }
                )
            
            if auth_response["success"]:
                auth_data = json.loads(auth_response["response_data"])
                token = auth_data["access_token"]
                
                booking_data = {
                    "json": {
                        "trip_id": "550e8400-e29b-41d4-a716-446655440002",
                        "seat_numbers": [1],
                        "passenger_details": {
                            "first_name": "Load",
                            "last_name": "Test"
                        }
                    },
                    "headers": {
                        "Authorization": f"Bearer {token}"
                    }
                }
                
                result = await runner.run_load_test(
                    "POST",
                    "/api/v1/bookings/",
                    concurrent_users=20,
                    requests_per_user=3,
                    **booking_data
                )
                
                # Booking creation should handle concurrency well
                assert result.error_rate < 0.20, f"Booking error rate {result.error_rate:.2%} too high"
                assert result.avg_response_time < 5.0, f"Booking avg response time {result.avg_response_time:.3f}s too slow"
    
    @pytest.mark.asyncio
    async def test_real_time_tracking_load(self):
        """Test real-time tracking endpoints under load."""
        async with LoadTestRunner() as runner:
            trip_id = "550e8400-e29b-41d4-a716-446655440003"
            
            # Test location retrieval load
            location_result = await runner.run_load_test(
                "GET",
                f"/api/v1/tracking/trips/{trip_id}/location",
                concurrent_users=100,
                requests_per_user=10
            )
            
            # Real-time endpoints should be very fast
            assert location_result.error_rate < 0.10, f"Location tracking error rate {location_result.error_rate:.2%} too high"
            assert location_result.avg_response_time < 0.5, f"Location tracking avg response time {location_result.avg_response_time:.3f}s too slow"
            assert location_result.requests_per_second > 100, f"Location tracking RPS {location_result.requests_per_second:.2f} too low"
            
            # Test ETA calculation load
            eta_result = await runner.run_load_test(
                "GET",
                f"/api/v1/tracking/trips/{trip_id}/eta",
                concurrent_users=50,
                requests_per_user=5
            )
            
            assert eta_result.error_rate < 0.10, f"ETA calculation error rate {eta_result.error_rate:.2%} too high"
            assert eta_result.avg_response_time < 1.0, f"ETA calculation avg response time {eta_result.avg_response_time:.3f}s too slow"
    
    @pytest.mark.asyncio
    async def test_payment_processing_load(self):
        """Test payment processing under load."""
        async with LoadTestRunner() as runner:
            # Create authenticated session
            auth_response = await runner.make_request(
                "POST",
                "/api/v1/auth/login",
                json={
                    "email": "payment_load_test@example.com",
                    "password": "PaymentLoad123!"
                }
            )
            
            if not auth_response["success"]:
                await runner.make_request(
                    "POST",
                    "/api/v1/auth/register",
                    json={
                        "email": "payment_load_test@example.com",
                        "password": "PaymentLoad123!",
                        "first_name": "Payment",
                        "last_name": "Load"
                    }
                )
                
                auth_response = await runner.make_request(
                    "POST",
                    "/api/v1/auth/login",
                    json={
                        "email": "payment_load_test@example.com",
                        "password": "PaymentLoad123!"
                    }
                )
            
            if auth_response["success"]:
                auth_data = json.loads(auth_response["response_data"])
                token = auth_data["access_token"]
                
                payment_intent_data = {
                    "json": {
                        "booking_id": "550e8400-e29b-41d4-a716-446655440004",
                        "payment_method": "card"
                    },
                    "headers": {
                        "Authorization": f"Bearer {token}"
                    }
                }
                
                result = await runner.run_load_test(
                    "POST",
                    "/api/v1/payments/create-intent",
                    concurrent_users=15,
                    requests_per_user=2,
                    **payment_intent_data
                )
                
                # Payment processing should be reliable but may be slower due to external services
                assert result.error_rate < 0.15, f"Payment intent error rate {result.error_rate:.2%} too high"
                assert result.avg_response_time < 10.0, f"Payment intent avg response time {result.avg_response_time:.3f}s too slow"
    
    @pytest.mark.asyncio
    async def test_admin_dashboard_load(self):
        """Test admin dashboard under load."""
        async with LoadTestRunner() as runner:
            # Create admin session
            admin_auth_response = await runner.make_request(
                "POST",
                "/api/v1/auth/login",
                json={
                    "email": "admin_load_test@example.com",
                    "password": "AdminLoad123!"
                }
            )
            
            if not admin_auth_response["success"]:
                await runner.make_request(
                    "POST",
                    "/api/v1/auth/register",
                    json={
                        "email": "admin_load_test@example.com",
                        "password": "AdminLoad123!",
                        "first_name": "Admin",
                        "last_name": "Load",
                        "role": "admin"
                    }
                )
                
                admin_auth_response = await runner.make_request(
                    "POST",
                    "/api/v1/auth/login",
                    json={
                        "email": "admin_load_test@example.com",
                        "password": "AdminLoad123!"
                    }
                )
            
            if admin_auth_response["success"]:
                auth_data = json.loads(admin_auth_response["response_data"])
                token = auth_data["access_token"]
                
                dashboard_headers = {
                    "headers": {
                        "Authorization": f"Bearer {token}"
                    }
                }
                
                result = await runner.run_load_test(
                    "GET",
                    "/api/v1/admin/dashboard",
                    concurrent_users=10,
                    requests_per_user=5,
                    **dashboard_headers
                )
                
                # Admin dashboard should handle moderate load well
                assert result.error_rate < 0.10, f"Admin dashboard error rate {result.error_rate:.2%} too high"
                assert result.avg_response_time < 2.0, f"Admin dashboard avg response time {result.avg_response_time:.3f}s too slow"


@pytest.mark.stress_test
class TestSystemStressLimits:
    """Stress testing to find system breaking points."""
    
    @pytest.mark.asyncio
    async def test_extreme_concurrent_users(self):
        """Test system behavior with extreme concurrent user load."""
        async with LoadTestRunner() as runner:
            # Gradually increase load until system starts failing
            max_concurrent_users = 500
            step_size = 50
            
            for concurrent_users in range(step_size, max_concurrent_users + 1, step_size):
                logger.info(f"Testing with {concurrent_users} concurrent users")
                
                result = await runner.run_load_test(
                    "GET",
                    "/api/v1/bookings/trips/search",
                    concurrent_users=concurrent_users,
                    requests_per_user=2,
                    params={
                        "origin_terminal_id": "550e8400-e29b-41d4-a716-446655440000",
                        "destination_terminal_id": "550e8400-e29b-41d4-a716-446655440001",
                        "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
                    }
                )
                
                logger.info(f"Results for {concurrent_users} users: "
                           f"Success rate: {(1-result.error_rate):.2%}, "
                           f"Avg response time: {result.avg_response_time:.3f}s, "
                           f"RPS: {result.requests_per_second:.2f}")
                
                # If error rate exceeds 50% or response time exceeds 30s, we've found the breaking point
                if result.error_rate > 0.5 or result.avg_response_time > 30.0:
                    logger.warning(f"System breaking point reached at {concurrent_users} concurrent users")
                    break
                
                # Small delay between stress levels
                await asyncio.sleep(2)
    
    @pytest.mark.asyncio
    async def test_sustained_load_endurance(self):
        """Test system endurance under sustained load."""
        async with LoadTestRunner() as runner:
            # Run sustained load for extended period
            duration_minutes = 5
            concurrent_users = 25
            requests_per_minute = 60
            
            logger.info(f"Starting {duration_minutes}-minute endurance test with {concurrent_users} users")
            
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)
            
            results = []
            
            while time.time() < end_time:
                result = await runner.run_load_test(
                    "GET",
                    "/api/v1/bookings/trips/search",
                    concurrent_users=concurrent_users,
                    requests_per_user=1,
                    params={
                        "origin_terminal_id": "550e8400-e29b-41d4-a716-446655440000",
                        "destination_terminal_id": "550e8400-e29b-41d4-a716-446655440001",
                        "departure_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
                    }
                )
                
                results.append(result)
                
                # Log periodic results
                elapsed_minutes = (time.time() - start_time) / 60
                logger.info(f"Minute {elapsed_minutes:.1f}: "
                           f"Success rate: {(1-result.error_rate):.2%}, "
                           f"Avg response time: {result.avg_response_time:.3f}s")
                
                # Brief pause between test cycles
                await asyncio.sleep(1)
            
            # Analyze endurance results
            total_requests = sum(r.total_requests for r in results)
            total_successful = sum(r.successful_requests for r in results)
            overall_success_rate = total_successful / total_requests if total_requests > 0 else 0
            
            avg_response_times = [r.avg_response_time for r in results if r.successful_requests > 0]
            overall_avg_response_time = statistics.mean(avg_response_times) if avg_response_times else 0
            
            logger.info(f"Endurance test completed: "
                       f"Overall success rate: {overall_success_rate:.2%}, "
                       f"Overall avg response time: {overall_avg_response_time:.3f}s")
            
            # System should maintain good performance throughout the test
            assert overall_success_rate > 0.95, f"Overall success rate {overall_success_rate:.2%} too low"
            assert overall_avg_response_time < 5.0, f"Overall avg response time {overall_avg_response_time:.3f}s too slow"
            
            # Performance shouldn't degrade significantly over time
            if len(avg_response_times) > 1:
                initial_response_time = avg_response_times[0]
                final_response_time = avg_response_times[-1]
                degradation = final_response_time / initial_response_time if initial_response_time > 0 else 1
                
                assert degradation < 2.0, f"Performance degraded by {degradation:.2f}x during endurance test"


def generate_load_test_report(results: List[LoadTestResult]) -> str:
    """Generate a comprehensive load test report."""
    report = []
    report.append("# Load Test Report")
    report.append(f"Generated at: {datetime.utcnow().isoformat()}")
    report.append("")
    
    for result in results:
        report.append(f"## {result.endpoint}")
        report.append(f"- Total Requests: {result.total_requests}")
        report.append(f"- Successful Requests: {result.successful_requests}")
        report.append(f"- Failed Requests: {result.failed_requests}")
        report.append(f"- Success Rate: {(1-result.error_rate):.2%}")
        report.append(f"- Average Response Time: {result.avg_response_time:.3f}s")
        report.append(f"- 95th Percentile Response Time: {result.p95_response_time:.3f}s")
        report.append(f"- 99th Percentile Response Time: {result.p99_response_time:.3f}s")
        report.append(f"- Requests Per Second: {result.requests_per_second:.2f}")
        
        if result.errors:
            report.append("- Sample Errors:")
            for error in result.errors[:5]:
                report.append(f"  - {error}")
        
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    # Run load tests
    pytest.main([
        __file__,
        "-v",
        "-m", "load_test",
        "--tb=short"
    ])