from sqlalchemy import Column, Integer, String
from app.db.session import Base

class Book(Base):
    __tablename__ = "tb_books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    description = Column(String, nullable=False)
    release_year = Column(Integer, nullable=False)