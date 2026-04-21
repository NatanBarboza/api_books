from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.book_schemas import (
    BookCreate, 
    BookResponse, 
    BookUpdate
)
from app.service import book_service
from app.db.session import get_db

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("/", response_model=list[BookResponse])
def list_books(db: Session = Depends(get_db)):
    return book_service.list_books(db)

@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    return book

@router.post("/create", response_model=BookResponse)
def create_book(book: dict, db: Session = Depends(get_db)):
    return book_service.create_book(db, book)

@router.put("/edit/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookUpdate, db: Session = Depends(get_db)):
    updated = book_service.update_book(db, book_id, book.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Book not found.")
    return updated

@router.delete("/delete/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    success = book_service.delete_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found.")
    return {
        "status_code": 201,
        "message": "Book deleted."
    }