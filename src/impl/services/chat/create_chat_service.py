# impl/services/chat/create_chat_service.py
import logging
from datetime import datetime
from traceback import format_exc
from fastapi import HTTPException

from models.chat_post201_response import ChatPost201Response  # adjust if the name differs

logger = logging.getLogger(__name__)


class CreateChatService:
    """
    Create a new chat row and return its identifier.

    Steps
    -----
    1. Validate caller supplied `user_id`.
    2. Open a DB session via the DI container.
    3. Use `chat_repository.create_chat(...)` to insert the row.
    4. Commit → close the session.
    5. Build the `ChatPost201Response`.
    """

    # ──────────────────────────────────────────────────────────────
    # construction
    # ──────────────────────────────────────────────────────────────
    def __init__(self, user_id: int, dependencies):
        self.user_id = user_id
        self.dependencies = dependencies
        self.response = None

        logger.debug("CreateChatService initialised (user_id=%s)", user_id)

        self._preprocess_request_data()
        self._process_request()

    # ──────────────────────────────────────────────────────────────
    # helpers
    # ──────────────────────────────────────────────────────────────
    def _open_session(self):
        """Return a fresh SQLAlchemy Session object."""
        session_factory = self.dependencies.session_factory()
        return session_factory()                      # type: sqlalchemy.orm.Session

    # ──────────────────────────────────────────────────────────────
    # main workflow
    # ──────────────────────────────────────────────────────────────
    def _preprocess_request_data(self):
        if not self.user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")

        # Providers from the DI container
        chat_repo_provider = self.dependencies.chat_repository

        session = self._open_session()
        try:
            chat_repo = chat_repo_provider(session=session)

            # Default settings; tweak as necessary
            default_settings = {
                "system_prompt": "You are a helpful assistant."
            }

            # Insert the new chat
            chat_row = chat_repo.create_chat(
                user_id=self.user_id,
                settings=default_settings
            )

            session.commit()
            logger.debug("Chat created (id=%s)", chat_row.id)

            # Stash data for use in _process_request
            self.preprocessed_data = {
                "chat_id": chat_row.id,
                "created_at": chat_row.created_at,
            }

        except Exception as e:
            session.rollback()
            logger.error("Error creating chat: %s\n%s", e, format_exc())
            raise HTTPException(status_code=500, detail="Unable to create chat")
        finally:
            session.close()

    def _process_request(self):
        """Build the FastAPI response model."""
        self.response = ChatPost201Response(
            chat_id=self.preprocessed_data["chat_id"],
            created_at=self.preprocessed_data["created_at"].isoformat(),
            msg="Chat created"
        )
