from pydantic import BaseModel

class Book(BaseModel):
    id: int 
    title: str
    writer: str
    release_year: int