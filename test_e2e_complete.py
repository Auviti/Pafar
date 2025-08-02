#!/usr/bin/env python3
"""
Complete End-to-End Test Runner for Pafar Transport Management System
Executes comprehensive integration tests across all platforms
"""
import os
import sys
import subprocess
import time
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import concurrent.futures
import requests
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('e2e_test_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TestEnvironmentManager:
    """Manages test environment setup and teardown."""
    
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        self.mobile_dir = self.base_dir / "mobile"
        
    def start_backend_server(self):
        """Start the FastAPI backend server."""
        logger.info("Starting backend server...")
        
        # Set environment variables for testing
        env = os.environ.copy()
        env.update({
            'TESTING': 'true',
            'DATABASE_URL': 'sqlite:///./test_pafar.db',
            'REDIS_URL': 'redis://localhost:6379/1',
            'SECRET_KEY': 'test-secret-key-for-e2e-testing',
            'STRIPE_SECRET_KEY': 'sk_test_fake_key_for_testing',
        })
        
        # Start backend server
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=self.backend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.processes.append(backend_process)
        
        # Wait for server to start
        self._wait_for_service("http://localhost:8000/health", timeout=30)
        logger.info("Backend server started successfully")
        
        return backend_process
    
    def start_frontend_server(self):
        """Start the React frontend development server."""
        logger.info("Starting frontend server...")
        
        # Install dependencies if needed
        if not (self.frontend_dir / "node_modules").exists():
            logger.info("Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=self.frontend_dir, check=True)
        
        # Set environment variables
        env = os.environ.copy()
        env.update({
            'REACT_APP_API_URL': 'http://localhost:8000',
            'REACT_APP_WS_URL': 'ws://localhost:8000',
            'NODE_ENV': 'test',
        })
        
        # Start frontend server
        frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=self.frontend_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.processes.append(frontend_process)
        
        # Wait for server to start
        self._wait_for_service("http://localhost:3000", timeout=60)
        logger.info("Frontend server started successfully")
        
        return frontend_process
    
    def setup_mobile_environment(self):
        """Setup mobile testing environment."""
        logger.info("Setting up mobile test environment...")
        
        # Check if Flutter is installed
        try:
            result = subprocess.run(["flutter", "--version"], capture_output=True, text=True)
            logger.info(f"Flutter version: {result.stdout.split()[1] if result.stdout else 'Unknown'}")
        except FileNotFoundError:
            logger.error("Flutter not found. Please install Flutter SDK.")
            return False
        
        # Get dependencies
        subprocess.run(["flutter", "pub", "get"], cwd=self.mobile_dir, check=True)
        
        # Generate mocks
        subprocess.run(
            ["flutter", "packages", "pub", "run", "build_runner", "build", "--delete-conflicting-outputs"],
            cwd=self.mobile_dir,
            check=True
        )
        
        logger.info("Mobile environment setup completed")
        return True
    
    def start_redis_server(self):
        """Start Redis server for caching and real-time features."""
        logger.info("Starting Redis server...")
        
        try:
            # Check if Redis is already running
            response = requests.get("http://localhost:6379", timeout=1)
        except:
            # Start Redis server
            redis_process = subprocess.Popen(
                ["redis-server", "--port", "6379", "--daemonize", "no"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(redis_process)
            time.sleep(2)  # Give Redis time to start
        
        logger.info("Redis server is running")
    
    def _wait_for_service(self, url: str, timeout: int = 30):
        """Wait for a service to become available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code < 500:
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        raise TimeoutError(f"Service at {url} did not become available within {timeout} seconds")
    
    def cleanup(self):
        """Clean up test environment."""
        logger.info("Cleaning up test environment...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except Exception as e:
                logger.warning(f"Error terminating process: {e}")
        
        # Clean up test database
        test_db_path = self.backend_dir / "test_pafar.db"
        if test_db_path.exists():
            test_db_path.unlink()
        
        logger.info("Cleanup completed")


class TestRunner:
    """Runs comprehensive end-to-end tests."""
    
    def __init__(self, env_manager: TestEnvironmentManager):
        self.env_manager = env_manager
        self.test_results = {
            'backend': {},
            'frontend': {},
            'mobile': {},
            'integration': {},
            'performance': {}
        }
    
    def run_backend_tests(self) -> Dict[str, Any]:
        """Run backend integration tests."""
        logger.info("Running backend integration tests...")
        
        results = {}
        
        # Run API integration tests
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_e2e_integration_complete.py", "-v", "--tb=short"],
                cwd=self.env_manager.backend_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            results['api_integration'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Backend API integration tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['api_integration'] = {
                'success': False,
                'output': '',
                'errors': 'Test timeout after 10 minutes',
                'duration': 600
            }
            logger.error("Backend API integration tests timed out")
        
        # Run load tests
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/performance/load_test_complete.py", "-v", "-m", "load_test"],
                cwd=self.env_manager.backend_dir,
                capture_output=True,
                text=True,
                timeout=900  # 15 minutes timeout
            )
            
            results['load_tests'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Backend load tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['load_tests'] = {
                'success': False,
                'output': '',
                'errors': 'Load test timeout after 15 minutes',
                'duration': 900
            }
            logger.error("Backend load tests timed out")
        
        return results
    
    def run_frontend_tests(self) -> Dict[str, Any]:
        """Run frontend end-to-end tests."""
        logger.info("Running frontend E2E tests...")
        
        results = {}
        
        # Run Playwright E2E tests
        try:
            result = subprocess.run(
                ["npm", "run", "test:e2e"],
                cwd=self.env_manager.frontend_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            results['e2e_tests'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Frontend E2E tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['e2e_tests'] = {
                'success': False,
                'output': '',
                'errors': 'E2E test timeout after 10 minutes',
                'duration': 600
            }
            logger.error("Frontend E2E tests timed out")
        
        # Run component integration tests
        try:
            result = subprocess.run(
                ["npm", "run", "test:integration"],
                cwd=self.env_manager.frontend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            results['component_integration'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Frontend component integration tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['component_integration'] = {
                'success': False,
                'output': '',
                'errors': 'Component integration test timeout after 5 minutes',
                'duration': 300
            }
            logger.error("Frontend component integration tests timed out")
        
        return results
    
    def run_mobile_tests(self) -> Dict[str, Any]:
        """Run mobile integration tests."""
        logger.info("Running mobile integration tests...")
        
        results = {}
        
        # Run Flutter integration tests
        try:
            result = subprocess.run(
                ["flutter", "test", "test/integration/complete_app_integration_test.dart"],
                cwd=self.env_manager.mobile_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            results['integration_tests'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Mobile integration tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['integration_tests'] = {
                'success': False,
                'output': '',
                'errors': 'Mobile integration test timeout after 10 minutes',
                'duration': 600
            }
            logger.error("Mobile integration tests timed out")
        
        # Run widget tests
        try:
            result = subprocess.run(
                ["flutter", "test", "--coverage"],
                cwd=self.env_manager.mobile_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            results['widget_tests'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Mobile widget tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['widget_tests'] = {
                'success': False,
                'output': '',
                'errors': 'Widget test timeout after 5 minutes',
                'duration': 300
            }
            logger.error("Mobile widget tests timed out")
        
        return results
    
    def run_cross_platform_tests(self) -> Dict[str, Any]:
        """Run cross-platform integration tests."""
        logger.info("Running cross-platform integration tests...")
        
        results = {}
        
        # Test data consistency across platforms
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_e2e_integration_complete.py::TestCompleteSystemIntegration::test_cross_platform_data_synchronization", "-v"],
                cwd=self.env_manager.backend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            results['data_consistency'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Cross-platform data consistency tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['data_consistency'] = {
                'success': False,
                'output': '',
                'errors': 'Cross-platform test timeout after 5 minutes',
                'duration': 300
            }
            logger.error("Cross-platform tests timed out")
        
        return results
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance and stress tests."""
        logger.info("Running performance tests...")
        
        results = {}
        
        # Run stress tests
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/performance/load_test_complete.py", "-v", "-m", "stress_test"],
                cwd=self.env_manager.backend_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            results['stress_tests'] = {
                'success': result.returncode == 0,
                'output': result.stdout,
                'errors': result.stderr,
                'duration': self._extract_test_duration(result.stdout)
            }
            
            logger.info(f"Performance stress tests: {'PASSED' if result.returncode == 0 else 'FAILED'}")
            
        except subprocess.TimeoutExpired:
            results['stress_tests'] = {
                'success': False,
                'output': '',
                'errors': 'Stress test timeout after 30 minutes',
                'duration': 1800
            }
            logger.error("Performance stress tests timed out")
        
        return results
    
    def _extract_test_duration(self, output: str) -> float:
        """Extract test duration from test output."""
        # This is a simplified extraction - in practice, you'd parse the actual test output format
        import re
        duration_match = re.search(r'(\d+\.?\d*)\s*seconds?', output)
        if duration_match:
            return float(duration_match.group(1))
        return 0.0
    
    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        report = []
        report.append("# Pafar E2E Test Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Summary
        total_tests = 0
        passed_tests = 0
        
        for platform, tests in self.test_results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result.get('success', False):
                    passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report.append("## Summary")
        report.append(f"- Total Tests: {total_tests}")
        report.append(f"- Passed: {passed_tests}")
        report.append(f"- Failed: {total_tests - passed_tests}")
        report.append(f"- Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # Detailed results
        for platform, tests in self.test_results.items():
            if not tests:
                continue
                
            report.append(f"## {platform.title()} Tests")
            
            for test_name, result in tests.items():
                status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
                duration = result.get('duration', 0)
                
                report.append(f"### {test_name.replace('_', ' ').title()}")
                report.append(f"- Status: {status}")
                report.append(f"- Duration: {duration:.2f}s")
                
                if not result.get('success', False) and result.get('errors'):
                    report.append("- Errors:")
                    for line in result['errors'].split('\n')[:10]:  # First 10 lines
                        if line.strip():
                            report.append(f"  {line}")
                
                report.append("")
        
        return "\n".join(report)


def main():
    """Main test execution function."""
    logger.info("Starting comprehensive E2E test suite for Pafar Transport Management System")
    
    env_manager = TestEnvironmentManager()
    test_runner = TestRunner(env_manager)
    
    try:
        # Setup test environment
        logger.info("Setting up test environment...")
        
        # Start Redis server
        env_manager.start_redis_server()
        
        # Start backend server
        backend_process = env_manager.start_backend_server()
        
        # Start frontend server
        frontend_process = env_manager.start_frontend_server()
        
        # Setup mobile environment
        mobile_ready = env_manager.setup_mobile_environment()
        
        # Run tests
        logger.info("Starting test execution...")
        
        # Run backend tests
        test_runner.test_results['backend'] = test_runner.run_backend_tests()
        
        # Run frontend tests
        test_runner.test_results['frontend'] = test_runner.run_frontend_tests()
        
        # Run mobile tests (if environment is ready)
        if mobile_ready:
            test_runner.test_results['mobile'] = test_runner.run_mobile_tests()
        else:
            logger.warning("Mobile environment not ready, skipping mobile tests")
        
        # Run cross-platform tests
        test_runner.test_results['integration'] = test_runner.run_cross_platform_tests()
        
        # Run performance tests
        test_runner.test_results['performance'] = test_runner.run_performance_tests()
        
        # Generate and save report
        report = test_runner.generate_report()
        
        with open('e2e_test_report.md', 'w') as f:
            f.write(report)
        
        logger.info("Test report saved to e2e_test_report.md")
        print(report)
        
        # Determine overall success
        all_passed = all(
            result.get('success', False)
            for platform_tests in test_runner.test_results.values()
            for result in platform_tests.values()
        )
        
        if all_passed:
            logger.info("🎉 All E2E tests passed!")
            return 0
        else:
            logger.error("❌ Some E2E tests failed. Check the report for details.")
            return 1
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1
    
    finally:
        # Cleanup
        env_manager.cleanup()


if __name__ == "__main__":
    sys.exit(main())