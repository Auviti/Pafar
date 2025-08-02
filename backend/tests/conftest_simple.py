"""
Simple pytest configuration for basic testing.
"""
import pytest


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key: str):
            return self.data.get(key)
        
        async def setex(self, key: str, time, value):
            self.data[key] = value
            return True
        
        async def delete(self, key: str):
            if key in self.data:
                del self.data[key]
                return True
            return False
        
        async def exists(self, key: str):
            return key in self.data
    
    return MockRedis()


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "security: Security tests")