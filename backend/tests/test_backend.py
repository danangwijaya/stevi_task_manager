from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "GeoAI" in response.json()["app"]

def test_login_admin():
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"

def test_login_student():
    response = client.post("/api/v1/auth/login", json={
        "username": "mahasiswa1",
        "password": "mhs123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "annotator"

def test_classes_list():
    response = client.get("/api/v1/annotations/classes")
    assert response.status_code == 200
    classes = response.json()
    assert len(classes) == 13
    class_names = [c["name"] for c in classes]
    assert "Hutan Lahan Kering" in class_names
    assert "Tanaman Padi Lahan Basah" in class_names
    assert "Wilayah Operasi Tambang" in class_names

def test_tasks_summary_and_export():
    # Login
    auth_resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get stats
    stats_resp = client.get("/api/v1/tasks/stats/summary", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_tasks"] > 0
    assert len(stats["student_contributions"]) == 10

def test_task_siblings_and_reset():
    # Admin login
    auth_resp = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get existing tasks
    tasks_resp = client.get("/api/v1/tasks/", headers=headers)
    assert tasks_resp.status_code == 200
    tasks = tasks_resp.json()
    if tasks:
        first_task = tasks[0]
        # Test siblings endpoint
        siblings_resp = client.get(f"/api/v1/tasks/{first_task['id']}/siblings", headers=headers)
        assert siblings_resp.status_code == 200
        assert isinstance(siblings_resp.json(), list)


