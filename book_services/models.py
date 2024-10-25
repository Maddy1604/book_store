from sqlalchemy import Column, BigInteger, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from settings import settings, logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Base class for all models
Base = declarative_base()

# Engine and session for the database
engine = create_engine(settings.books_db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the DB session
def get_db():
    '''
    Description:
    This function provides a database session to be used for each request. 
    It ensures that the session is properly closed after the request.
    Yields:
    SessionLocal: The database session for querying and interacting with the database.
    Raises:
    Logs any unexpected database connection issues.
    '''
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        raise HTTPException(status_code=500, detail="Internal database error")
    finally:
        try:
            db.close()
            logger.info("Database session closed.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to close the database session: {e}")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    author = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(BigInteger, nullable=False)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    
    @property
    def to_dict(self):
        """
        Converts the `books` object to a dictionary format.
        Returns:
        dict: A dictionary containing all the User attributes.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns}
        except SQLAlchemyError as e:
            logger.error(f"Error in to_dict method: {e}")
            raise HTTPException(status_code=500, detail="Error processing user data")
