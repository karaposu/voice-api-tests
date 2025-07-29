# impl/services/affirmations/get_affirmations_service.py

import logging
from fastapi import HTTPException
from traceback import format_exc

from models.affirmation.get_affirmations200_response import GetAffirmations200Response
from models.affirmation.affirmation import Affirmation as AffirmationModel

logger = logging.getLogger(__name__)


class GetAffirmationsService:
    """
    Service class for retrieving user's affirmations with optional filters.
    """
    
    def __init__(self, request, dependencies):
        self.request = request
        self.dependencies = dependencies
        self.response = None
        
        logger.debug(f"GetAffirmationsService initialized for user_id: {request.user_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _preprocess_request_data(self):
        """Fetch affirmations from database based on filters."""
        session = self._get_session()
        try:
            # Get the affirmation repository
            affirmation_repo = self.dependencies.affirmation_repository(session=session)
            
            # Extract filters from request
            user_id = self.request.user_id
            category = getattr(self.request, 'category', None)
            scheduled_only = getattr(self.request, 'scheduled_only', False)
            
            logger.debug(f"Fetching affirmations - category: {category}, scheduled_only: {scheduled_only}")
            
            # Fetch affirmations from repository
            affirmations = affirmation_repo.get_user_affirmations(
                user_id=user_id,
                category=category,
                scheduled_only=scheduled_only
            )
            
            self.affirmations = affirmations
            logger.debug(f"Found {len(affirmations)} affirmations for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error fetching affirmations: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to fetch affirmations")
        finally:
            session.close()
    
    def _process_request(self):
        """Build the response with fetched affirmations."""
        # Convert SQLAlchemy models to Pydantic response models
        affirmation_responses = []
        for affirmation in self.affirmations:
            # Determine source based on how it was created
            source = "user_created"  # Default to user_created
            
            affirmation_response = AffirmationModel(
                affirmation_id=str(affirmation.id),
                text=affirmation.content,
                category=affirmation.category,
                source=source,
                playing_voice=affirmation.voice_id,
                is_scheduled=affirmation.schedule_config_id is not None,
                schedule_config=None,  # TODO: Load schedule config if needed
                created_at=affirmation.created_at,
                updated_at=affirmation.updated_at
            )
            affirmation_responses.append(affirmation_response)
        
        self.response = GetAffirmations200Response(
            affirmations=affirmation_responses,
            count=len(affirmation_responses)
        )