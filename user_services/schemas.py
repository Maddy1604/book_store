# 1.Pydantic is a Python library used for data validation and settings management using Python type annotations.
# 2.It allows for define data models and validation rule
# 3.Pydantic is heavily used in FastAPI for request and response data validation, 
#   which ensures that the data coming into or going out of your API conforms to the expected structure and type. 
from pydantic import BaseModel, EmailStr, field_validator
import re
from typing import Optional

# Schema for creating a new user
class UserRegistration(BaseModel):
    '''
    Defines a model for user registration. 
    This model inherits from BaseModel and fields are type-annotated.
    '''
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    super_key: str 

    @field_validator("first_name", "last_name")
    def validate_name(cls, value):
        '''
        Discription: This method validates both the first_name and last_name fields.
        Parameters: 
        cls: The class the method is attached to.
        value: The value of the field (either first name or last name) that will be validated.
        Return: Returns the validated value if it passes the check.
        '''
        # Validate first and last names
        if len (value) < 3:
            raise ValueError("Name must contain at least 3 characters")
        return value
        
    @field_validator("email")
    def validate_email(cls, value):
        # Validate email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("Invalid email format")
        return value
    
    @field_validator("password")
    def validate_password(cls, value):
        # Validate password strength
        if len(value) < 8 or not re.search(r'\W', value):
            raise ValueError("Password must contain at least 8 characters and 1 special character")
        return value


# Schema for user login
class UserLogin(BaseModel):
    '''
    This class is used for validating the login request, 
    ensuring that an email and password are provided and in the given format.
    '''
    # id : int
    email: EmailStr
    password: str

    @field_validator("password")
    def validate_password(cls, value):
        # Check if the password is provided (not empty)
        if len(value) == 0:
            raise ValueError("Password cannot be empty")
        return value

