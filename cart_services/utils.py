# from .models import Cart, CartItem, get_db
# from .schemas import CartItem, CartResponse
# from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Request
from loguru import logger
import requests as http
from settings import settings

def auth_user(request: Request):
    """
    Description:
    Authenticate the user by verifying the Authorization token in the request headers.
    Parameters:
    request: The FastAPI request object containing the headers.
    Returns:
    None: Sets the `request.state.user` with user data if authentication is successful.
    """
    try:
        token = request.headers.get("Authorization")
        if not token:
            raise HTTPException(status_code=401, detail="Authorization token missing")
        
        response = http.get(url=f"{settings.ENDPOINT}{token}")
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail="Invalid User")
        
        user_data = response.json().get("data")
        if not user_data:
            raise HTTPException(status_code=401, detail="User data missing in response")

        request.state.user = user_data
        logger.info("User authenticated successfully.")
        
    except Exception as e:
        logger.error(f"Error during user authentication: {str(e)}")
        raise HTTPException(status_code=500, detail="User authentication failed")


# # Serching for active cart or existing cart 
# def get_active_cart(user_id:int, db : Session = Depends(get_db)):
#     return db.query(Cart).filter(Cart.user_id == user_id, Cart.is_ordered == False).first()

# # Creating new cart
# def create_cart(user_id : int, db : Session = Depends(get_db)):
#     new_cart = Cart(user_id=user_id)
#     db.new(new_cart)
#     db.commit()
#     db.refresh(new_cart)
#     return new_cart

# # Delete the existing cart
# def delete_cart(cart_id : int, db : Session = Depends(get_db)):
#     cart = db.query(Cart).filter(Cart.id == cart_id).first()
#     if cart:
#         db.delete(cart)
#         db.commit()

# # Adding and updating the cart 
# def add_or_update_cart(cart : Cart, items : CartResponse, db : Session = Depends(get_db)):
#     item = db.query(CartItem).filter(CartItem.ca )