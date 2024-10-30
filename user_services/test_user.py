from .route import app
from fastapi.testclient import TestClient
from .models import get_db, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import pytest 

engine = create_engine("postgresql+psycopg2://postgres:123456@localhost:5432/book_users")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

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

# 1. Testing for successfull registration for normal user
def test_user_registration_successful_regular_user(db_setup):
    data = {
        "email": "asha@gmail.com",
        "password": "asha@gmail.com",
        "first_name": "Asha",
        "last_name": "Lavande",
        "super_key": ""  # No super key, registers as a regular user
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json()["data"]["is_super_user"] is False  # Regular user
   
# 2. Testing for successfull registration of super user
def test_user_registration_successful_super_user(db_setup):
    data = {
        "email": "asha@gmail.com",
        "password": "asha@gmail.com",
        "first_name": "Asha",
        "last_name": "Lavande",
        "super_key": "mahesh"  # super key, registers as a super user
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json()["data"]["is_super_user"] is True  # Regular user

# 3. Testing for user with incorrect user key
def test_user_registration_successful_incorrect_key(db_setup):
    data = {
        "email": "asha@gmail.com",
        "password": "asha@gmail.com",
        "first_name": "Asha",
        "last_name": "Lavande",
        "super_key": "ashaa"  # incorrect super key, registers as a regular user
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json()["data"]["is_super_user"] is False  # Regular user

# 4. Test user with correct login Id and Pass
def test_user_login(db_setup):
    # Register user first
    data = {
        "email": "sam@gmail.com",
        "password": "sam@gmail.com",
        "first_name": "Sam",
        "last_name": "Leonardo",
        "super_key": ""  # No super key, registers as a regular user
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json()["data"]["is_super_user"] is False

    login_data = {
        "email" : "sam@gmail.com",
        "password" : "sam@gmail.com"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 201

# 5. Test user with incorrect login Id and Pass
def test_user_login_incorrect_pass(db_setup):
    # Register user first
    data = {
        "email": "sam@gmail.com",
        "password": "sam@gmail.com",
        "first_name": "Sam",
        "last_name": "Leonardo",
        "super_key": "mahesh"  # super key, registers as a super user
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json()["data"]["is_super_user"] is True

    login_data = {
        "email" : "sam@gmail.com",
        "password" : "sam55@gmail.com"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 400

# 6. Verifiying user email by sending token as query parameter to endpoint
def test_fetch_user(db_setup):
    # Register user first
    data = {
        "email": "sam@gmail.com",
        "password": "sam@gmail.com",
        "first_name": "Sam",
        "last_name": "Leonardo",
        "super_key": "mahesh"  # No super key, registers as a regular user
    }
    response = client.post("/register", json=data)
    assert response.status_code == 201
    assert response.json()["data"]["is_super_user"] is True

    login_data = {
        "email" : "sam@gmail.com",
        "password" : "sam@gmail.com"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 201
    token = response.json()["access_token"]
    print(token)

    response = client.get(f"/user/{token}")
    assert response.status_code == 200