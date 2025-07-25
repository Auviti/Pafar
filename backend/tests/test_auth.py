import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.core.database import get_session_factory
from app.models.user import User, UserType
from app.api.auth import hash_password
from uuid import uuid4

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def test_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="function")
async def db_session():
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session

@pytest.mark.anyio
async def test_register_and_login(test_client, db_session):
    # Register a new user
    payload = {
        "email": "testuser@example.com",
        "phone": "+12345678901",
        "full_name": "Test User",
        "password": "Password123",
        "user_type": "customer"
    }
    resp = await test_client.post("/auth/register", json=payload)
    assert resp.status_code == status.HTTP_200_OK, resp.text
    data = resp.json()
    assert data["email"] == payload["email"]
    assert data["is_verified"] is False

    # Try registering with the same email
    resp2 = await test_client.post("/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST

    # Manually verify the user for login
    user = await db_session.get(User, data["id"])
    user.is_verified = True
    await db_session.commit()

    # Login with correct credentials
    login_data = {"username": payload["email"], "password": payload["password"]}
    resp3 = await test_client.post("/auth/login", data=login_data)
    assert resp3.status_code == status.HTTP_200_OK, resp3.text
    token = resp3.json()["access_token"]
    assert token

    # Login with wrong password
    resp4 = await test_client.post("/auth/login", data={"username": payload["email"], "password": "wrongpass"})
    assert resp4.status_code == status.HTTP_400_BAD_REQUEST

    # Login with unverified user
    payload2 = payload.copy()
    payload2["email"] = "unverified@example.com"
    resp5 = await test_client.post("/auth/register", json=payload2)
    assert resp5.status_code == status.HTTP_200_OK
    resp6 = await test_client.post("/auth/login", data={"username": payload2["email"], "password": payload2["password"]})
    assert resp6.status_code == status.HTTP_403_FORBIDDEN

    # Access profile with JWT
    headers = {"Authorization": f"Bearer {token}"}
    resp7 = await test_client.get("/auth/me", headers=headers)
    assert resp7.status_code == status.HTTP_200_OK
    assert resp7.json()["email"] == payload["email"]

    # Access profile with invalid JWT
    resp8 = await test_client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp8.status_code == status.HTTP_401_UNAUTHORIZED 