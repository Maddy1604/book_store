from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger

logger.remove(0)
logger.add("logs/file.log", level="INFO", rotation="100 MB")

class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file='.env', extra="ignore")

    SUPER_USER_KEY : str

    # Database urls
    book_users_url : str
    books_db_url : str
    books_cart_url : str

    JWT_SECRET : str
    JWT_ALGORITHM : str

    ACCESS_TOKEN_EXPIRY : int
    REFRESH_TOKEN_EXPIRY : int
    
    MAIL_USERNAME : str
    MAIL_PASSWORD : str
    MAIL_FROM : str
    MAIL_PORT : int
    MAIL_SERVER : str
    MAIL_FROM_NAME : str
    MAIL_STARTTLS : bool = True
    MAIL_SSL_TLS : bool = False
    USE_CREDENTIALS : bool = True
    VALIDATE_CERTS : bool = True

    # For user_services address 
    ENDPOINT : str

    # For book_services to identify book
    IDENTIFY_BOOK : str
    ORDER_BOOK_STOCK : str
    # CNACLE_BOOK_STOCK : str

settings = Settings()



