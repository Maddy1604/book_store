from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from .models import Base, get_db
from .route import app
import pytest
import responses

# Set up the test database
engine = create_engine("postgresql+psycopg2://postgres:123456@localhost:5432/test_books")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a TestClient instance
client = TestClient(app)

# Overwrite the get_db dependency
def over_write_get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

@pytest.fixture
def db_setup():
    Base.metadata.create_all(bind = engine)
    yield 
    Base.metadata.drop_all(bind = engine)

app.dependency_overrides[get_db] = over_write_get_db

@pytest.fixture
def auth_super_user_mock():
    responses.add(
        responses.GET,
        "http://127.0.0.1:8000/user/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk",
        json = {
            "message" : "Authorization Successful",
            "status" : "success",
            "data" : {
                    "id": 1,
                    "email": "mahesh16@gmail.com",
                    "first_name": "Mahesh",
                    "last_name": "Lavande",
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
        "http://127.0.0.1:8000/user/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW1AZ21haWwuY29tIiwidXNlcl9pZCI6MiwiZXhwIjoxNzMwNDgyODUzfQ.UaRzpGJK5NIuvnAXmefYj_qbBX52I3K-12CLiSyK_VQ",
        json={
            "message": "Authorization Successful",
            "status": "success",
            "data": {
                "id": 2,
                "email": "sam@gmail.com",
                "first_name": "Sam",
                "last_name": "Thomson",
                "is_verified": True,
                "is_super_user": False
            }
        },
        status=200
    )

# 1. Test case for super user to create book
@responses.activate
def test_create_book_successful(db_setup, auth_super_user_mock):
    
    # Payload for creating a note
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create note API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert response.status_code == 201

# 2. Test case for regular user can not create the book
@responses.activate
def test_create_book_unsuccessful(db_setup, auth_regular_user_mock):
    
    # Payload for creating a book
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create note API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW1AZ21haWwuY29tIiwidXNlcl9pZCI6MiwiZXhwIjoxNzMwNDgyODUzfQ.UaRzpGJK5NIuvnAXmefYj_qbBX52I3K-12CLiSyK_VQ"})
    # Assert the response status code and content
    assert response.status_code == 403

# 3. Test case for getting the book for all user 
@responses.activate
def test_get_book(db_setup, auth_regular_user_mock, auth_super_user_mock):
    # Payload for creating a book
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create note API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert response.status_code == 201

    # All users are able to fetch book (super_user)
    get_response = client.get("/books/", headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
   
   # All user able to fetch book (Regular user)
    # get_response = client.get("/books/", headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW1AZ21haWwuY29tIiwidXNlcl9pZCI6MiwiZXhwIjoxNzMwNDgyODUzfQ.UaRzpGJK5NIuvnAXmefYj_qbBX52I3K-12CLiSyK_VQ"})
   
    assert get_response.status_code == 200

# 4. Test case for updating the book by super user
@responses.activate
def test_update_book_successful(db_setup, auth_super_user_mock):
    
    # Payload for creating a note
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create note API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert response.status_code == 201
    book_id = response.json()["data"]["id"]

    # Payload for updating book data
    update_data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 500,
        "stock": 5
        }

    # Call the create note API
    put_response = client.put(f"/books/{book_id}",json=update_data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert put_response.status_code == 200

# 5. Test case that regular user try to update the book 
@responses.activate
def test_update_book_unsuccessful(db_setup, auth_super_user_mock, auth_regular_user_mock):
    
    # Payload for creating a note
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create note API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert response.status_code == 201
    book_id = response.json()["data"]["id"]

    # Payload for updating book data
    update_data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 500,
        "stock": 5
        }

    # Call the create note API
    put_response = client.put(f"/books/{book_id}",json=update_data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW1AZ21haWwuY29tIiwidXNlcl9pZCI6MiwiZXhwIjoxNzMwNDgyODUzfQ.UaRzpGJK5NIuvnAXmefYj_qbBX52I3K-12CLiSyK_VQ"})
    # Assert the response status code and content
    assert put_response.status_code == 403

# 6. Test case for super user able to delete the existing book
@responses.activate
def test_delete_book_successful(db_setup, auth_super_user_mock):
    
    # Payload for creating a note
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create book API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert response.status_code == 201
    book_id = response.json()["data"]["id"]

    # Call the delete book API
    del_response = client.delete(f"/books/{book_id}", headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert del_response.status_code == 200

# 7. Test case for regular user can not able to delete the book 
@responses.activate
def test_delete_book_unsuccessful(db_setup, auth_super_user_mock, auth_regular_user_mock):
    
    # Payload for creating a note
    data = {
        "name": "Cartoon comics",
        "author": "Mahesh",
        "description": "Nothing important",
        "price": 200,
        "stock": 10
        }

    # Call the create book API
    response = client.post("/books/",json=data, headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYWhlc2gxNkBnbWFpbC5jb20iLCJ1c2VyX2lkIjoxLCJleHAiOjE3MzA0ODIwNzJ9.JV1-O79sw8kd3FzK9evxhi0WaJo2aHVtB-uLkVNKilk"})
    # Assert the response status code and content
    assert response.status_code == 201
    book_id = response.json()["data"]["id"]

    # Call the delete book API
    del_response = client.delete(f"/books/{book_id}", headers= {"Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYW1AZ21haWwuY29tIiwidXNlcl9pZCI6MiwiZXhwIjoxNzMwNDgyODUzfQ.UaRzpGJK5NIuvnAXmefYj_qbBX52I3K-12CLiSyK_VQ"})
    # Assert the response status code and content
    assert del_response.status_code == 403
