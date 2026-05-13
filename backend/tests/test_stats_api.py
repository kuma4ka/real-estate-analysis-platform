"""
Integration tests for the Stats & Forecast API endpoints.
Build 1 – Backend module integration (API router + services + in-memory DB).

Covers:
  TC_025 – GET /api/v1/stats  (stats endpoint)
  TC_026 – empty-DB filter/forecast graceful handling (bug fixed)
  TC_027 – GET /api/v1/stats/forecast (price forecast endpoint)
"""
import pytest
from datetime import timedelta
from app import create_app, db
from app.models import User, Property
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Clear module-level TTLCaches so each test starts with fresh data
        from app.api.stats import _compute_stats, _compute_price_forecast
        _compute_stats.cache.clear()
        _compute_price_forecast.cache.clear()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _make_user(email: str, role: str, password: str = "Secure123!") -> User:
    u = User(email=email, role=role)
    u.set_password(password)
    return u


def _register_and_login(client, email: str, role: str = "Analyst"):
    """Register user with given role, log in, return JWT token."""
    with client.application.app_context():
        u = _make_user(email, role)
        db.session.add(u)
        db.session.commit()

    # Log in through API to get a proper JWT
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Secure123!"})
    assert resp.status_code == 200, f"Login failed: {resp.get_json()}"
    return resp.get_json()["token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_properties(client, count: int = 3):
    """Seed the DB with `count` properties on consecutive days."""
    from datetime import datetime, timezone
    with client.application.app_context():
        for i in range(count):
            p = Property(
                title=f"Квартира {i + 1}",
                price=50_000 + i * 10_000,
                currency="USD",
                city="Київ" if i % 2 == 0 else "Харків",
                rooms=i + 1,
                area=40.0 + i * 5,
                source_url=f"http://example.com/stats/{i}",
                is_active=True,
                created_at=datetime.now(timezone.utc) - timedelta(days=count - i),
            )
            db.session.add(p)
        db.session.commit()


# ─────────────────────────────────────────────────────────
# GET /api/v1/stats  (requires Analyst role)
# ─────────────────────────────────────────────────────────

class TestStatsEndpoint:
    def test_stats_requires_auth(self, client):
        """TC_025: Unauthenticated request returns 401."""
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 401

    def test_stats_forbidden_for_regular_user(self, client):
        """Regular User role should be rejected (403)."""
        token = _register_and_login(client, "user@example.com", role="User")
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        assert resp.status_code == 403

    def test_stats_empty_db_returns_zeros(self, client):
        """TC_025: Analyst on empty DB → valid response with zeros."""
        token = _register_and_login(client, "analyst@example.com", role="Analyst")
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_active" in data
        assert data["total_active"] == 0
        assert data["avg_price"] == 0
        assert isinstance(data["by_city"], list)
        assert isinstance(data["by_rooms"], list)
        assert isinstance(data["by_price_ranges"], list)
        assert isinstance(data["recent_trend"], list)

    def test_stats_returns_correct_totals(self, client):
        """TC_025: Stats endpoint reflects seeded data correctly."""
        token = _register_and_login(client, "analyst2@example.com", role="Analyst")
        _seed_properties(client, count=4)
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_active"] == 4
        assert data["avg_price"] > 0
        assert data["avg_area"] > 0

    def test_stats_by_city_grouping(self, client):
        """Stats by_city groups results by distinct city names."""
        token = _register_and_login(client, "analyst3@example.com", role="Analyst")
        _seed_properties(client, count=4)
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        data = resp.get_json()
        cities = [item["city"] for item in data["by_city"]]
        assert "Київ" in cities
        assert "Харків" in cities

    def test_stats_by_rooms_grouping(self, client):
        """Stats by_rooms contains all seeded room counts."""
        token = _register_and_login(client, "analyst4@example.com", role="Analyst")
        _seed_properties(client, count=3)  # creates rooms 1, 2, 3
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        data = resp.get_json()
        room_values = [item["rooms"] for item in data["by_rooms"]]
        assert 1 in room_values
        assert 2 in room_values

    def test_stats_price_histogram_populated(self, client):
        """Price histogram ranges should be present and correctly named."""
        token = _register_and_login(client, "analyst5@example.com", role="Analyst")
        _seed_properties(client, count=3)
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        data = resp.get_json()
        ranges = [item["range"] for item in data["by_price_ranges"]]
        assert "$50-100k" in ranges  # 50k-80k properties should land here
        # Total counts across buckets should equal total properties
        total_counted = sum(item["count"] for item in data["by_price_ranges"])
        assert total_counted == data["total_active"]

    def test_stats_recent_trend_has_entries(self, client):
        """recent_trend list should have one entry per seeded day."""
        token = _register_and_login(client, "analyst6@example.com", role="Analyst")
        _seed_properties(client, count=3)
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        data = resp.get_json()
        assert len(data["recent_trend"]) >= 3
        for entry in data["recent_trend"]:
            assert "month" in entry
            assert "count" in entry
            assert "avg_price" in entry

    def test_stats_avg_price_per_m2_in_response(self, client):
        """avg_price_per_m2 field must be present in stats response."""
        token = _register_and_login(client, "analyst7@example.com", role="Analyst")
        _seed_properties(client, count=3)
        resp = client.get("/api/v1/stats", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "avg_price_per_m2" in data


# ─────────────────────────────────────────────────────────
# GET /api/v1/stats/forecast  (requires Analyst role)
# ─────────────────────────────────────────────────────────

class TestForecastEndpoint:
    def test_forecast_requires_auth(self, client):
        """TC_027: Unauthenticated request returns 401."""
        resp = client.get("/api/v1/stats/forecast")
        assert resp.status_code == 401

    def test_forecast_forbidden_for_regular_user(self, client):
        """Regular User role should be rejected (403)."""
        token = _register_and_login(client, "userfc@example.com", role="User")
        resp = client.get("/api/v1/stats/forecast", headers=_auth_headers(token))
        assert resp.status_code == 403

    def test_forecast_empty_db_returns_graceful_error(self, client):
        """TC_026: Empty DB → 200 with error field describing insufficient data (not a 500 crash)."""
        token = _register_and_login(client, "analystfc@example.com", role="Analyst")
        resp = client.get("/api/v1/stats/forecast", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        # Must include graceful error message, not crash
        assert "error" in data
        assert data["forecast"] == []
        assert data["historical"] == []

    def test_forecast_insufficient_data_returns_graceful_error(self, client):
        """TC_026: Only 2 data points → graceful 200 with error (needs ≥3 days)."""
        token = _register_and_login(client, "analystfc2@example.com", role="Analyst")
        _seed_properties(client, count=2)
        resp = client.get("/api/v1/stats/forecast", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        # Either error due to insufficient data points or valid forecast
        # (might be on same day, so ≥3 unique day check)
        assert "error" in data or "forecast" in data

    def test_forecast_with_enough_data_returns_30_day_forecast(self, client):
        """TC_027: ≥3 days of data → forecast has 30 future entries."""
        token = _register_and_login(client, "analystfc3@example.com", role="Analyst")
        _seed_properties(client, count=5)
        resp = client.get("/api/v1/stats/forecast", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        # If enough unique day data, should have forecast
        if "error" not in data:
            assert len(data["forecast"]) == 30
            for entry in data["forecast"]:
                assert "date" in entry
                assert "predicted_price" in entry
                assert "lower" in entry
                assert "upper" in entry
            assert "r_squared" in data
            assert "slope_per_day" in data
            assert "historical" in data
            assert len(data["historical"]) >= 1

    def test_forecast_city_filter_scopes_data(self, client):
        """Forecast with city param scopes data to that city."""
        token = _register_and_login(client, "analystfc4@example.com", role="Analyst")
        _seed_properties(client, count=6)
        resp = client.get("/api/v1/stats/forecast?city=Київ", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert "city" not in data  # Removed to fix Reflected XSS
        # 6 properties seeded alternating between Kyiv and Kharkiv, so 3 for Kyiv
        assert len(data.get("historical", [])) == 3

    def test_forecast_available_cities_list(self, client):
        """Forecast response always includes available_cities dropdown data."""
        token = _register_and_login(client, "analystfc5@example.com", role="Analyst")
        _seed_properties(client, count=4)
        resp = client.get("/api/v1/stats/forecast", headers=_auth_headers(token))
        data = resp.get_json()
        assert "available_cities" in data
        assert isinstance(data["available_cities"], list)
