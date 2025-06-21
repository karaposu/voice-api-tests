# here is db/models/user.py

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Float, Text,
    ForeignKey, LargeBinary, Boolean, UniqueConstraint, CheckConstraint, or_, func
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash

from .base import Base, get_current_time


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=get_current_time)
    is_verified = Column(Boolean, default=False)
    can_see_admin_panel = Column(Boolean, default=False)


    user_details = relationship(
        "UserDetails",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    
    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"
    

    

