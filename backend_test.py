import pytest
from fastapi.testclient import TestClient
import os

@pytest.fixture
def client():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("DB_NAME", "test_db")
    from backend.server import app
    with TestClient(app) as c:
        yield c

def test_root_endpoint(client):
    """Test GET /api/ endpoint"""
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
