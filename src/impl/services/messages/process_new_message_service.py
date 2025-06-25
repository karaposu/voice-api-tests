# impl/services/messages/process_new_message_service.py
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from models.new_message_response import NewMessageResponse
from impl.schemes import ChatMessage               # dataclass used by ChatBackend
from impl.chatbackend import ChatBackend
from db.models.message import Message              # ORM row type

logger = logging.getLogger(__name__)


class ProcessNewMessageService:
    """
    • Persist the user's message
    • Build chat history for the LLM
    • Generate & persist assistant reply
    • Return `NewMessageResponse`
    """

    # ----------------------------
    # construction & public entry
    # ----------------------------
    def __init__(
        self,
        user_id: int,
        chat_id: int,
        new_msg_req,              # models.new_message_request.NewMessageRequest
        *,
        dependencies,
        history_size: int = 4,    # how many past turns to send to the LLM
    ) -> None:
        self.user_id = int(user_id)
        self.chat_id = int(chat_id)
        self.req     = new_msg_req
        self.deps    = dependencies
        self.history_size = history_size

        self.response: Optional[NewMessageResponse] = None

        logger.debug(
            "ProcessNewMessageService(user_id=%s chat_id=%s)", self.user_id, self.chat_id
        )

        self._run()

    # ----------------------------
    # internal helpers
    # ----------------------------
    def _open_session(self):
        return self.deps.session_factory()()

    # ----------------------------
    # main workflow
    # ----------------------------
    def _run(self) -> None:
        session = self._open_session()

        try:
            chat_repo = self.deps.chat_repository(session=session)
            msg_repo  = self.deps.message_repository(session=session)

            # 1 ─ Guard: caller owns the chat
            chat_row = chat_repo.get_chat_by_id(self.chat_id)
            if chat_row is None or chat_row.user_id != self.user_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This chat not found for this user")

            # 2 ─ Persist the user's inbound message
            user_msg_row: Message = msg_repo.insert_message(
                chat_id = self.chat_id,
                user_id = self.user_id,
                user_type = "user",
                user_name     = getattr(self.req, "user_name", "") or "User",
                message   = self.req.message,
                message_format= getattr(self.req, "message_format", "text"),
            )

            # 3 ─ Fetch last `history_size` messages (now includes the new one)
            history_orm = msg_repo.fetch_last_n(
                chat_id = self.chat_id,
                n       = self.history_size,
            )

            # 4 ─ Build ChatBackend & populate history
            backend = ChatBackend(config = chat_row.settings or {})

            for row in history_orm:
                backend.add_message(
                    user_id    = row.user_id,
                    user_name  = row.user_name,
                    user_type  = row.user_type,
                    message    = row.message,
                    message_type = row.message_format or "text",
                    timestamp  = row.timestamp,
                )

            # 5 ─ Generate assistant reply
            ai_text = backend.produce_ai_response(history_count=self.history_size)

            # 6 ─ Persist assistant message
            ai_msg_row: Message = msg_repo.insert_message(
                chat_id = self.chat_id,
                user_id = 0,
                user_type = "assistant",
                user_name = "AI",
                message   = ai_text,
                message_format = "text",
            )

            session.commit()

            # 7 ─ Build outbound response
            self.response = NewMessageResponse(
                message_id=user_msg_row.id,          # ← the user-message primary-key
                timestamp=user_msg_row.timestamp,    # ← when it was persisted
            )
            # self.response = NewMessageResponse(
            #     msg="Message accepted",
            #     message_id=user_msg_row.id,       # ← fill it
            #     timestamp=user_msg_row.timestamp  # ← fill it
            #     user_message_id=user_msg_row.id,
            #     assistant_message_id=ai_msg_row.id,
            #     assistant_text=ai_text,
            # )

            print("self.response:",  self.response)

        except HTTPException:
            raise
        except SQLAlchemyError as exc:
            session.rollback()
            logger.error("DB error while processing new message: %s", exc, exc_info=True)
            raise HTTPException(500, "Database error while posting message")
        except Exception as exc:
            session.rollback()
            logger.error("Unexpected error: %s", exc, exc_info=True)
            raise HTTPException(500, "Internal server error")
        finally:
            session.close()
