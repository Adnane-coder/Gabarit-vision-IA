from fastapi.testclient import TestClient

from app.main import app


def test_ai_status():
    with TestClient(app) as client:
        response = client.get("/api/v1/ai/status")
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["mode"] == "mock"
    assert body["model_name"] == "inspection-model"
