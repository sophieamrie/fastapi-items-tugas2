from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Item(Base):
    __tablename__ = "items"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=False, index=True)
    description  = Column(String, nullable=True)
    price        = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)