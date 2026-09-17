from fastapi.testclient import TestClient

from app.main import app


def test_run_inspection():
    with TestClient(app) as client:
        response = client.post("/api/v1/inspection/run", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"] in ("PASS", "FAIL")
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["inspection_id"].startswith("INS-2026-")
    assert isinstance(body["defects"], list)
    assert body["processing_time_ms"] >= 0
