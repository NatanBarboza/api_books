from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "tb_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String, nullable=True)
    event = Column(String, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())