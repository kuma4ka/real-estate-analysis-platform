"""
System E2E Tests for Practical Work 4
Builds on REST APIs (Black Box logic) verifying security, edge cases, and rate limiters.
Matches document test IDs: TC_013 to TC_022.
"""
import pytest
from datetime import datetime, timezone
import json

from app import create_app, db
from app.models import User, Property
from config import TestConfig


class SystemTestConfig(TestConfig):
    # Required to trigger Flask-Limiter in testing mode
    RATELIMIT_ENABLED = True


@pytest.fixture
def client():
    # Load app with Rate Limiting enabled explicitly
    app = create_app(SystemTestConfig)
    
    with app.app_context():
        # Force limiter on even if testing = True
        from app import limiter
        limiter.enabled = True
        # Clear limiter memory storage
        limiter.reset()
        
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _login(client, email: str, password: str = "Secure123!") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if resp.status_code == 200:
        return resp.get_json()["token"]
    return ""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestSystemE2E:
    # ─── REGISTRATION & AUTH SECURITY ──────────────────────────────────────────

    def test_TC_013_registration_short_pass_rejected(self, client):
        """TC_013: Password="A1!" -> 400 Validation Error (too short)"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "short@test.com", "password": "A1!"
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert "password" in data["errors"]
        assert "least 8 characters long" in data["errors"]["password"][0]

    def test_TC_014_registration_no_digit(self, client):
        """TC_014: Password="Password!" -> 400 Validation Error (no digit)"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "nodigit@test.com", "password": "Password!"
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert "password" in data["errors"]
        assert "least one digit" in data["errors"]["password"][0]

    def test_TC_015_registration_no_upper(self, client):
        """TC_015: Password="pass123!" -> 400 Validation Error (no uppercase)"""
        resp = client.post("/api/v1/auth/register", json={
            "email": "noupper@test.com", "password": "pass123!"
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert "password" in data["errors"]
        assert "uppercase letter" in data["errors"]["password"][0]

    def test_TC_016_rate_limit_registration(self, client):
        """TC_016: 6th identical IP request to /register -> 429 Too Many Requests"""
        endpoint = "/api/v1/auth/register"
        for i in range(5):
            r = client.post(endpoint, json={
                "email": f"limit{i}@test.com", "password": "ValidPass123!"
            })
            # Allow 201 Created for the 5 successful hits
            assert r.status_code == 201

        # 6th should be locked
        r6 = client.post(endpoint, json={
            "email": "limit6@test.com", "password": "ValidPass123!"
        })
        assert r6.status_code == 429
        data = r6.get_json()
        # Flask limiter default error response is HTML via abort(429) or JSON if configured
        # But we mostly verify the status code.

    def test_TC_017_login_consecutive_fails_lockout(self, client):
        """TC_017: 5 bad auths -> Account Locked (429)"""
        # Seed user
        client.post("/api/v1/auth/register", json={
            "email": "lockout@test.com", "password": "ValidPass123!"
        })
        
        for _ in range(5):
            r = client.post("/api/v1/auth/login", json={
                "email": "lockout@test.com", "password": "WrongPassword!"
            })
            assert r.status_code == 401

        r6 = client.post("/api/v1/auth/login", json={
            "email": "lockout@test.com", "password": "WrongPassword!"
        })
        assert r6.status_code == 429
        assert "temporarily locked" in r6.get_json()["message"]

    # ─── PROPERTIES ENDPOINT VALIDATION ──────────────────────────────────────────

    def test_TC_018_properties_negative_price(self, client):
        """TC_018: price_min=-100 -> 400 Bad Request"""
        resp = client.get("/api/v1/properties?price_min=-100")
        assert resp.status_code == 400
        assert "cannot be negative" in resp.get_json()["message"]

    def test_TC_019_properties_reversed_prices(self, client):
        """TC_019: min=10k, max=5k -> Empty Array (or 400). Here empty array []"""
        with client.application.app_context():
            p = Property(
                title="Apt", price=7500, currency="USD", city="Kyiv", 
                is_active=True, source_url="http://test.com/1", created_at=datetime.now(timezone.utc)
            )
            db.session.add(p)
            db.session.commit()

        resp = client.get("/api/v1/properties?price_min=10000&price_max=5000")
        assert resp.status_code == 200
        assert resp.get_json()["data"] == []

    def test_TC_020_properties_inject_auth(self, client):
        """TC_020: Fake JWT token in Header -> 401 Unauthorized"""
        # We test auth injection by hitting an endpoint requiring valid auth, e.g., auth/me
        # Or an endpoint requiring User auth (though properties is publicly visible unless they access something specific).
        # Let's test the /admin/system endpoint with fake auth or the /auth/me for raw token injection check.
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer FakeSpoofedToken123"})
        assert resp.status_code == 401
        assert "Invalid token" in resp.get_json()["message"]

    # ─── FORECAST & SYSTEM LOGIC ───────────────────────────────────────────────

    def test_TC_021_forecast_insufficient_data(self, client):
        """TC_021: GET /stats/forecast < 3 days -> graceful 'Not enough historical data' error field"""
        # Register an Analyst to access the route
        client.post("/api/v1/auth/register", json={
            "email": "analyst@test.com", "password": "ValidPass123!"
        })
        with client.application.app_context():
            user = User.query.filter_by(email="analyst@test.com").first()
            user.role = "Analyst"
            db.session.commit()
            
        token = _login(client, "analyst@test.com", "ValidPass123!")
        assert token

        resp = client.get("/api/v1/stats/forecast", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "error" in data
        assert "Not enough historical data" in data["error"]

    def test_TC_022_system_endpoint_no_role(self, client):
        """TC_022: GET /admin/system with User role -> 403 Forbidden"""
        client.post("/api/v1/auth/register", json={
            "email": "user@test.com", "password": "ValidPass123!"
        })
        token = _login(client, "user@test.com", "ValidPass123!")
        
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        assert resp.status_code == 403
