from fastapi import FastAPI, Depends, HTTPException, Security, Request, Response
from sqlalchemy.orm import Session
from .models import Book, get_db
from .schemas import CreateBookSchema
from .utils import auth_user
from settings import logger
from fastapi.security import APIKeyHeader

# Initialize FastAPI app with dependency
app = FastAPI(dependencies= [Security(APIKeyHeader(name= "Authorization", auto_error= False)), Depends(auth_user)])

# CREATE Book
@app.post("/books/", status_code= 201)
def create_book(request: Request, body : CreateBookSchema, db: Session = Depends(get_db)):
    """
    Create a new book in the system. Only admin or superusers are allowed to perform this action.
    Parameters:
    book: A `CreateBookSchema` schema instance containing the book details.
    db: The database session to interact with the database.
    Return:
    dict: A dictionary containing a success message and the newly created book details.
    """
    try:
        # Retrieve user data from the request state
        user_data = request.state.user
        logger.info(user_data)

        # Check if the user is a superuser
        if not user_data.get('is_super_user', False):
            logger.warning(f"Unauthorized user tried to create a book: {user_data['email']}")
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")

        # Check if the book already exists
        book = db.query(Book).filter(Book.name == body.name).first()
        if book:
            raise HTTPException(status_code=400, detail="Book with this name already exists")
        logger.info("book fetched")
        # Prepare the data for creating a new book
        data = body.model_dump()
        data.update(user_id=user_data["id"]) 

        new_book = Book(**data)
        db.add(new_book)
        db.commit()
        db.refresh(new_book)

        logger.info(f"Book created by {user_data['email']}: {new_book.name}")
        
        return {
            "message": "Book created successfully",
            "status": "success",
            "data": new_book
        }
        
    except HTTPException as e:
        logger.error(f"Error during book creation: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred during book creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

# GET all books
@app.get("/books/", status_code= 200)
def get_books(request: Request, db: Session = Depends(get_db)):
    """
    Get a list of all books in the system. Accessible by any authorized user.
    Parameters:
    db: The database session to interact with the database.
    current_user: Dictionary containing user details
    Returns:
    dict: A dictionary containing a success message and a list of books the database.
    """
    try:
        user_id = request.state.user["id"]
        
        books = db.query(Book).all()
        if not books:
             # If no books found in the database
                logger.warning(f"No books found in the database for user ID: {user_id}")
                raise HTTPException(status_code=404, detail="No books found")
            
        # Serialize books
        books_data = [x.to_dict for x in books]
        logger.info(f"Books retrieved by {request.state.user['email']}")

        return {
            "message": "Books retrieved successfully",
            "status": "success",
            "data": books_data
        }
        
    except Exception as e:
        logger.error(f"Unexpected error during books retrieval: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# UPDATE Book
@app.put("/books/{book_id}", status_code= 200)
def update_book(request: Request, book_id: int, body : CreateBookSchema, db: Session = Depends(get_db)):
    """
    Update details of an existing book. Only admin or superusers are allowed to perform this action.
    Parameters:
    book_id: The ID of the book to update
    book_update: CreateBookSchema containing updated data
    db: The database session to interact with the database.
    current_user: Dictionary containing user details
    Returns:
    dict: A dictionary containing a success message and the updated book details.
    """
    try:
        user_data = request.state.user

        if not user_data.get("is_super_user", False):
            logger.warning(f"Unauthorized user tried to update a book: {user_data['email']}")
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")

        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        for key, value in body.model_dump().items():
            setattr(book, key, value)

        db.commit()
        db.refresh(book)

        logger.info(f"Book updated by {user_data['email']}: {book.name}")

        return {
            "message": "Book updated successfully",
            "status": "success",
            "data": book.to_dict
        }
        
    except HTTPException as e:
        logger.error(f"Error during book update: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during book update: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

# DELETE Book 
@app.delete("/books/{book_id}", status_code= 200)
def delete_book(request: Request, book_id: int, db: Session = Depends(get_db)):
    """
    Delete a book from the system. Only admin or superusers are allowed to perform this action.
    Parameters:
    book_id: The ID of the book to delete
    db: The database session to interact with the database.
    current_user: Dictionary containing user details
    Returns:
    dict: A success message confirming the deletion of the book.

    """
    try:
        user_data = request.state.user
        if not user_data.get("is_super_user", False ):
            logger.warning(f"Unauthorized user tried to delete a book: {user_data['email']}")
            raise HTTPException(status_code=403, detail="Not authorized to perform this action")

        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        db.delete(book)
        db.commit()

        logger.info(f"Book deleted by {user_data['email']}: {book.name}")

        return {
            "message": "Book deleted successfully",
            "status": "success"
        }
        
    except HTTPException as e:
        logger.error(f"Error during book deletion: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during book deletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
