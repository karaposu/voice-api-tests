# db/repositories/chat_repository.py
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from fastapi import HTTPException, status

from db.models.chat import Chat
import logging

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, session):
        self.session = session            # sqlalchemy.orm.Session

    # ──────────────────────────────────────────────────────────────
    # public API
    # ──────────────────────────────────────────────────────────────
    def create_chat(self, *, user_id: int, settings: dict | None = None) -> Chat:
        """
        Insert a new chat row and return the ORM instance.

        Parameters
        ----------
        user_id : int
            Owner of the chat session.
        settings : dict | None
            Initial JSON settings (system prompt, model config, …).

        Returns
        -------
        Chat
            The persisted Chat row (with autoincremented `id`).
        """
        settings = settings or {}

        try:
            chat_row = Chat(
                user_id   = user_id,
                settings  = settings,
                created_at= datetime.utcnow(),
            )
            self.session.add(chat_row)
            self.session.commit()       # flush + commit
            self.session.refresh(chat_row)  # ensure we have the generated primary key
            logger.debug("Chat created (id=%s user_id=%s)", chat_row.id, user_id)
            return chat_row

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error("DB error creating chat: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail="Database error while creating chat")
        

    def get_chat_by_id(self, chat_id: int) -> Optional[Chat]:
        """
        Fetch a single Chat row by primary-key ID.

        Returns
        -------
        Chat | None
            The chat if found, else ``None``.  
            Caller decides whether to raise 404.
        """
        try:
            return (
                self.session
                    .query(Chat)
                    .filter(Chat.id == chat_id)
                    .first()
            )
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while fetching chat_id %s: %s", chat_id, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while fetching chat",
            )

    def get_chats_by_user(self, user_id: int) -> list[Chat]:
        """
        Fetch all chats for a specific user.

        Parameters
        ----------
        user_id : int
            The user ID to filter chats by.

        Returns
        -------
        list[Chat]
            List of Chat instances for the user, ordered by creation date (newest first).
        """
        try:
            return (
                self.session
                    .query(Chat)
                    .filter(Chat.user_id == user_id)
                    .order_by(Chat.created_at.desc())
                    .all()
            )
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while fetching chats for user_id %s: %s", user_id, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while fetching user chats",
            )

    def delete_chat(self, chat_id: int, user_id: int) -> bool:
        """
        Delete a chat by ID, ensuring the user owns it.

        Parameters
        ----------
        chat_id : int
            The chat ID to delete.
        user_id : int
            The user ID to verify ownership.

        Returns
        -------
        bool
            True if deleted successfully, False if chat not found or user doesn't own it.
        """
        try:
            # First check if the chat exists and belongs to the user
            chat = (
                self.session
                    .query(Chat)
                    .filter(Chat.id == chat_id)
                    .filter(Chat.user_id == user_id)
                    .first()
            )
            
            if not chat:
                return False
            
            # Delete the chat (cascade will handle related messages)
            self.session.delete(chat)
            self.session.commit()
            logger.debug("Chat deleted (id=%s user_id=%s)", chat_id, user_id)
            return True
            
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while deleting chat_id %s: %s", chat_id, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while deleting chat",
            )
