
# app/models.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True)

