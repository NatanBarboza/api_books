from sqlalchemy.orm import Session
from app.models.book_model import Book

def get_all(db: Session) -> list[Book]:
    return db.query(Book).all()

def get_by_id(db: Session, book_id: int) -> Book | None:
    return db.query(Book).filter(Book.id == book_id).first()

def create(db: Session, book_data: dict) -> Book:
    book = Book(**book_data)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def update(db: Session, book: Book, data: dict) -> Book:
    for key, value in data.items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book

def delete(db: Session, book: Book) -> None:
    db.delete(book)
    db.commit()