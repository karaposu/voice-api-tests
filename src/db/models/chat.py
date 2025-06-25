# models/chat.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime


from .base import Base  # or wherever your Base is defined



class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # Owner of the chat session
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    settings = Column(JSON, default=dict, nullable=False)

    # Relationship to messages
    messages = relationship('Message', back_populates='chat', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Chat id={self.id} user_id={self.user_id} created_at={self.created_at}>"

