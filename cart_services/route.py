from fastapi import FastAPI, Depends, HTTPException, Security, Request, status
from sqlalchemy.orm import Session
from .models import Cart, CartItem, get_db
from .schemas import CreateCartItem, CartResponse
from .utils import auth_user
from settings import settings
from fastapi.security import APIKeyHeader
import requests as http
from loguru import logger


# Initialize FastAPI app with dependency
app = FastAPI(dependencies=[Security(APIKeyHeader(name="Authorization", auto_error=False)), Depends(auth_user)])

# CREATE Cart Item
@app.post("/cart/items/", status_code=201)
def create_or_update_cart_item(request: Request, payload: CreateCartItem, db: Session = Depends(get_db)):
    """
    Create a new cart item or update an existing item in the cart.
    Only authorized users can perform this action.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        # Verify the book exists in book_services
        book_service_url = f"{settings.IDENTIFY_BOOK}{payload.book_id}"
        response = http.get(book_service_url, headers={"Authorization": request.headers.get("Authorization")})

        # Check response status and handle error if book is not found
        if response.status_code != 200:
            logger.info(f"Book with ID {payload.book_id} not found.")
            raise HTTPException(status_code=400, detail=f"Book with ID {payload.book_id} not found")

        # Parse the response JSON and extract book price
        book_data = response.json()
        book_price = book_data["data"].get("price")
        book_stock = book_data["data"].get("stock")

        if book_price is None:
            logger.error("Book price not found in book data.")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Book price not available")

        if payload.quantity > book_stock:
            logger.info(f"Orderd book quantity {payload.quantity} is high than availabel book stock {book_stock}")
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"High order quuantity than present book stock ")

        # Get or create the user's cart
        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == False).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)

        # Check if the cart item already exists
        cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.book_id == payload.book_id).first()
        if cart_item:
            # Update quantity and price for existing item
            cart_item.quantity = payload.quantity
            cart_item.price = book_price * cart_item.quantity
        else:
            # Create a new cart item for the book
            cart_item = CartItem(cart_id=cart.id, book_id=payload.book_id, quantity=payload.quantity, price=book_price * payload.quantity)
            db.add(cart_item)

        # Commit the item addition/update
        db.commit()
        db.refresh(cart)

        # Recalculate total price and quantity for the entire cart
        cart.total_price = sum(item.price for item in cart.items)
        cart.total_quantity = sum(item.quantity for item in cart.items)

        # Commit the cart updates
        db.commit()
        logger.info(f"Cart updated for user: {user_data['email']}")

        # Return updated cart details
        return {
            "message": "Cart item added or updated successfully",
            "status": "success",
            "data": {
                "cart_id": cart.id,
                "total_price": cart.total_price,
                "total_quantity": cart.total_quantity
            }
        }

    except HTTPException as error:
        logger.error(f"Error during cart item creation: {str(error.detail)}")
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=f"{error}")
    except Exception as error:
        logger.error(f"Unexpected error during cart item creation: {str(error)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")


# GET Cart
@app.get("/cart/", status_code=200)
def get_cart(request: Request, db: Session = Depends(get_db)):
    """
    Get the user's cart details.
    Parameters:
    db: The database session to interact with the database.
    Returns:
    ResponseCartSchema: A schema instance containing cart details.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered ==  False).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")


        logger.info(f"Cart retrieved for user: {user_data['email']}")

        return {
            "message": "Cart retrieved successfully",
            "status": "success",
            "data": cart.to_dict
        }

    except HTTPException as error:
        logger.error(f"Error during cart retrieval: {str(error.detail)}")
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=(f"Error during cart retrieval: {str(error.detail)}"))
    except Exception as error:
        logger.error(f"Unexpected error during cart retrieval: {str(error)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


# DELETE Cart Item
@app.delete("/cart/items", status_code=200)
def delete_cart_item(request: Request, book_id: int, db: Session = Depends(get_db)):
    """
    Decrease the quantity of a cart item or delete it if the quantity reaches zero.
    Parameters:
    item_id: The ID of the cart item to modify.
    quantity: The quantity to remove from the cart item.
    db: The database session to interact with the database.
    Returns:
    dict: A success message confirming the action taken on the cart item.
    """
    try:
        user_data = request.state.user
        user_id = user_data["id"]

        # Retrieve the user's cart
        cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == False).first() 
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Retrieve the specific cart item
        cart_item = db.query(CartItem).filter(CartItem.book_id == book_id, CartItem.cart_id == cart.id).first()
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        db.delete(cart_item)

        # Commit changes to the cart item
        db.commit()

        # # Recalculate the cart's total price and quantity
        cart.total_price = sum(item.price for item in cart.items)
        cart.total_quantity = sum(item.quantity for item in cart.items)

        # Commit the updated cart totals
        db.commit()

        logger.info(f"Cart item quantity updated or deleted for user: {user_data['email']}.")

        return {
            "message": "Cart item quantity adjusted successfully",
            "status": "success"
        }

    except HTTPException as error:
        logger.error(f"Error during cart item update or deletion: {str(error.detail)}")
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=f"{error}")
    except Exception as error:
        logger.error(f"Unexpected error during cart item update or deletion: {str(error)}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
