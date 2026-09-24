from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "42-evaluation-explorer"


def test_index() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "42 Evaluation Explorer" in response.text
