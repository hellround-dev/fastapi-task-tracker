from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_task():
    response = client.post("/tasks", json = {"title": "Clean a house", "is_done": False})

    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "Clean a house"
    assert data["is_done"] is False
    assert "id" in data


def test_get_not_exists():
    response = client.get("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Задача с таким id не найдена"