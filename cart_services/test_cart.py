from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Base, get_db
from .route import app
import pytest
import responses
from fastapi import status

# Set up the test database
engine = create_engine("postgresql+psycopg2://postgres:123456@localhost:5432/test_cart")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a TestClient instance
client = TestClient(app)

# Overwrite the get_db dependency
def over_write_get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Error in database session: {e}")
    finally:
        db.close()

@pytest.fixture
def db_setup():
    try:
        Base.metadata.create_all(bind=engine)
        yield
    except Exception as e:
        print(f"Error setting up database tables: {e}")
    finally:
        Base.metadata.drop_all(bind=engine)

app.dependency_overrides[get_db] = over_write_get_db

@pytest.fixture
def auth_super_user_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:8000/user/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqYW1lc0BnbWFpbC5jb20iLCJ1c2VyX2lkIjoyLCJleHAiOjE3MzA5MTY3MzV9.iWWKIJgSSoU2Zgy8PQSyNx0FWGJKEowToAVjjQoNg4c",
        json = {
            "message" : "Authorization Successful",
            "status" : "success",
            "data" : {
                    "id": 1,
                    "email": "james@gmail.com",
                    "first_name": "James",
                    "last_name": "Pablo",
                    "is_verified": True,
                    "is_super_user" : True
            }
        },
        status = 200
        )

@pytest.fixture
def auth_regular_user_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:8000/user/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw",
        json={
            "message": "Authorization Successful",
            "status": "success",
            "data": {
                "id": 2,
                "email": "tej@gmail.com",
                "first_name": "Tej",
                "last_name": "Greene",
                "is_verified": True,
                "is_super_user": False
            }
        },
        status=200
    )

@pytest.fixture
def get_book_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:9000/books/1",
        json = {
            "message" : "Book found successfully",
            "status" : "success",
            "data" : 
                {
                "id" : 1,
                "name": "Cartoon Comics",
                "author": "Maddy",
                "description": "Nothing Important",
                "price": 200,
                "stock": 10
            }
            
        },
        status = 200
        )
    
@pytest.fixture
def insufficient_stock_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:9000/books/1",
        json={
            "message": "Book found successfully",
            "status": "success",
            "data": {
                 "id" : 1,
                "name": "Cartoon Comics",
                "author": "Maddy",
                "description": "Nothing Important",
                "price": 200,
                "stock": 5
            }
        },
        status=200
    )

# 1. Test case for adding items in cart
@responses.activate
def test_add_book_to_cart(db_setup , auth_regular_user_mock , get_book_mock):
    # Payload for adding items in cart
    data = {
        "book_id" : 1,
        "quantity" : 2
        }

    # Call the create note API
    response = client.post("/cart/items/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert response.status_code == 201

# 2. Test case for updating the qunatity of books in existing cart
@responses.activate
def test_update_book_in_cart(db_setup, auth_regular_user_mock , get_book_mock ):
    # Add item initially
    data = {
        "book_id": 1, 
        "quantity": 1
        }
    
    # Call the add items in cart API
    add_response = client.post("/cart/items/", json=data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert add_response.status_code == 201

    # Update item quantity
    update_data = {
        "book_id": 1,
        "quantity": 3
        }
    
    update_response = client.post("/cart/items/", json=update_data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert update_response.status_code == 201
    assert update_response.json()["status"] == "success"

# # 3. Test case for adding insufficent stock of book in cart (Error will occured that more quantity is added in cart)
# @responses.activate
# def test_add_insufficient_book(db_setup, auth_regular_user_mock , insufficient_stock_mock ):
#     # Add item initially
#     data = {
#         "book_id": 1, 
#         "quantity": 6
#         }
    
#     # Call the add items in cart API
#     add_response = client.post("/cart/items/", json=data, headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
#     # Assert the response status code and content
#     assert add_response.status_code == status.HTTP_406_NOT_ACCEPTABLE
#     assert add_response.json()["detail"] == "High order quantity than present book stock"

# # 4. Test case for getting cart for particular user (Error will occured that cart is not found)
# @responses.activate
# def test_get_not_active_cart(db_setup, auth_regular_user_mock):

#     # Call the get cart API of get all active cart for user
#     get_cart = client.get("/cart/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
#     # Assert the response status code and content
#     assert get_cart.status_code == 404

# 5. Test case for getting cart for particular user
@responses.activate
def test_get_active_cart(db_setup, auth_regular_user_mock, get_book_mock):
    # Adding items for creating and activating cart
    data = {
        "book_id": 1, 
        "quantity": 5
    }

       # Call the create note API
    response = client.post("/cart/items/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert response.status_code == 201

    # Call the get cart API of get all active cart for user
    get_cart = client.get("/cart/", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert get_cart.status_code == 200

# 6. Test case for deleting the itmes in cart by ID
@responses.activate
def test_delete_cart_item(db_setup, auth_regular_user_mock, get_book_mock):
    # Adding items for creating and activating cart
    data = {
        "book_id": 1, 
        "quantity": 5
    }

       # Call the create note API
    response = client.post("/cart/items/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert response.status_code == 201

    # need to hard code the book id
    book_id = 1

    # Call the delete cart item API
    del_response = client.delete(f"/cart/items?book_id={book_id}", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
    # Assert the response status code and content
    assert del_response.status_code == 200

# 7. Test case for deleting the non existing iem from cart
# @responses.activate
# def test_delete_cart_item_not_found(db_setup, auth_regular_user_mock, get_book_mock, capsys):
#     # Adding items for creating and activating cart
#     data = {
#         "book_id": 1, 
#         "quantity": 5
#     }

#        # Call the create note API
#     response = client.post("/cart/items/", json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
#     # Assert the response status code and content
#     assert response.status_code == 201

#     # Call the delete cart item API
#     del_response = client.delete(f"/cart/items?book_id=16", headers={"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWpAZ21haWwuY29tIiwidXNlcl9pZCI6MywiZXhwIjoxNzMwOTE2ODQzfQ.CzSonwfT_ClbIAxLkkxb9M-rdeNKU5x88Ciuq31rSmw"})
#     # Assert the response status code and content
#     assert del_response.status_code == 404

#     captured = capsys.readouterr()
#     assert "Cart item not found" in captured.out


