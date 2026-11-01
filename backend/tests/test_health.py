import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "application": "DocMind API",
        "version": "0.1.0",
    }
