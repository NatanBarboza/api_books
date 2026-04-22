from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session

from app.schema.book_schema import (
    BookCreate, 
    BookResponse, 
    BookUpdate
)
from app.service.book_service import BookService
from app.db.session import get_db
from app.dependecies.auth import get_current_user

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/", response_model=list[BookResponse])
def list_books(db: Session = Depends(get_db), _=Security(get_current_user, scopes=["user"])):
    return BookService(db).list_books()

@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db), _=Security(get_current_user, scopes=["user"])):
    book = BookService(db).get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book

@router.post("/create", response_model=BookResponse)
def create_book(book: dict, db: Session = Depends(get_db), _=Security(get_current_user, scopes=["admin"])):
    return BookService(db).create_book(book)

@router.put("/edit/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db), _=Security(get_current_user, scopes=["admin"])):
    updated = BookService(db).update_book(book_id, book.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Book not found.")
    return updated

@router.delete("/delete/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), _=Security(get_current_user, scopes=["admin"])):
    success = BookService(db).delete_book(book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found.")
    return {
        "status_code": 201,
        "message": "Book deleted."
    }