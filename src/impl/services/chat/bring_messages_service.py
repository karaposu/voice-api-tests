# impl/services/chat/bring_messages_service.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from models.chat_message import ChatMessage  # Pydantic response model
from db.models.message import Message        # SQLAlchemy ORM model

logger = logging.getLogger(__name__)


class BringMessagesService:
    """
    Load a slice of message history for a given chat.

    Parameters
    ----------
    user_id : int
        Authenticated caller.  Used for an ownership check.
    chat_id : int
        Target chat session.
    dependencies : container
        DI container (session_factory, chat_repository, message_repository, …)
    limit : int, optional
        Max rows to return (default 50).
    offset : int, optional
        Skip this many rows (default 0).
    since : datetime | None, optional
        If supplied, return messages created strictly after this timestamp.
    """

    def __init__(
        self,
        user_id: int,
        chat_id: int,
        *,
        dependencies,
        limit: int = 50,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> None:
        self.user_id = user_id
        self.chat_id = chat_id
        self.dependencies = dependencies
        self.limit = limit
        self.offset = offset
        self.since = since

        self.response: List[ChatMessage] = []

        logger.debug("BringMessagesService(user_id=%s chat_id=%s)", user_id, chat_id)

        self._preprocess_request_data()
        self._process_request()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _get_session(self):
        return self.dependencies.session_factory()()

    # ------------------------------------------------------------------ #
    # Workflow
    # ------------------------------------------------------------------ #

    def _preprocess_request_data(self):
        session = self._get_session()
        try:
            chat_repo = self.dependencies.chat_repository(session=session)
            msg_repo  = self.dependencies.message_repository(session=session)

            # 1 ─ Verify ownership (ensures caller can only read their chats)
            chat_row = chat_repo.get_chat_by_id(self.chat_id)
            if chat_row is None or chat_row.user_id != self.user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat not found",
                )

            # 2 ─ Fetch messages (oldest → newest)
            orm_messages: List[Message] = msg_repo.fetch_messages(
                chat_id=self.chat_id,
                limit=self.limit,
                offset=self.offset,
                since=self.since,
            )

            # 3 ─ Map ORM → Pydantic
            self.preprocessed_data = [
                ChatMessage(
                    message_id = m.id,           
                    chat_id=m.chat_id,
                    user_id=m.user_id,
                    user_name=m.user_name,
                    user_type=m.user_type,
                    message=m.message,
                    message_format=m.message_format,
                    timestamp=m.timestamp,
                )
                for m in orm_messages
            ]

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            session.rollback()
            logger.error("DB error while fetching messages: %s", e, exc_info=True)
            raise HTTPException(status_code=500, detail="Database error")
        finally:
            session.close()

    def _process_request(self):
        # For this simple service, the preprocessed data is already
        # the final response payload.
        self.response = self.preprocessed_data
