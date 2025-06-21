# impl/services/user/profile_service.py
import logging
from traceback import format_exc
from datetime import datetime
from fastapi import HTTPException

from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)


class ChatService:
    """
    
    """

    def __init__(self, request, dependencies):
        self.request = request            # expects .user_id
        self.dependencies = dependencies  # container with session_factory / user_repository
        self.response = None

        logger.debug("Inside ChatService")

        self.preprocess_request_data()
        self.process_request()

    # ──────────────────────────────────────────────────────────────
    # main work happens here
    # ──────────────────────────────────────────────────────────────
    def preprocess_request_data(self):
        """
        Loads the user row (and settings) and prepares a
        GetUserProfile200Response instance.
        """
        logger.debug("Inside UserProfileService.preprocess_request_data")
        try:
            # 1.  Extract parameters carried on the lightweight request object
            user_id = self.request.user_id
            logger.debug("user_id: %s", user_id)

            # 2.  Grab session-factory & repo providers from DI container
            session_factory          = self.dependencies.session_factory()
            user_repository_provider = self.dependencies.user_repository
            # chat_repository_provider = self.dependencies.chat_repository

            # 3.  Open a DB session
            session = session_factory()
            try:
                logger.debug("DB session opened for user profile retrieval")

                # 4.  Instantiate repository
                user_repo = user_repository_provider(session=session)

                # 5.  Fetch main user row
                user_row = user_repo.get_user_profile(user_id)
                if not user_row:
                    logger.error("User %s not found", user_id)
                    raise HTTPException(status_code=404, detail="User not found")

                # # 6.  Fetch settings row (may be None)
                # settings_row = user_repo.get_user_settings(user_id)

                # 7.  Convert settings → pydantic (if present)
                # settings_out = (
                #     GetUserProfile200ResponseSettings.model_validate(
                #         settings_row, from_attributes=True
                #     )
                #     if settings_row
                #     else None
                # )

                # 8.  Build final response object

                profile_out = GetUserProfile200Response(
                    email        = user_row.email,
                    name         = None,
                    plan         = None,
                    upload_limit = None,
                    settings     = None,
                    created_at   = None,
                    updated_at   = None
                )
                # profile_out = GetUserProfile200Response(
                #     email        = user_row.email,
                #     name         = user_row.name,
                #     plan         = getattr(user_row, "plan", None),
                #     upload_limit = getattr(user_row, "upload_limit", None),
                #     settings     = settings_out,
                #     created_at   = user_row.created_at.isoformat() if user_row.created_at else None,
                #     updated_at   = user_row.updated_at.isoformat() if user_row.updated_at else None,
                # )

                self.preprocessed_data = profile_out

            except SQLAlchemyError as db_exc:
                session.rollback()
                logger.error(
                    "DB error while building user profile: %s\n%s",
                    db_exc, format_exc()
                )
                raise HTTPException(status_code=500, detail="Database error")
            finally:
                session.close()

        except HTTPException as http_exc:
            raise http_exc  # Let FastAPI handle it
        except Exception as e:
            logger.error("Unexpected error: %s\n%s", e, format_exc())
            raise HTTPException(status_code=500, detail="Internal server error")

    # ──────────────────────────────────────────────────────────────
    # delivers the prepared payload
    # ──────────────────────────────────────────────────────────────
    def process_request(self):
        self.response = self.preprocessed_data
