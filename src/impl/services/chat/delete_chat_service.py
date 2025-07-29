# impl/services/chat/delete_chat_service.py
import logging
from traceback import format_exc
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class DeleteChatService:
    """
    Delete a chat session by ID.

    Steps
    -----
    1. Validate caller supplied `user_id` and `chat_id`.
    2. Open a DB session via the DI container.
    3. Use `chat_repository.delete_chat(...)` to delete the chat.
    4. Ensure user owns the chat before deletion.
    5. Close the session.
    6. Return 204 No Content on success, 404 if not found or not owned.
    """

    # ──────────────────────────────────────────────────────────────
    # construction
    # ──────────────────────────────────────────────────────────────
    def __init__(self, chat_id: int, user_id: int, dependencies):
        self.chat_id = chat_id
        self.user_id = user_id
        self.dependencies = dependencies
        self.response = None

        logger.debug("DeleteChatService initialised (chat_id=%s, user_id=%s)", chat_id, user_id)

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
        if not self.chat_id:
            raise HTTPException(status_code=400, detail="Missing chat_id")
        if not self.user_id:
            raise HTTPException(status_code=400, detail="Missing user_id")

        # Providers from the DI container
        chat_repo_provider = self.dependencies.chat_repository

        session = self._open_session()
        try:
            chat_repo = chat_repo_provider(session=session)

            # Delete the chat (verifies ownership)
            deleted = chat_repo.delete_chat(
                chat_id=self.chat_id,
                user_id=self.user_id
            )

            if not deleted:
                # Chat not found or user doesn't own it
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat not found or access denied"
                )

            logger.debug("Chat deleted successfully (id=%s)", self.chat_id)

            # Stash data for use in _process_request
            self.preprocessed_data = {
                "deleted": True
            }

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            session.rollback()
            logger.error("Error deleting chat: %s\n%s", e, format_exc())
            raise HTTPException(status_code=500, detail="Unable to delete chat")
        finally:
            session.close()

    def _process_request(self):
        """Build the response - None for 204 No Content."""
        # For DELETE endpoints returning 204, we don't need to set a response
        self.response = None