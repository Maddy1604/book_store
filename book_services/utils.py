from fastapi import Request, HTTPException
from settings import settings, logger
import requests as http

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

