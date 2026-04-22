from sqlalchemy.orm import Session
from app.repository.book_repository import BookRepository

class BookService:
    def __init__(self, db: Session):
        self.repo = BookRepository(db)

    def list_books(self):
        return self.repo.get_all()

    def get_book(self, book_id: int):
        return self.repo.get_by_id(book_id)

    def create_book(self, data):
        return self.repo.create(data)

    def update_book(self, book_id: int, data):
        book = self.repo.get_by_id(book_id)
        if not book:
            return None
        return self.repo.update(book, data)

    def delete_book(self, book_id: int):
        book = self.repo.get_by_id(book_id)
        if not book:
            return False
        self.repo.delete(book)
        return True