# Importing required liberaries and moduels
from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from .models import User, get_db
from .schemas import UserRegistration, UserLogin 
from .utils import hash_password, verify_password, create_token, create_tokens
from settings import settings
from .emails import send_verification_email
import jwt
from loguru import logger
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI()

# Defined the super key
SUPER_USER_KEY = settings.SUPER_USER_KEY 

# Initialize the limiter with a rate limit of 5 requests per minute per user
limiter = Limiter(key_func=get_remote_address)

# Register the rate limit exception handler
app.state.limiter = limiter

# # Custom rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Handles rate limiting exceptions and returns a custom response when the limit is exceeded.
    """
    return JSONResponse(
        status_code=429,
        content={
            "message": "Rate limit exceeded. Please try again later.",
            "detail": f"You have exceeded the allowed number of requests. Try again after some time."
        }
    )

# Simple get api with response
@app.get("/")
@limiter.limit("100/minute")  
def read_root(request: Request):    
    '''
    Discription: This is the handler function that gets called when a request is made to the root endpoint
    Parameters: None
    Return: A dictionary with a welcome message.
    '''
    return {"message": "Welcome to the Fundoo Notes API!"}

# Register a new user
@app.post("/register", status_code=201)
@limiter.limit("100/minute") 
def register_user(request: Request, user: UserRegistration, db: Session = Depends(get_db)):
    '''
    Discription: Registers a new user after validating the input, checking if the user exists, 
    hashing the password, and storing the user in the database.
    Parameters: 
    request: Request: Provides information about the HTTP request, which is used to generate the email verification link.
    user: UserRegistration: The request body is validated using the UserRegistration, 
    which ensures that all required fields are correctly formatted.
    db: Session = Depends(get_db): Uses dependency injection to pass the current database session to the function.
    Return: Returns a JSON response with a success message and the registered user's data 
    (using the to_dict() method of the User model).
    '''
    try:
        # Check if the user already exists by email
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.info("Email already registered")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Hash the user's password
        hashed_password = hash_password(user.password)
        logger.info("User password is hased successfully.")

        # Checking user super key is matched with defined super key
        is_super_user = False  
        if user.super_key == SUPER_USER_KEY:
            is_super_user = True  
            logger.info(f"User is being marked as a super user because the provided super key matches.")

        # Create a new User object
        db_user = User(
            email=user.email, 
            password=hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            is_super_user = is_super_user
        )
        
        # Add the user to the database and commit the transaction
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info("User is created and stored in database successfully.")
        
        # Generate the access token where subject use as key and user entered email as value 
        access_token = create_token({"sub": db_user.email}, "access")
        logger.info("Access token is generated contains subject as user email.")

        # Generate verification link using request url_for function taking token as access_token 
        verify_link = request.url_for('verify_registered_user', token= access_token)
        logger.info("Verification link is genereated contained access token")

        # Celery task for sending verification mail to newly registered user to their email address
        send_verification_email(db_user.email, str(verify_link))
        logger.info(f"Verifiction email is send to user at user email: {user.email}")
        
        # Return the success message
        return {
            "message": "User registered successfully",
            "status": "success",
            "data": db_user.to_dict,
            "access_token": access_token
        }
    
    except Exception as error:
        logger.error(f"Error while registering new user : {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error while registring new user.")

#  Post api for User login
@app.post("/login", status_code=201)
@limiter.limit("100/minute") 
def login_user(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    '''
    Discription:  Logs in a user by verifying their email and password against the database, 
    returning a success message if they match.
    Parameters: 
    user: UserLogin : The request body is validated using the UserLogin (email and password).
    db: Session = Depends(get_db): Dependency injection is used to get a database session via the get_db function.
    Return: If the email and password match, a success message is returned, along with the logged-in user's data.
    '''
    try:
        # Check if the user exists in the database by email
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or not verify_password(user.password, db_user.password):
            logger.info("Invalid email or password")
            raise HTTPException(status_code=400, detail="Invalid email or password")

        # Generate both JWT tokens
        access_token, refresh_token = create_tokens({"sub": db_user.email, "user_id": db_user.id})
        logger.info("Generating access token and refresh token using using user email and user ID")

        # Return the success message
        return {
            "message": "Login successful",
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "data": db_user.to_dict
        }

    except Exception as error:
        logger.error(f"Error while user credentials not match with database: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error while user credentials not match with database.")


# Get api for verifying user with generated acccess token
@app.get("/verify/{token}")
@limiter.limit("100/minute") 
def verify_registered_user(request: Request, token: str, db: Session = Depends(get_db)):
    '''
    Discription:  Verifiying user access token and access the resource, 
    returning a success message if they match.
    Parameters: 
    token : str: takes user access token for verifyinh the user.
    db: Session = Depends(get_db): Dependency injection is used to get a database session via the get_db function.
    Return: If the email and password match, a success message is returned, along with the logged-in user's data.
    '''
    try:
        # Decode the token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email = payload.get("sub")

        if email is None:
            logger.info("Invalid token")
            raise HTTPException(status_code=400, detail="Invalid token")

        # Fetch the user from the database
        user = db.query(User).filter(User.email == email).first()
        logger.info("Fetching user with user email.")

        # If user is not found in database
        if not user:
            logger.info("User is not found in database.")
            raise HTTPException(status_code=404, detail="User not found")

        # Mark user as verified
        if user.is_verified:
            logger.info("User is already verified in database.")
            return {"message": "User is already verified"}
    
        # Verify the user
        user.is_verified = True
        db.commit()
        logger.info("User is successfully verified and chages saved in database")

        return {"message": "Email verified successfully!"}

    except Exception as error:
        logger.error(f"Error while verifying because token has expired or invalid : {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error while verifying because token has expired or invalid.")


# Get api for creating endpoint with token which return status code success and include_in_schema = false given
# particular route (/user/{token}) will not appear in the auto-generated documentation (Swagger UI, Redoc, etc.).

@app.get("/user/{token}",status_code= 200, include_in_schema= False)
@limiter.limit("100/minute") 
def auth_user(request: Request, token: str, db: Session = Depends(get_db)):
    '''
    Discription:  This function verifyies the user email address, 
    returning a success message if they match.
    Parameters: 
    Get api for creating endpoint with token which return status code success and include_in_schema = false given
    particular route (/user/{token}) will not appear in the auto-generated documentation (Swagger UI, Redoc, etc.).
    Return: If the email and password match, a success message is returned, along with the logged-in user's data.
    '''
    try:
        # Decode the JWT token to get payload
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        # print(payload)
        user_id: int = payload.get("user_id")
        if user_id is None:
            logger.info("Invalid User ID")
            raise HTTPException(status_code=401, detail="Invalid User ID")
        
        # Fetch user details from the database based on user_id from token
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            logger.info("User not found")
            raise HTTPException(status_code=404, detail= "User not found")
        
        # Return user details in JSON format
        return {
            "message": "Authorizaton successful",
            "status": "success",
            "data": db_user
        }

    except Exception as error:
        logger.error(f"Error while verifying because invalid token : {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error while verifiying because invalid token.")

# GET api for takes user ids and validate that ids and return the response
@app.get('/users', status_code=200, include_in_schema=False)
@limiter.limit("100/minute") 
def get_users(request: Request, user_ids : List[int] = Query([]), db : Session = Depends(get_db)):
    """
    Description: 
    This function for get http request from note_services and in that request there is list of user ids
    take the list of user ids and validate if there valid user or not. 
    If they are valid users then return the user data.
    Paramenter:
    user_ids : list of user ids which is in query format
    db : session = Depends(get_db): Uses dependency injection to pass the current database session to the function.
    Return:
    Success message if user found its data
    """
    try:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        logger.info("Fetching all payload.user_id users from database")

        if not users:
            logger.info("Some of the user is not found from databse")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found with user Id.")
        
        # It gives the dict of every user of given payload.user_id from database
        users = [user.to_dict for user in users]

        # Return the success meassage
        return {
            "message" : "User found successfully.", 
            "status" : "Success",
            "data" : users
        }
    
    except Exception as error:
        logger.error(f"Error while fetching the users : {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error while fetching the users : {error}")
    
