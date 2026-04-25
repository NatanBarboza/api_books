import pytest
from app.core.security import hash_password
from app.models.user_model import User

AUTH_URL = "/auth"


@pytest.fixture
def regular_user(db):
    user = User(
        email="regular@test.com",
        username="regularuser",
        hashed_password=hash_password("Test1234"),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def another_admin(db):
    user = User(
        email="another@test.com",
        username="anotheradmin",
        hashed_password=hash_password("Test1234"),
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# PATCH /auth/users/{user_id}/promote
# ---------------------------------------------------------------------------

class TestPromoteUser:
    def test_promote_succeeds_with_admin(self, client, admin_token, regular_user):
        """Admin deve conseguir promover um usuário comum."""
        response = client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_superuser"] is True
        assert data["username"] == regular_user.username
        assert "promoted" in data["message"]

    def test_promote_reflects_in_database(self, client, db, admin_token, regular_user):
        """Promoção deve persistir no banco de dados."""
        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        db.refresh(regular_user)
        assert regular_user.is_superuser is True

    def test_promote_returns_404_for_nonexistent_user(self, client, admin_token):
        """Deve retornar 404 para usuário inexistente."""
        response = client.patch(
            f"{AUTH_URL}/users/999/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found."

    def test_promote_returns_400_when_already_admin(self, client, admin_token, another_admin):
        """Deve retornar 400 ao tentar promover quem já é admin."""
        response = client.patch(
            f"{AUTH_URL}/users/{another_admin.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "User already has admin access."

    def test_promote_returns_400_when_self_promotion(self, client, db, admin_token):
        """Admin não deve conseguir alterar o próprio papel."""
        admin_user = db.query(User).filter(User.username == "adminuser").first()
        response = client.patch(
            f"{AUTH_URL}/users/{admin_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "You cannot change your own role."

    def test_promote_requires_authentication(self, client, regular_user):
        """Deve retornar 401 sem token."""
        response = client.patch(f"{AUTH_URL}/users/{regular_user.id}/promote")
        assert response.status_code == 401

    def test_promote_forbidden_for_user_scope(self, client, user_token, regular_user):
        """Usuário comum não deve conseguir promover ninguém."""
        response = client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /auth/users/{user_id}/demote
# ---------------------------------------------------------------------------

class TestDemoteUser:
    def test_demote_succeeds_with_admin(self, client, admin_token, another_admin):
        """Admin deve conseguir rebaixar outro admin."""
        response = client.patch(
            f"{AUTH_URL}/users/{another_admin.id}/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_superuser"] is False
        assert data["username"] == another_admin.username
        assert "demoted" in data["message"]

    def test_demote_reflects_in_database(self, client, db, admin_token, another_admin):
        """Rebaixamento deve persistir no banco de dados."""
        client.patch(
            f"{AUTH_URL}/users/{another_admin.id}/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        db.refresh(another_admin)
        assert another_admin.is_superuser is False

    def test_demote_returns_404_for_nonexistent_user(self, client, admin_token):
        """Deve retornar 404 para usuário inexistente."""
        response = client.patch(
            f"{AUTH_URL}/users/999/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found."

    def test_demote_returns_400_when_already_user(self, client, admin_token, regular_user):
        """Deve retornar 400 ao tentar rebaixar quem já é usuário comum."""
        response = client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "User already has user access."

    def test_demote_returns_400_when_self_demotion(self, client, db, admin_token):
        """Admin não deve conseguir alterar o próprio papel."""
        admin_user = db.query(User).filter(User.username == "adminuser").first()
        response = client.patch(
            f"{AUTH_URL}/users/{admin_user.id}/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "You cannot change your own role."

    def test_demote_requires_authentication(self, client, another_admin):
        """Deve retornar 401 sem token."""
        response = client.patch(f"{AUTH_URL}/users/{another_admin.id}/demote")
        assert response.status_code == 401

    def test_demote_forbidden_for_user_scope(self, client, user_token, another_admin):
        """Usuário comum não deve conseguir rebaixar ninguém."""
        response = client.patch(
            f"{AUTH_URL}/users/{another_admin.id}/demote",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Ciclo completo — promote + demote
# ---------------------------------------------------------------------------

class TestPromoteDemoteCycle:
    def test_promote_then_demote_returns_to_user(self, client, db, admin_token, regular_user):
        """Promover e depois rebaixar deve retornar o usuário ao estado original."""
        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        db.refresh(regular_user)
        assert regular_user.is_superuser is True

        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        db.refresh(regular_user)
        assert regular_user.is_superuser is False

    def test_promoted_user_can_access_admin_routes(self, client, db, admin_token, regular_user):
        """Usuário promovido deve conseguir acessar rotas admin após novo login."""
        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        login_response = client.post(
            f"{AUTH_URL}/login",
            data={"username": regular_user.username, "password": "Test1234"},
        )
        new_token = login_response.json()["access_token"]

        book_response = client.post(
            "/books/create",
            json={
                "title": "Test Book",
                "author": "Author",
                "description": "Desc",
                "release_year": 2024,
            },
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert book_response.status_code == 200