from sqlalchemy.orm import Session
from app.models.audit_model import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        event: str,
        username: str | None = None,
        user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        entry = AuditLog(
            event=event,
            username=username,
            user_id=user_id,
            ip_address=ip_address,
        )
        self.db.add(entry)
        self.db.commit()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_user_id(self, user_id: int, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_event(self, event: str, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.event == event)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )