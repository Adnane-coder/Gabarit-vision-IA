from fastapi.testclient import TestClient

from app.main import app


def test_camera_status():
    with TestClient(app) as client:
        response = client.get("/api/v1/camera/status")
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is True
    assert body["device"] == "Mock Camera"


def test_camera_capture():
    with TestClient(app) as client:
        response = client.post("/api/v1/camera/capture")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["image_id"].startswith("IMG-")
