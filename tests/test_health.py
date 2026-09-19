import os

os.environ.setdefault('ML_CLIENT_ID', 'test-client')
os.environ.setdefault('ML_REDIRECT_URI', 'https://example.com/callback')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test_connector.db')

from fastapi.testclient import TestClient

from main import app


def test_health():
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
