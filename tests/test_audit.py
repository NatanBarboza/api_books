import pytest
from app.core.security import hash_password, create_refresh_token
from app.models.user_model import User
from app.models.audit_model import AuditLog
from app.main import limiter

AUTH_URL = "/auth"

@pytest.fixture(autouse=True)
def reset_limiter():
    """Reseta os contadores do rate limiter antes de cada teste."""
    limiter.reset()
    yield
    limiter.reset()

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


# ---------------------------------------------------------------------------
# Geração de eventos — cada ação registra na auditoria
# ---------------------------------------------------------------------------

class TestAuditEventGeneration:
    def test_register_generates_audit_event(self, client, db, admin_token):
        client.post(
            f"{AUTH_URL}/register",
            json={"email": "audit@test.com", "username": "audituser", "password": "Test1234"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "register" in events

    def test_login_success_generates_audit_event(self, client, db, admin_token, regular_user):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": regular_user.username, "password": "Test1234"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "login_success" in events

    def test_login_failed_generates_audit_event(self, client, db, admin_token):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": "ghost", "password": "Wrong123"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "login_failed" in events

    def test_logout_generates_audit_event(self, client, db, admin_token, user_token):
        client.post(
            f"{AUTH_URL}/logout",
            json={"access_token": user_token, "refresh_token": None},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "logout" in events

    def test_refresh_generates_audit_event(self, client, db, admin_token, regular_user):
        refresh_token = create_refresh_token(str(regular_user.id))
        client.post(
            f"{AUTH_URL}/refresh",
            json={"refresh_token": refresh_token},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "refresh" in events

    def test_promote_generates_audit_event(self, client, db, admin_token, regular_user):
        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "promote" in events

    def test_demote_generates_audit_event(self, client, db, admin_token, regular_user):
        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/promote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        client.patch(
            f"{AUTH_URL}/users/{regular_user.id}/demote",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        events = [r["event"] for r in response.json()["results"]]
        assert "demote" in events


# ---------------------------------------------------------------------------
# GET /auth/audit — acesso e estrutura da resposta
# ---------------------------------------------------------------------------

class TestAuditEndpoint:
    def test_audit_requires_authentication(self, client):
        response = client.get(f"{AUTH_URL}/audit")
        assert response.status_code == 401

    def test_audit_forbidden_for_user_scope(self, client, user_token):
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_audit_accessible_for_admin(self, client, admin_token):
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_audit_response_has_correct_structure(self, client, admin_token):
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_audit_result_has_correct_fields(self, client, db, admin_token, regular_user):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": regular_user.username, "password": "Test1234"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        result = response.json()["results"][0]
        assert "id" in result
        assert "user_id" in result
        assert "username" in result
        assert "event" in result
        assert "ip_address" in result
        assert "created_at" in result

    def test_audit_returns_empty_when_no_events(self, client, admin_token):
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []


# ---------------------------------------------------------------------------
# GET /auth/audit — filtros e paginação
# ---------------------------------------------------------------------------

class TestAuditFilters:
    def test_filter_by_event_returns_only_matching_events(self, client, db, admin_token, regular_user):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": regular_user.username, "password": "Test1234"},
        )
        client.post(
            f"{AUTH_URL}/login",
            data={"username": "ghost", "password": "Wrong123"},
        )
        response = client.get(
            f"{AUTH_URL}/audit?event=login_failed",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        results = response.json()["results"]
        assert all(r["event"] == "login_failed" for r in results)

    def test_filter_by_user_id_returns_only_matching_user(self, client, db, admin_token, regular_user):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": regular_user.username, "password": "Test1234"},
        )
        response = client.get(
            f"{AUTH_URL}/audit?user_id={regular_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        results = response.json()["results"]
        assert all(r["user_id"] == regular_user.id for r in results)

    def test_limit_param_restricts_results(self, client, db, admin_token, regular_user):
        for _ in range(5):
            client.post(
                f"{AUTH_URL}/login",
                data={"username": regular_user.username, "password": "Test1234"},
            )
        response = client.get(
            f"{AUTH_URL}/audit?limit=3",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert len(response.json()["results"]) <= 3

    def test_offset_param_skips_results(self, client, db, admin_token, regular_user):
        for _ in range(4):
            client.post(
                f"{AUTH_URL}/login",
                data={"username": regular_user.username, "password": "Test1234"},
            )
        response_all = client.get(
            f"{AUTH_URL}/audit?limit=100&offset=0",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        response_offset = client.get(
            f"{AUTH_URL}/audit?limit=100&offset=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        total = response_all.json()["total"]
        total_offset = response_offset.json()["total"]
        assert total_offset == total - 2

    def test_login_failed_does_not_store_user_id(self, client, db, admin_token):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": "ghost", "password": "Wrong123"},
        )
        response = client.get(
            f"{AUTH_URL}/audit?event=login_failed",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        results = response.json()["results"]
        assert len(results) > 0
        assert results[0]["user_id"] is None
        assert results[0]["username"] == "ghost"

    def test_results_are_ordered_by_most_recent(self, client, db, admin_token, regular_user):
        client.post(
            f"{AUTH_URL}/login",
            data={"username": regular_user.username, "password": "Test1234"},
        )
        client.post(
            f"{AUTH_URL}/login",
            data={"username": "ghost", "password": "Wrong123"},
        )
        response = client.get(
            f"{AUTH_URL}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        results = response.json()["results"]
        assert results[0]["event"] == "login_success"
        assert results[1]["event"] == "login_failed"