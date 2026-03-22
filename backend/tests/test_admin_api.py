"""
Integration tests for the Admin System endpoint.
Build 1 – Backend module integration: admin blueprint + metrics + DB.

Covers:
  TC_028 – GET /api/v1/admin/system (system metrics)
"""
import pytest
from app import create_app, db
from app.models import User, Property
from config import TestConfig
from datetime import datetime, timezone


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _create_user(client, email: str, role: str) -> str:
    """Create a user with a given role directly in DB, return JWT from login."""
    with client.application.app_context():
        u = User(email=email, role=role)
        u.set_password("Secure123!")
        db.session.add(u)
        db.session.commit()

    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Secure123!"})
    assert resp.status_code == 200
    return resp.get_json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAdminSystemEndpoint:
    def test_system_requires_auth(self, client):
        """TC_028: No token → 401 Unauthorized."""
        resp = client.get("/api/v1/admin/system")
        assert resp.status_code == 401

    def test_system_forbidden_for_analyst(self, client):
        """Analyst role should NOT be able to access admin/system (403)."""
        token = _create_user(client, "analyst@admin.com", "Analyst")
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        assert resp.status_code == 403

    def test_system_forbidden_for_regular_user(self, client):
        """Regular User role should NOT be able to access admin/system (403)."""
        token = _create_user(client, "user@admin.com", "User")
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        assert resp.status_code == 403

    def test_system_accessible_for_admin(self, client):
        """TC_028: Admin role → 200 with all expected fields in response."""
        token = _create_user(client, "admin@admin.com", "Admin")
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_users" in data
        assert "total_properties" in data
        assert "active_properties" in data
        assert "role_distribution" in data
        assert "server_uptime_seconds" in data
        assert "total_requests_today" in data
        assert "db_status" in data

    def test_system_db_status_connected(self, client):
        """DB status field should report 'Connected' when using in-memory SQLite."""
        token = _create_user(client, "admin2@admin.com", "Admin")
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        data = resp.get_json()
        assert data["db_status"] == "Connected"

    def test_system_uptime_positive(self, client):
        """Server uptime must be a positive number."""
        token = _create_user(client, "admin3@admin.com", "Admin")
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        data = resp.get_json()
        assert data["server_uptime_seconds"] > 0

    def test_system_total_users_reflects_db(self, client):
        """TC_028: total_users count must match actual users in DB."""
        # Create 3 users including the admin
        _create_user(client, "admin4@admin.com", "Admin")
        _create_user(client, "extra1@admin.com", "User")
        _create_user(client, "extra2@admin.com", "Analyst")

        token = client.post("/api/v1/auth/login", json={
            "email": "admin4@admin.com", "password": "Secure123!"
        }).get_json()["token"]

        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        data = resp.get_json()
        assert data["total_users"] == 3

    def test_system_role_distribution_has_all_roles(self, client):
        """role_distribution has entries for Admin, Analyst, User, Guest keys."""
        token = _create_user(client, "admin5@admin.com", "Admin")
        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        data = resp.get_json()
        role_dist = data["role_distribution"]
        assert "Admin" in role_dist
        assert "Analyst" in role_dist
        assert "User" in role_dist
        assert "Guest" in role_dist

    def test_system_property_counts_reflect_db(self, client):
        """active_properties and total_properties match seeded data."""
        token = _create_user(client, "admin6@admin.com", "Admin")
        with client.application.app_context():
            p1 = Property(
                title="Active Apt",
                price=60_000,
                currency="USD",
                is_active=True,
                source_url="http://example.com/admin/1",
                created_at=datetime.now(timezone.utc),
            )
            p2 = Property(
                title="Inactive Apt",
                price=40_000,
                currency="USD",
                is_active=False,
                source_url="http://example.com/admin/2",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add_all([p1, p2])
            db.session.commit()

        resp = client.get("/api/v1/admin/system", headers=_auth(token))
        data = resp.get_json()
        assert data["total_properties"] == 2
        assert data["active_properties"] == 1
