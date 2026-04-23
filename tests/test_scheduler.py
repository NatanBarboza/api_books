import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from app.models.revoked_token_model import RevokedToken
from app.repository.revoked_token_repository import RevokedTokenRepository
from app.core.scheduler import cleanup_expired_tokens, start_scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_revoked_token(jti: str, expires_at: datetime) -> RevokedToken:
    return RevokedToken(jti=jti, expires_at=expires_at)


def past(hours: int = 1) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def future(hours: int = 1) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


# ---------------------------------------------------------------------------
# RevokedTokenRepository.delete_expired
# ---------------------------------------------------------------------------

class TestDeleteExpired:
    def test_removes_expired_tokens(self, db):
        """Tokens com expires_at no passado devem ser removidos."""
        db.add(make_revoked_token("jti-expired-1", past(2)))
        db.add(make_revoked_token("jti-expired-2", past(1)))
        db.commit()

        deleted = RevokedTokenRepository(db).delete_expired()

        assert deleted == 2
        assert db.query(RevokedToken).count() == 0

    def test_keeps_valid_tokens(self, db):
        """Tokens com expires_at no futuro não devem ser removidos."""
        db.add(make_revoked_token("jti-valid-1", future(1)))
        db.add(make_revoked_token("jti-valid-2", future(2)))
        db.commit()

        deleted = RevokedTokenRepository(db).delete_expired()

        assert deleted == 0
        assert db.query(RevokedToken).count() == 2

    def test_removes_only_expired_keeps_valid(self, db):
        """Remove apenas expirados, mantém os válidos."""
        db.add(make_revoked_token("jti-expired", past(1)))
        db.add(make_revoked_token("jti-valid", future(1)))
        db.commit()

        deleted = RevokedTokenRepository(db).delete_expired()

        assert deleted == 1
        remaining = db.query(RevokedToken).all()
        assert len(remaining) == 1
        assert remaining[0].jti == "jti-valid"

    def test_returns_zero_when_nothing_to_delete(self, db):
        """Deve retornar 0 quando não há tokens expirados."""
        deleted = RevokedTokenRepository(db).delete_expired()
        assert deleted == 0

    def test_expired_token_is_no_longer_found_after_cleanup(self, db):
        """Token removido não deve mais ser encontrado pelo is_revoked."""
        repo = RevokedTokenRepository(db)
        db.add(make_revoked_token("jti-gone", past(1)))
        db.commit()

        assert repo.is_revoked("jti-gone") is True
        repo.delete_expired()
        assert repo.is_revoked("jti-gone") is False


# ---------------------------------------------------------------------------
# cleanup_expired_tokens (função do agendador)
# ---------------------------------------------------------------------------

class TestCleanupExpiredTokens:
    def test_cleanup_runs_without_error(self, db):
        """A função de limpeza deve executar sem lançar exceções."""
        with patch("app.core.scheduler.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            repo_mock = MagicMock()
            repo_mock.delete_expired.return_value = 0

            with patch("app.core.scheduler.RevokedTokenRepository", return_value=repo_mock):
                cleanup_expired_tokens()

            repo_mock.delete_expired.assert_called_once()
            mock_db.close.assert_called_once()

    def test_cleanup_closes_db_even_on_error(self, db):
        """A sessão do banco deve ser fechada mesmo se ocorrer um erro."""
        with patch("app.core.scheduler.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            repo_mock = MagicMock()
            repo_mock.delete_expired.side_effect = Exception("DB error")

            with patch("app.core.scheduler.RevokedTokenRepository", return_value=repo_mock):
                cleanup_expired_tokens()

            mock_db.close.assert_called_once()

    def test_cleanup_logs_when_tokens_deleted(self):
        """Deve logar quando tokens forem removidos."""
        with patch("app.core.scheduler.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            repo_mock = MagicMock()
            repo_mock.delete_expired.return_value = 3

            with patch("app.core.scheduler.RevokedTokenRepository", return_value=repo_mock):
                with patch("app.core.scheduler.logger") as mock_logger:
                    cleanup_expired_tokens()
                    mock_logger.info.assert_called_once()

    def test_cleanup_does_not_log_info_when_nothing_deleted(self):
        """Não deve logar info quando nenhum token for removido."""
        with patch("app.core.scheduler.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            repo_mock = MagicMock()
            repo_mock.delete_expired.return_value = 0

            with patch("app.core.scheduler.RevokedTokenRepository", return_value=repo_mock):
                with patch("app.core.scheduler.logger") as mock_logger:
                    cleanup_expired_tokens()
                    mock_logger.info.assert_not_called()

    def test_cleanup_logs_error_on_exception(self):
        """Deve logar o erro quando uma exceção ocorrer."""
        with patch("app.core.scheduler.SessionLocal") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            repo_mock = MagicMock()
            repo_mock.delete_expired.side_effect = Exception("DB error")

            with patch("app.core.scheduler.RevokedTokenRepository", return_value=repo_mock):
                with patch("app.core.scheduler.logger") as mock_logger:
                    cleanup_expired_tokens()
                    mock_logger.error.assert_called_once()


# ---------------------------------------------------------------------------
# start_scheduler
# ---------------------------------------------------------------------------

class TestStartScheduler:
    def test_scheduler_starts_successfully(self):
        """O agendador deve iniciar e estar rodando."""
        scheduler = start_scheduler()
        assert scheduler.running is True
        scheduler.shutdown()

    def test_scheduler_has_cleanup_job(self):
        """O agendador deve ter o job de limpeza registrado."""
        scheduler = start_scheduler()
        job_ids = [job.id for job in scheduler.get_jobs()]
        assert "cleanup_expired_tokens" in job_ids
        scheduler.shutdown()

    def test_scheduler_shuts_down_cleanly(self):
        """O agendador deve encerrar sem erros."""
        scheduler = start_scheduler()
        scheduler.shutdown()
        assert scheduler.running is False