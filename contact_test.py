import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

@pytest.fixture
def client():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("MONGO_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("DB_NAME", "test_db")
    from backend.server import app
    with TestClient(app) as c:
        yield c

@patch('backend.server.send_email')
def test_contact_form(mock_send_email, client):
    """Test POST /api/contact endpoint"""
    mock_send_email.return_value = {"status": "success", "message": "Nachricht erfolgreich gesendet"}

    test_data = {
        "name": "Max Mustermann",
        "email": "max.mustermann@example.com",
        "company": "Mustermann GmbH",
        "phone": "+49 123 456789",
        "message": "Dies ist eine Testnachricht für die Kontaktformular-Funktionalität."
    }

    response = client.post("/api/contact", json=test_data)

    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Nachricht erfolgreich gesendet"}
    mock_send_email.assert_called_once()
