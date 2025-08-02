"""
Simple test to verify testing infrastructure.
"""
import pytest


def test_basic_math():
    """Test basic functionality."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


@pytest.mark.unit
def test_unit_marker():
    """Test unit marker."""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test integration marker."""
    assert True


def test_string_operations():
    """Test string operations."""
    text = "Hello, World!"
    assert text.lower() == "hello, world!"
    assert text.upper() == "HELLO, WORLD!"
    assert len(text) == 13


def test_list_operations():
    """Test list operations."""
    numbers = [1, 2, 3, 4, 5]
    assert sum(numbers) == 15
    assert max(numbers) == 5
    assert min(numbers) == 1
    assert len(numbers) == 5


def test_dictionary_operations():
    """Test dictionary operations."""
    data = {"name": "John", "age": 30, "city": "New York"}
    assert data["name"] == "John"
    assert data.get("age") == 30
    assert "city" in data
    assert len(data) == 3