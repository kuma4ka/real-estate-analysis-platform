import pytest
from app import create_app, db
from app.models import User
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


VALID_REGISTER_PAYLOAD = {
    "email": "test@example.com",
    "password": "Secure123!"
}


class TestRegister:
    def test_register_success(self, client):
        resp = client.post('/api/v1/auth/register', json=VALID_REGISTER_PAYLOAD)
        assert resp.status_code == 201
        data = resp.get_json()
        assert 'token' in data
        assert data['user']['email'] == 'test@example.com'

    def test_register_duplicate_email(self, client):
        client.post('/api/v1/auth/register', json=VALID_REGISTER_PAYLOAD)
        resp = client.post('/api/v1/auth/register', json=VALID_REGISTER_PAYLOAD)
        assert resp.status_code == 409

    def test_register_invalid_email(self, client):
        resp = client.post('/api/v1/auth/register', json={
            "email": "not-an-email",
            "password": "Secure123!"
        })
        assert resp.status_code == 400

    def test_register_weak_password_no_uppercase(self, client):
        resp = client.post('/api/v1/auth/register', json={
            "email": "test2@example.com",
            "password": "secure123!"
        })
        assert resp.status_code == 400

    def test_register_weak_password_no_digit(self, client):
        resp = client.post('/api/v1/auth/register', json={
            "email": "test2@example.com",
            "password": "SecurePass!"
        })
        assert resp.status_code == 400

    def test_register_weak_password_no_special(self, client):
        resp = client.post('/api/v1/auth/register', json={
            "email": "test2@example.com",
            "password": "Secure123"
        })
        assert resp.status_code == 400

    def test_register_no_body(self, client):
        resp = client.post('/api/v1/auth/register', data='not-json',
                           content_type='text/plain')
        assert resp.status_code in (400, 415)


class TestLogin:
    def test_login_success(self, client):
        client.post('/api/v1/auth/register', json=VALID_REGISTER_PAYLOAD)
        resp = client.post('/api/v1/auth/login', json=VALID_REGISTER_PAYLOAD)
        assert resp.status_code == 200
        assert 'token' in resp.get_json()

    def test_login_wrong_password(self, client):
        client.post('/api/v1/auth/register', json=VALID_REGISTER_PAYLOAD)
        resp = client.post('/api/v1/auth/login', json={
            "email": "test@example.com",
            "password": "WrongPass1!"
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/v1/auth/login', json={
            "email": "nobody@example.com",
            "password": "Whatever1!"
        })
        assert resp.status_code == 401

    def test_login_no_body(self, client):
        resp = client.post('/api/v1/auth/login', data='', content_type='text/plain')
        assert resp.status_code in (400, 415)


class TestMe:
    def _get_token(self, client):
        client.post('/api/v1/auth/register', json=VALID_REGISTER_PAYLOAD)
        resp = client.post('/api/v1/auth/login', json=VALID_REGISTER_PAYLOAD)
        return resp.get_json()['token']

    def test_get_me_authenticated(self, client):
        token = self._get_token(client)
        resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        assert resp.get_json()['email'] == 'test@example.com'

    def test_get_me_no_token(self, client):
        resp = client.get('/api/v1/auth/me')
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get('/api/v1/auth/me',
                          headers={'Authorization': 'Bearer invalid.token.here'})
        assert resp.status_code == 401
