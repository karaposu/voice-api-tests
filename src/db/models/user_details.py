# here is db/models/user_details.py


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

from typing import Optional, Dict, Any, List



class UserDetails(Base):
    __tablename__ = 'user_details'
    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    login_time_logs = relationship(
        "LoginTimeLog",
        back_populates="user_details",
        cascade="all, delete-orphan"
    )
    
    @property
    def last_login_at(self) -> Optional[datetime]:
        """Returns the latest login datetime."""
        if not self.login_time_logs:
            return None
        return max(log.login_datetime for log in self.login_time_logs)
    
    user = relationship("User", back_populates="user_details")
    # user = relationship("User", back_populates="settings")