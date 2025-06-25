
# schemes.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from datetime import datetime

class ChatMessage(BaseModel):
    user_id: int
    user_name: str
    user_type: str
    id: int
    message: str
    message_type: str
    timestamp: datetime
    userData: Dict[str, Any] = Field(default_factory=dict)
    chatContextNotes: List[str] = Field(default_factory=list)
    coachContext: Dict[str, Any] = Field(default_factory=dict)
