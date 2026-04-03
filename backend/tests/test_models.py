from app.models import User, Property


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
        assert user.check_password("wrong") is False

    def test_check_password_empty_string(self):
        user = User(email="test@example.com")
        user.set_password("PassW0rd!")
        assert user.check_password("") is False

    def test_different_passwords_produce_different_hashes(self):
        u1 = User(email="a@example.com")
        u2 = User(email="b@example.com")
        u1.set_password("PassW0rd!")
        u2.set_password("OtherP4ss!")
        assert u1.password_hash != u2.password_hash

    def test_same_password_produces_different_hashes(self):
        u1 = User(email="a@example.com")
        u2 = User(email="b@example.com")
        u1.set_password("PassW0rd!")
        u2.set_password("PassW0rd!")
        assert u1.password_hash != u2.password_hash

    def test_role_can_be_set_to_analyst(self):
        user = User(email="test@example.com", role="Analyst")
        assert user.role == "Analyst"

    def test_to_dict_contains_required_keys(self):
        user = User(email="test@example.com", role="Analyst")
        user.set_password("PassW0rd!")
        d = user.to_dict()
        assert d["email"] == "test@example.com"
        assert d["role"] == "Analyst"
        assert "id" in d
        assert "created_at" in d
        assert "password_hash" not in d


class TestPropertyModelDefaults:
    def test_property_stores_currency(self):
        p = Property(title="Test", price=50000, currency="USD")
        assert p.currency == "USD"

    def test_property_stores_is_active(self):
        p = Property(title="Test", price=50000, is_active=True)
        assert p.is_active is True

    def test_property_without_coordinates(self):
        p = Property(title="No coords", price=30000)
        assert p.latitude is None
        assert p.longitude is None
