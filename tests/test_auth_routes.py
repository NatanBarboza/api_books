import pytest
from datetime import datetime, timezone
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.user_model import User
from app.models.revoked_token_model import RevokedToken
from app.main import app, limiter

AUTH_URL = "/auth"

@pytest.fixture(autouse=True)
def reset_limiter():
    """Reseta os contadores do rate limiter antes de cada teste."""
    limiter.reset()
    yield
    limiter.reset()

# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_succeeds_with_valid_data(self, client):
        payload = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "Test1234",
        }
        response = client.post(f"{AUTH_URL}/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["username"] == payload["username"]
        assert data["is_active"] is True
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_fails_with_duplicate_email(self, client):
        payload = {
            "email": "dup@test.com",
            "username": "user1",
            "password": "Test1234",
        }
        client.post(f"{AUTH_URL}/register", json=payload)

        payload["username"] = "user2"
        response = client.post(f"{AUTH_URL}/register", json=payload)
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered."

    def test_register_fails_with_duplicate_username(self, client):
        payload = {
            "email": "user1@test.com",
            "username": "sameusername",
            "password": "Test1234",
        }
        client.post(f"{AUTH_URL}/register", json=payload)

        payload["email"] = "user2@test.com"
        response = client.post(f"{AUTH_URL}/register", json=payload)
        assert response.status_code == 409
        assert response.json()["detail"] == "Username already registered."

    def test_register_fails_with_weak_password(self, client):
        payload = {
            "email": "weak@test.com",
            "username": "weakuser",
            "password": "123",
        }
        response = client.post(f"{AUTH_URL}/register", json=payload)
        assert response.status_code == 422

    def test_register_fails_with_missing_fields(self, client):
        response = client.post(f"{AUTH_URL}/register", json={"email": "incomplete@test.com"})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_succeeds_with_valid_credentials(self, client, db):
        user = User(
            email="login@test.com",
            username="loginuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "loginuser", "password": "Test1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_returns_user_scope_for_regular_user(self, client, db):
        user = User(
            email="user@test.com",
            username="regularuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "regularuser", "password": "Test1234"},
        )
        assert response.status_code == 200

    def test_login_returns_admin_scope_for_superuser(self, client, db):
        user = User(
            email="admin@test.com",
            username="adminuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "adminuser", "password": "Test1234"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_fails_with_wrong_password(self, client, db):
        user = User(
            email="wrongpass@test.com",
            username="wrongpassuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "wrongpassuser", "password": "WrongPass99"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials."

    def test_login_fails_with_nonexistent_user(self, client):
        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "ghost", "password": "Test1234"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials."

    def test_login_fails_with_inactive_user(self, client, db):
        user = User(
            email="inactive@test.com",
            username="inactiveuser",
            hashed_password=hash_password("Test1234"),
            is_active=False,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        response = client.post(
            f"{AUTH_URL}/login",
            data={"username": "inactiveuser", "password": "Test1234"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Account deactivated."


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

class TestMe:
    def test_me_returns_authenticated_user(self, client, db, user_token):
        response = client.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "user@test.com"
        assert "hashed_password" not in data

    def test_me_requires_authentication(self, client):
        response = client.get(f"{AUTH_URL}/me")
        assert response.status_code == 401

    def test_me_fails_with_invalid_token(self, client):
        response = client.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": "Bearer tokeninvalido"},
        )
        assert response.status_code == 401

    def test_me_fails_with_revoked_token(self, client, db, user_token):
        from app.core.security import decode_token
        payload = decode_token(user_token)
        db.add(RevokedToken(jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)))
        db.commit()

        response = client.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

class TestRefresh:
    def test_refresh_returns_new_tokens(self, client, db):
        user = User(
            email="refresh@test.com",
            username="refreshuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        refresh_token = create_refresh_token(str(user.id))

        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token

    def test_refresh_revokes_used_token(self, client, db):
        user = User(
            email="rotation@test.com",
            username="rotationuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        refresh_token = create_refresh_token(str(user.id))
        client.post(f"{AUTH_URL}/refresh", json={"refresh_token": refresh_token})

        # tentar usar o mesmo refresh token novamente deve falhar
        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token."

    def test_refresh_fails_with_revoked_token(self, client, db):
        user = User(
            email="revokedrefresh@test.com",
            username="revokedrefreshuser",
            hashed_password=hash_password("Test1234"),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        refresh_token = create_refresh_token(str(user.id))

        from app.core.security import decode_token
        payload = decode_token(refresh_token)
        db.add(RevokedToken(jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)))
        db.commit()

        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token."

    def test_refresh_fails_with_access_token(self, client, user_token):
        # access token não deve ser aceito no endpoint de refresh
        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": user_token},
        )
        assert response.status_code == 401

    def test_refresh_fails_with_invalid_token(self, client):
        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": "tokeninvalido"},
        )
        assert response.status_code == 401

    def test_refresh_fails_with_inactive_user(self, client, db):
        user = User(
            email="inactiverefresh@test.com",
            username="inactiverefreshuser",
            hashed_password=hash_password("Test1234"),
            is_active=False,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        refresh_token = create_refresh_token(str(user.id))

        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_succeeds_with_valid_tokens(self, client, db, user_token):
        user = db.query(User).filter(User.username == "testuser").first()
        refresh_token = create_refresh_token(str(user.id))

        response = client.post(
            f"{AUTH_URL}/logout",
            json={"access_token": user_token, "refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 204

    def test_logout_revokes_access_token(self, client, db, user_token):
        user = db.query(User).filter(User.username == "testuser").first()
        refresh_token = create_refresh_token(str(user.id))

        client.post(
            f"{AUTH_URL}/logout",
            json={"access_token": user_token, "refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # access token revogado não deve mais autenticar
        response = client.get(
            f"{AUTH_URL}/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 401

    def test_logout_revokes_refresh_token(self, client, db, user_token):
        user = db.query(User).filter(User.username == "testuser").first()
        refresh_token = create_refresh_token(str(user.id))

        client.post(
            f"{AUTH_URL}/logout",
            json={"access_token": user_token, "refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # refresh token revogado não deve emitir novos tokens
        response = client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401

    def test_logout_without_refresh_token_only_revokes_access(self, client, db, user_token):
        response = client.post(
            f"{AUTH_URL}/logout",
            json={"access_token": user_token, "refresh_token": None},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 204

    def test_logout_requires_authentication(self, client, user_token):
        response = client.post(
            f"{AUTH_URL}/logout",
            json={"access_token": user_token, "refresh_token": None},
        )
        assert response.status_code == 401