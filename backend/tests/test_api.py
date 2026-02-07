import pytest
from app import create_app
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(TestConfig)

    with app.app_context():
        pass

    with app.test_client() as client:
        yield client


def test_root_route(client):
    response = client.get('/')
    assert response.status_code == 200


def test_health_check(client):
    response = client.get('/api/health')

    assert response.status_code != 500