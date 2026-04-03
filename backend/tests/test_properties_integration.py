import pytest
from datetime import datetime, timezone
from app import create_app, db
from app.models import User, Property
from config import TestConfig


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def _create_and_login(client, email: str, role: str = "User") -> str:
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


def _seed_properties(client, *, cities=None, count_per_city=5):
    if cities is None:
        cities = ["Київ"]
    with client.application.app_context():
        idx = 0
        for city in cities:
            for i in range(count_per_city):
                p = Property(
                    title=f"Apartment {city} {i}",
                    price=30_000 + idx * 1_000,
                    currency="USD",
                    city=city,
                    rooms=1 + (i % 3),
                    area=40.0,
                    is_active=True,
                    source_url=f"http://example.com/pi/{idx}",
                    created_at=datetime.now(timezone.utc),
                )
                db.session.add(p)
                idx += 1
        db.session.commit()


class TestFullAuthLoginFlow:
    def test_register_then_login_then_get_me(self, client):
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": "flow@test.com", "password": "Secure123!"
        })
        assert reg_resp.status_code == 201
        reg_data = reg_resp.get_json()
        assert "token" in reg_data
        assert reg_data["user"]["email"] == "flow@test.com"

        login_resp = client.post("/api/v1/auth/login", json={
            "email": "flow@test.com", "password": "Secure123!"
        })
        assert login_resp.status_code == 200
        token = login_resp.get_json()["token"]

        me_resp = client.get("/api/v1/auth/me", headers=_auth(token))
        assert me_resp.status_code == 200
        assert me_resp.get_json()["email"] == "flow@test.com"

    def test_login_increments_failed_attempts(self, client):
        with client.application.app_context():
            u = User(email="lockme@test.com", role="User")
            u.set_password("Secure123!")
            db.session.add(u)
            db.session.commit()

        for _ in range(3):
            resp = client.post("/api/v1/auth/login", json={
                "email": "lockme@test.com", "password": "WrongPass1!"
            })
            assert resp.status_code == 401

        with client.application.app_context():
            user = User.query.filter_by(email="lockme@test.com").first()
            assert user.failed_login_attempts == 3

    def test_account_lockout_after_5_bad_attempts(self, client):
        with client.application.app_context():
            u = User(email="lockout@test.com", role="User")
            u.set_password("Secure123!")
            db.session.add(u)
            db.session.commit()

        for _ in range(5):
            client.post("/api/v1/auth/login", json={
                "email": "lockout@test.com", "password": "WrongPass1!"
            })

        resp = client.post("/api/v1/auth/login", json={
            "email": "lockout@test.com", "password": "WrongPass1!"
        })
        assert resp.status_code == 429


class TestPropertiesIntegration:
    def test_filter_on_empty_db_returns_empty_not_crash(self, client):
        resp = client.get("/api/v1/properties?city=Kyiv")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"] == []
        assert data["meta"]["total_items"] == 0

    def test_pagination_page2_returns_second_slice(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=15)
        resp = client.get("/api/v1/properties?page=2&per_page=10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["meta"]["page"] == 2
        assert len(body["data"]) == 5
        assert body["meta"]["total_items"] == 15

    def test_pagination_beyond_last_page_returns_empty(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=5)
        resp = client.get("/api/v1/properties?page=999&per_page=10")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"] == []

    def test_filter_with_english_alias_kyiv_resolves(self, client):
        _seed_properties(client, cities=["Київ", "Харків"], count_per_city=3)
        resp = client.get("/api/v1/properties?city=Kyiv")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) == 3
        for item in data:
            assert "Київ" in item["city"]

    def test_filter_by_rooms(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=6)
        resp = client.get("/api/v1/properties?rooms=1")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) > 0
        for item in data:
            assert item["rooms"] == 1

    def test_sort_newest_default(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=5)
        resp = client.get("/api/v1/properties?sort=newest")
        assert resp.status_code == 200
        items = resp.get_json()["data"]
        assert len(items) > 0

    def test_sort_by_price_ascending(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=5)
        resp = client.get("/api/v1/properties?sort=cheapest")
        assert resp.status_code == 200
        prices = [item["price"] for item in resp.get_json()["data"]]
        assert prices == sorted(prices)

    def test_sort_by_price_descending(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=5)
        resp = client.get("/api/v1/properties?sort=expensive")
        assert resp.status_code == 200
        prices = [item["price"] for item in resp.get_json()["data"]]
        assert prices == sorted(prices, reverse=True)

    def test_authenticated_user_sees_source_url(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=1)
        token = _create_and_login(client, "auth_user@test.com")
        resp = client.get("/api/v1/properties", headers=_auth(token))
        assert resp.status_code == 200
        items = resp.get_json()["data"]
        assert items[0]["source_url"] is not None

    def test_guest_source_url_hidden(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=2)
        resp = client.get("/api/v1/properties")
        assert resp.status_code == 200
        for item in resp.get_json()["data"]:
            assert item["source_url"] is None

    def test_property_detail_returns_correct_data(self, client):
        with client.application.app_context():
            p = Property(
                title="Detail Test",
                price=75_000,
                currency="USD",
                city="Одеса",
                is_active=True,
                source_url="http://example.com/detail/1",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(p)
            db.session.commit()
            prop_id = p.id

        resp = client.get(f"/api/v1/properties/{prop_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["title"] == "Detail Test"
        assert data["price"] == 75_000

    def test_property_detail_not_found_returns_404(self, client):
        resp = client.get("/api/v1/properties/999999")
        assert resp.status_code == 404

    def test_search_filter_integration(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=3)
        with client.application.app_context():
            p = Property(
                title="Унікальна мансарда",
                price=90_000,
                currency="USD",
                city="Київ",
                is_active=True,
                source_url="http://example.com/unique/1",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(p)
            db.session.commit()

        resp = client.get("/api/v1/properties?search=Унікальна")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert len(data) == 1
        assert "Унікальна" in data[0]["title"]

    def test_price_filter_integration(self, client):
        _seed_properties(client, cities=["Київ"], count_per_city=5)
        resp = client.get("/api/v1/properties?price_min=30000&price_max=32000")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        for item in data:
            assert 30_000 <= item["price"] <= 32_000

    def test_map_endpoint_integration(self, client):
        with client.application.app_context():
            p_geo = Property(
                title="З координатами",
                price=55_000,
                currency="USD",
                city="Київ",
                latitude=50.45,
                longitude=30.52,
                is_active=True,
                source_url="http://example.com/map/1",
                created_at=datetime.now(timezone.utc),
            )
            p_no_geo = Property(
                title="Без координат",
                price=35_000,
                currency="USD",
                city="Харків",
                latitude=None,
                longitude=None,
                is_active=True,
                source_url="http://example.com/map/2",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add_all([p_geo, p_no_geo])
            db.session.commit()

        resp = client.get("/api/v1/properties/map")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 1
        assert data["data"][0]["city"] == "Київ"

    def test_authenticated_map_shows_source_url(self, client):
        with client.application.app_context():
            p = Property(
                title="Geo apt",
                price=50_000,
                currency="USD",
                city="Київ",
                latitude=50.45,
                longitude=30.52,
                is_active=True,
                source_url="http://example.com/map/auth/1",
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(p)
            db.session.commit()

        token = _create_and_login(client, "mapuser@test.com")
        resp = client.get("/api/v1/properties/map", headers=_auth(token))
        assert resp.status_code == 200
        item = resp.get_json()["data"][0]
        assert item["source_url"] is not None
