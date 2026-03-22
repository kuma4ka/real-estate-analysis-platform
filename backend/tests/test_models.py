import pytest
from app.models import User

class TestUserModel:
    def test_set_password(self):
        user = User(email="test@example.com")
        user.set_password("PassW0rd!")
        assert user.password_hash is not None
        assert user.password_hash != "PassW0rd!"

    def test_check_password_correct(self):
        user = User(email="test@example.com")
        user.set_password("PassW0rd!")
        assert user.check_password("PassW0rd!") is True

    def test_check_password_incorrect(self):
        user = User(email="test@example.com")
        user.set_password("PassW0rd!")
        assert user.check_password("pass1") is False
