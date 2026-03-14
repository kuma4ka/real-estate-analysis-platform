import pytest
from app import create_app, db
from app.models import Property
from config import TestConfig
import datetime


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def seeded_client(client):
    """Client with two properties, one with coordinates and one without."""
    with client.application.app_context():
        p1 = Property(
            title='Квартира з координатами',
            price=50_000,
            currency='USD',
            city='Київ',
            is_active=True,
            latitude=50.45,
            longitude=30.52,
            source_url='http://example.com/1',
            created_at=datetime.datetime.utcnow(),
        )
        p2 = Property(
            title='Квартира без координат',
            price=40_000,
            currency='USD',
            city='Львів',
            is_active=True,
            latitude=None,
            longitude=None,
            source_url='http://example.com/2',
            created_at=datetime.datetime.utcnow(),
        )
        db.session.add_all([p1, p2])
        db.session.commit()
    return client


class TestMapEndpoint:
    def test_map_returns_only_geocoded(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties/map')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'data' in data
        assert 'count' in data
        # Only p1 has coordinates
        assert data['count'] == 1
        assert data['data'][0]['city'] == 'Київ'

    def test_map_hides_source_url_for_unauthenticated(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties/map')
        listing = resp.get_json()['data'][0]
        assert listing['source_url'] is None

    def test_map_includes_required_fields(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties/map')
        listing = resp.get_json()['data'][0]
        for field in ('id', 'title', 'price', 'lat', 'lng', 'city'):
            assert field in listing

    def test_map_empty_when_no_geocoded(self, client):
        with client.application.app_context():
            p = Property(
                title='Без координат',
                price=30_000,
                currency='USD',
                city='Одеса',
                is_active=True,
                latitude=None,
                longitude=None,
                source_url='http://example.com/3',
                created_at=datetime.datetime.utcnow(),
            )
            db.session.add(p)
            db.session.commit()
        resp = client.get('/api/v1/properties/map')
        assert resp.status_code == 200
        assert resp.get_json()['count'] == 0

    def test_map_filter_by_city(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties/map?city=Київ')
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert all(d['city'] == 'Київ' for d in data)


class TestPropertiesEndpoint:
    def test_properties_returns_paginated(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties')
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'data' in body
        assert 'meta' in body
        assert body['meta']['total_items'] == 2

    def test_properties_hides_source_url_for_guest(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties')
        for item in resp.get_json()['data']:
            assert item['source_url'] is None

    def test_properties_filter_city(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties?city=Київ')
        data = resp.get_json()['data']
        assert len(data) == 1

    def test_properties_filter_price_range(self, seeded_client):
        resp = seeded_client.get('/api/v1/properties?price_min=45000&price_max=55000')
        data = resp.get_json()['data']
        assert len(data) == 1
        assert data[0]['price'] == 50_000

    def test_properties_filter_search(self, seeded_client):
        # Both "Квартира з координатами" and "Квартира без координат" match "координат"
        resp = seeded_client.get('/api/v1/properties?search=координат')
        data = resp.get_json()['data']
        assert len(data) == 2

        resp2 = seeded_client.get('/api/v1/properties?search=без')
        data2 = resp2.get_json()['data']
        assert len(data2) == 1
        assert data2[0]['title'] == 'Квартира без координат'
