
# db/models/login_time_log.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base  # or wherever your Base is defined

class LoginTimeLog(Base):
    __tablename__ = 'login_time_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_id = Column(Integer, ForeignKey('user_details.setting_id'), nullable=False)
    login_datetime = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship back to UserDetails
    user_details = relationship("UserDetails", back_populates="login_time_logs")
