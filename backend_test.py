import pytest
from fastapi.testclient import TestClient
import os
import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine

# Set the DATABASE_URL for testing
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

from backend.server import app, database, contact_submissions, metadata

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_contact_form_submission(client):
    """Test POST /api/contact endpoint"""
    # Make sure the table is created
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

    test_data = {
        "name": "Test User",
        "email": "test@example.com",
        "company": "Test Inc.",
        "phone": "1234567890",
        "message": "This is a test message."
    }

    response = client.post("/api/contact", json=test_data)

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify that the data was inserted correctly
    await database.connect()
    query = contact_submissions.select()
    results = await database.fetch_all(query)
    await database.disconnect()

    assert len(results) == 1
    assert results[0]["name"] == "Test User"
    assert results[0]["email"] == "test@example.com"

    # Clean up the test database
    if os.path.exists("./test.db"):
        os.remove("./test.db")

def test_root_endpoint(client):
    """Test GET /api/ endpoint"""
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
