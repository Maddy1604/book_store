# 1.SQLAlchemy in FastAPI is used to simplify database interactions by providing an ORM that allows 
# developers to manage database records using Python objects instead of raw SQL queries.
# 2. It healps to complex database queries and seesion management and integrate seamlessly with fastapi injection

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from settings import settings

# Base object with assigning with declarative base
Base = declarative_base()

# creating engine and assigning create engine module with database url which is stored in .env File
# and in setting file is mentioned as string
engine = create_engine(settings.book_users_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creating Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()

# Creating a class User with base as parameter in this table stuructre is going to define
class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_super_user = Column(Boolean, default=False)

    # property is used for return data in dictionary format
    @property
    def to_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns if col.name != "password"} 

