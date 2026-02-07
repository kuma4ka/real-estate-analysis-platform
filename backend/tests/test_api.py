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