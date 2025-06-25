# db/models/message.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

from .base import Base  # or wherever your Base is defined

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    user_name = Column(String, nullable=True)
    user_type = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    message_format = Column(String, default='text', nullable=True)
    transcription = Column(String, default='text', nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    
    step_context = Column(String, default='text', nullable=True)
    extracted_user_data= Column(String, default='text', nullable=True)
    used_user_data= Column(String, default='text', nullable=True)
    message_owner_emotional_state= Column(String, default='text', nullable=True)
    message_owner_mini_goal= Column(String, default='text', nullable=True)
    message_owner_medium_goal= Column(String, default='text', nullable=True)

    
    # Relationship back to chat
    chat = relationship('Chat', back_populates='messages')
    
    def __repr__(self):
        return f"<Message id={self.id} chat_id={self.chat_id} user={self.user_name}>"
    

# Example engine and session setup
if __name__ == '__main__':
    engine = create_engine('sqlite:///chatbackend.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create a new chat with an owner (user_id=1)
    chat = Chat(user_id=1, settings={'system_prompt': 'You are a coach.'})
    session.add(chat)
    session.commit()

    # Add a message
    msg = Message(
        chat_id=chat.id,
        user_id=1,
        user_name='User',
        user_type='user',
        message='Hello, world!'
    )
    session.add(msg)
    session.commit()
    print(chat, chat.messages)
