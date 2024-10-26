from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from settings import settings
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException


Base = declarative_base()

engine = create_engine(settings.books_cart_url)
LocalSession = sessionmaker(autoflush=False, autocommit = False, bind=engine)


def get_db():

    db = LocalSession()
    try:
        yield db 
    finally:
        db.close()


class Cart(Base):
    __tablename__ = "cart"

    id = Column(BigInteger, primary_key = True, index=True, autoincrement=True)
    total_price = Column(Integer, default=0)
    total_quantity = Column(Integer, default=0)
    is_ordered = Column(Boolean, default=False)
    user_id = Column(BigInteger, nullable=False)

    items = relationship("CartItem", back_populates='cart')

    @property
    def to_dict(self):
        """
        Converts the `books` object to a dictionary format.
        Returns:
        dict: A dictionary containing all the User attributes.
        """
        try:
            cart_dict = {col.name: getattr(self, col.name) for col in self.__table__.columns}
            # Adding related items to the dictionary
            cart_dict["items"] = [item.to_dict for item in self.items] 
            return cart_dict
        except SQLAlchemyError as error:
            logger.error(f"Error in to_dict method: {error}")
            raise HTTPException(status_code=500, detail="Error processing cart data")


class CartItem(Base):
    __tablename__ = "cart-item"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(BigInteger, nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Integer, default=0)
    cart_id = Column(BigInteger, ForeignKey("cart.id", ondelete='CASCADE'))

    cart = relationship("Cart", back_populates="items")

    @property
    def to_dict(self):
        """
        Converts the `books` object to a dictionary format.
        Returns:
        dict: A dictionary containing all the User attributes.
        """
        try:
            return {col.name: getattr(self, col.name) for col in self.__table__.columns}
        except SQLAlchemyError as error:
            logger.error(f"Error in to_dict method: {error}")
            raise HTTPException(status_code=500, detail="Error processing cart item data")