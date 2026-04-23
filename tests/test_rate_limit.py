import pytest
from fastapi.testclient import TestClient
from app.main import app, limiter
from app.db.session import get_db, Base
from app.core.security import hash_password
from app.models.user_model import User

AUTH_URL = "/auth"


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reseta os contadores do rate limiter antes de cada teste."""
    limiter.reset()
    yield
    limiter.reset()


# ---------------------------------------------------------------------------
# Rate limit — POST /auth/login
# ---------------------------------------------------------------------------

class TestLoginRateLimit:
    def test_login_allows_requests_within_limit(self, client, db):
        user = User(
            email="ratelimit@test.com",
            username="ratelimituser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        for _ in range(5):
            response = client.post(
                f"{AUTH_URL}/login",
                data={"username": "ratelimituser", "password": "Test1234"},
            )
            assert response.status_code == 200

    def test_login_blocks_after_limit_exceeded(self, client, db):
        user = User(
            email="blocked@test.com",
            username="blockeduser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        for _ in range(5):
            client.post(
                f"{AUTH_URL}/login",
                data={"username": "blockeduser", "password": "Test1234"},
            )

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "blockeduser", "password": "Test1234"},
        )
        assert response.status_code == 429

    def test_login_429_response_body(self, client, db):
        user = User(
            email="body@test.com",
            username="bodyuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        for _ in range(5):
            client.post(
                f"{AUTH_URL}/login",
                data={"username": "bodyuser", "password": "Test1234"},
            )

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "bodyuser", "password": "Test1234"},
        )
        assert response.status_code == 429
        assert "error" in response.json()

    def test_login_rate_limit_applies_to_failed_attempts_too(self, client):
        for _ in range(5):
            client.post(
                f"{AUTH_URL}/login",
                data={"username": "ghost", "password": "Wrong123"},
            )

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "ghost", "password": "Wrong123"},
        )
        assert response.status_code == 429

    def test_login_limit_resets_after_limiter_reset(self, client, db):
        user = User(
            email="reset@test.com",
            username="resetuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        for _ in range(5):
            client.post(
                f"{AUTH_URL}/login",
                data={"username": "resetuser", "password": "Test1234"},
            )

        blocked = client.post(
            f"{AUTH_URL}/login",
            data={"username": "resetuser", "password": "Test1234"},
        )
        assert blocked.status_code == 429

        limiter.reset()

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "resetuser", "password": "Test1234"},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Rate limit — POST /auth/register
# ---------------------------------------------------------------------------

class TestRegisterRateLimit:
    def test_register_allows_requests_within_limit(self, client):
        for i in range(3):
            response = client.post(
                f"{AUTH_URL}/register",
                json={
                    "email": f"user{i}@test.com",
                    "username": f"user{i}",
                    "password": "Test1234",
                },
            )
            assert response.status_code == 201

    def test_register_blocks_after_limit_exceeded(self, client):
        for i in range(3):
            client.post(
                f"{AUTH_URL}/register",
                json={
                    "email": f"reg{i}@test.com",
                    "username": f"reguser{i}",
                    "password": "Test1234",
                },
            )

        response = client.post(
            f"{AUTH_URL}/register",
            json={
                "email": "blocked@test.com",
                "username": "blockedreguser",
                "password": "Test1234",
            },
        )
        assert response.status_code == 429

    def test_register_429_response_body(self, client):
        for i in range(3):
            client.post(
                f"{AUTH_URL}/register",
                json={
                    "email": f"body{i}@test.com",
                    "username": f"bodyreguser{i}",
                    "password": "Test1234",
                },
            )

        response = client.post(
            f"{AUTH_URL}/register",
            json={
                "email": "bodyblocked@test.com",
                "username": "bodyblocked",
                "password": "Test1234",
            },
        )
        assert response.status_code == 429
        assert "error" in response.json()

    def test_register_rate_limit_applies_to_invalid_payloads_too(self, client):
        for i in range(3):
            client.post(
                f"{AUTH_URL}/register",
                json={
                    "email": f"valid{i}@test.com",
                    "username": f"validuser{i}",
                    "password": "Test1234",
                },
            )

        response = client.post(
            f"{AUTH_URL}/register",
            json={
                "email": "valid4@test.com",
                "username": "validuser4",
                "password": "Test1234",
            },
        )
        assert response.status_code == 429


    def test_register_limit_resets_after_limiter_reset(self, client):
        for i in range(3):
            client.post(
                f"{AUTH_URL}/register",
                json={
                    "email": f"reset{i}@test.com",
                    "username": f"resetreguser{i}",
                    "password": "Test1234",
                },
            )

        blocked = client.post(
            f"{AUTH_URL}/register",
            json={
                "email": "resetblocked@test.com",
                "username": "resetblocked",
                "password": "Test1234",
            },
        )
        assert blocked.status_code == 429

        limiter.reset()

        response = client.post(
            f"{AUTH_URL}/register",
            json={
                "email": "afterreset@test.com",
                "username": "afterreset",
                "password": "Test1234",
            },
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Rotas sem rate limit não são afetadas
# ---------------------------------------------------------------------------

class TestUnlimitedRoutes:
    def test_refresh_has_no_rate_limit(self, client, db):
        """Garante que rotas sem @limiter.limit não são bloqueadas."""
        user = User(
            email="norlimit@test.com",
            username="nolimituser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        from app.core.security import create_refresh_token
        refresh_token = create_refresh_token(str(user.id))

        for _ in range(10):
            response = client.post(
                f"{AUTH_URL}/refresh",
                json={"refresh_token": refresh_token},
            )
            refresh_token = response.json().get("refresh_token", refresh_token)

        assert response.status_code == 200
