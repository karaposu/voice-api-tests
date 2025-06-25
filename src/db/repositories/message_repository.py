# db/repositories/message_repository.py
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models.message import Message
import logging

logger = logging.getLogger(__name__)


class MessageRepository:
    def __init__(self, session: Session):
        self.session = session
    
    # ──────────────────────────────────────────────────────────────
    # public api
    # ──────────────────────────────────────────────────────────────
    def fetch_messages(
        self,
        *,
        chat_id: int,
        limit: int = 50,
        offset: int = 0,
        since: Optional[datetime] = None,
    ) -> List[Message]:
        """
        Return messages for a chat (oldest → newest).

        Parameters
        ----------
        chat_id : int
            Target chat identifier.
        limit : int, default 50
            Max rows to return.
        offset : int, default 0
            Skip this many rows.
        since : datetime | None
            If supplied, return only rows with timestamp > `since`.

        Returns
        -------
        list[Message]
        """
        try:
            q = (
                self.session
                .query(Message)
                .filter(Message.chat_id == chat_id)
            )

            if since is not None:
                q = q.filter(Message.timestamp > since)

            messages = (
                q.order_by(Message.timestamp.asc())
                 .offset(offset)
                 .limit(limit)
                 .all()
            )

            logger.debug(
                "Fetched %s messages (chat_id=%s, limit=%s, offset=%s, since=%s)",
                len(messages), chat_id, limit, offset, since
            )
            return messages

        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while fetching messages: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while fetching messages",
            )
        
    
    def insert_message(
        self,
        *,
        chat_id: int,
        user_id: int,
        user_type: str,
        user_name: str,
        message: str,
        message_format: str = "text",
        timestamp: datetime | None = None,
    ) -> Message:
        """Persist a single message row and return the ORM object."""
        ts = timestamp or datetime.utcnow()
        try:
            msg_row = Message(
                chat_id=chat_id,
                user_id=user_id,
                user_type=user_type,
                user_name=user_name,
                message=message,
                message_format=message_format,
                timestamp=ts,
            )
            self.session.add(msg_row)
            self.session.commit()
            self.session.refresh(msg_row)  # populate autoincremented id
            logger.debug("Inserted message id=%s (chat_id=%s)", msg_row.id, chat_id)
            return msg_row
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while inserting message: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while inserting message",
            )

    # ──────────────────────────────────────────────────────────────
    # FETCH last N (helper for ChatBackend history)
    # ──────────────────────────────────────────────────────────────
    def fetch_last_n(self, *, chat_id: int, n: int) -> List[Message]:
        """
        Return the latest *n* messages for a chat (oldest → newest).

        Used by ProcessNewMessageService to build LLM context.
        """
        try:
            rows = (
                self.session.query(Message)
                .filter(Message.chat_id == chat_id)
                .order_by(Message.timestamp.desc())
                .limit(n)
                .all()
            )
            rows.reverse()  # oldest → newest
            return rows
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while fetching last %s messages: %s", n, exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error while fetching messages",
            )
