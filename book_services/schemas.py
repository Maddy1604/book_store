from pydantic import BaseModel

# Schema for creating new book
class CreateBookSchema(BaseModel):
    """
    This schema is used for creating a new book. It defines the fields required 
    for creating a book.
    """
    name: str
    author: str
    description: str
    price: int
    stock: int
    