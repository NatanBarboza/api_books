from sqlalchemy.orm import Session
from app.models.revoked_token_model import RevokedToken
from datetime import datetime, timezone

class RevokedTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def revoke(self, jti: str, expires_at: datetime) -> None:
        self.db.add(RevokedToken(jti=jti, expires_at=expires_at))
        self.db.commit()

    def is_revoked(self, jti: str) -> bool:
        return self.db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None
    
    def delete_expired(self) -> int:
        now = datetime.now(timezone.utc)
        deleted = (
            self.db.query(RevokedToken)
            .filter(RevokedToken.expires_at < now)
            .delete()
        )
        self.db.commit()
        return deleted