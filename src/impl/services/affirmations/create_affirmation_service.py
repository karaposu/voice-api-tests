# impl/services/affirmations/create_affirmation_service.py

import logging
from fastapi import HTTPException
from traceback import format_exc

from models.affirmation.create_affirmation201_response import CreateAffirmation201Response
from models.affirmation.affirmation import Affirmation as AffirmationModel

logger = logging.getLogger(__name__)


class CreateAffirmationService:
    """
    Service class for creating a new user-generated affirmation.
    This handles direct affirmation creation (not AI-generated).
    """
    
    def __init__(self, request, user_id: int, dependencies):
        self.request = request
        self.user_id = user_id
        self.dependencies = dependencies
        self.response = None
        
        logger.debug(f"CreateAffirmationService initialized for user_id: {user_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _preprocess_request_data(self):
        """Validate request and prepare data for database insertion."""
        # Validate text is not empty
        if not self.request.text or not self.request.text.strip():
            raise HTTPException(status_code=400, detail="Affirmation text cannot be empty")
        
        # Clean and prepare the data
        self.prepared_data = {
            'content': self.request.text.strip(),  # Map 'text' from request to 'content' for DB
            'category': getattr(self.request, 'category', None),
            'voice_enabled': getattr(self.request, 'voice_enabled', False),
            'voice_id': getattr(self.request, 'voice_id', None)
        }
        
        logger.debug(f"Prepared affirmation data: {self.prepared_data}")
    
    def _save_affirmation_to_db(self):
        """Save the affirmation to the database using the repository."""
        session = self._get_session()
        try:
            # Get the affirmation repository
            affirmation_repo = self.dependencies.affirmation_repository(session=session)
            
            # Create the affirmation in the database
            affirmation = affirmation_repo.create_affirmation(
                user_id=self.user_id,
                **self.prepared_data
            )
            
            return affirmation
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving affirmation to database: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to save affirmation")
        finally:
            session.close()
    
    def _process_request(self):
        """Process the request and build the response."""
        # Save to database
        affirmation = self._save_affirmation_to_db()
        
        # Convert SQLAlchemy model to Pydantic response model
        affirmation_response = AffirmationModel(
            id=affirmation.id,
            content=affirmation.content,
            category=affirmation.category,
            voice_enabled=affirmation.voice_enabled,
            voice_id=affirmation.voice_id,
            is_active=affirmation.is_active,
            created_at=affirmation.created_at.isoformat() if affirmation.created_at else None,
            updated_at=affirmation.updated_at.isoformat() if affirmation.updated_at else None
        )
        
        self.response = CreateAffirmation201Response(
            affirmation_id=str(affirmation.id),
            text=affirmation.content,
            created_at=affirmation.created_at
        )