from sqlalchemy.orm import Session
from app.models.book_model import Book

class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Book]:
        return self.db.query(Book).all()

    def get_by_id(self, book_id: int) -> Book | None:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def create(self, book_data: dict) -> Book:
        book = Book(**book_data)
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def update(self, book: Book, data: dict) -> Book:
        for key, value in data.items():
            setattr(book, key, value)
        self.db.commit()
        self.db.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        self.db.delete(book)
        self.db.commit()