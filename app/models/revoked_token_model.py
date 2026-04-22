from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.session import Base

class RevokedToken(Base):
    __tablename__ = "tb_revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())