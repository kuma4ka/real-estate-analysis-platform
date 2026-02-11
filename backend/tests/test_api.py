import pytest
from app import create_app, db
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_health_check(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok', 'service': 'real-estate-backend'}


def test_get_properties(client):
    response = client.get('/api/v1/properties')
    assert response.status_code == 200

    assert 'data' in response.json
    assert 'meta' in response.json
    assert isinstance(response.json['data'], list)