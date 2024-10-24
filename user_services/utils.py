from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from settings import settings

# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utility function to hash a password
def hash_password(password: str) -> str:
    """
    Description:
    hashed password function hash the user password for privacy puspose.
    password : It take password as string which entered by user
    Return : Returns hash password in string format
    """
    return pwd_context.hash(password)

# Utility function to verify hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Description:
    verify the password that user entered and password that stored in database in hased format.
    Parameters:
    Plain_password : It takes password as string
    hashed_password : It takes hashed passsord as string
    Return : Boolean true or false
    """
    
    return pwd_context.verify(plain_password, hashed_password)

# Unified Token Generation Function
def create_token(data: dict, token_type: str, exp= None):
    """
    Description:
    Sends a verification email to the user.
    Parameters:
    email : The email address of the user to send the verification link to.
    verify_link : The verification link to be included in the email.
    """
    if token_type == "access":
        expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY))
    elif token_type == "refresh":
        expiration = exp or (datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRY))
    else:
        raise ValueError("Invalid token type. Must be 'access' or 'refresh'.")

    return jwt.encode({**data, "exp": expiration}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

# To generate both tokens
def create_tokens(data: dict):
    """
    Generates both access and refresh tokens.
    """
    access_token = create_token(data, "access")
    refresh_token = create_token(data, "refresh")
    return access_token, refresh_token
