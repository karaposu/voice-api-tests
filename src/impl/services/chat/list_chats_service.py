# impl/services/chat/list_chats_service.py
import logging
from traceback import format_exc
from fastapi import HTTPException
from typing import List

logger = logging.getLogger(__name__)


class ListChatsService:
    """
    List all chat IDs for a specific user.

    Steps
    -----
    1. Validate caller supplied `user_id`.
    2. Open a DB session via the DI container.
    3. Use `chat_repository.get_chats_by_user(...)` to fetch all chats.
    4. Extract chat IDs from the result.
    5. Close the session.
    6. Return the list of chat IDs.
    """

    # ──────────────────────────────────────────────────────────────
    # construction
    # ──────────────────────────────────────────────────────────────
    def __init__(self, user_id: int, dependencies):
        self.user_id = user_id
        self.dependencies = dependencies
        self.response = None

        logger.debug("ListChatsService initialised (user_id=%s)", user_id)

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

            # Fetch all chats for the user
            user_chats = chat_repo.get_chats_by_user(user_id=self.user_id)

            # Extract chat IDs
            chat_ids = [chat.id for chat in user_chats]

            logger.debug("Found %d chats for user_id=%s", len(chat_ids), self.user_id)

            # Stash data for use in _process_request
            self.preprocessed_data = {
                "chat_ids": chat_ids
            }

        except Exception as e:
            session.rollback()
            logger.error("Error fetching user chats: %s\n%s", e, format_exc())
            raise HTTPException(status_code=500, detail="Unable to fetch user chats")
        finally:
            session.close()

    def _process_request(self):
        """Build the response - list of chat IDs."""
        self.response = self.preprocessed_data["chat_ids"]