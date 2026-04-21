from sqlalchemy.orm import Session
from app.repository import book_repository

def list_books(db: Session):
    return book_repository.get_all(db)

def get_book(db: Session, book_id: int):
    return book_repository.get_by_id(db, book_id)

def create_book(db: Session, data):
    return book_repository.create(db, data)

def update_book(db: Session, book_id: int, data):
    book = book_repository.get_by_id(db, book_id)
    if not book:
        return None
    return book_repository.update(db, book, data)

def delete_book(db: Session, book_id: int):
    book = book_repository.get_by_id(db, book_id)
    if not book:
        return False
    book_repository.delete(db, book)
    return True