# impl/services/affirmations/edit_affirmation_service.py

import logging
from fastapi import HTTPException, status
from traceback import format_exc

from models.affirmation.edit_affirmation200_response import EditAffirmation200Response
from models.affirmation.affirmation import Affirmation as AffirmationModel

logger = logging.getLogger(__name__)


class EditAffirmationService:
    """
    Service class for editing an existing affirmation.
    """
    
    def __init__(self, request, affirmation_id: int, user_id: int, dependencies):
        self.request = request
        self.affirmation_id = affirmation_id
        self.user_id = user_id
        self.dependencies = dependencies
        self.response = None
        
        logger.debug(f"EditAffirmationService initialized for affirmation_id: {affirmation_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _verify_ownership(self, affirmation, user_id):
        """Verify that the affirmation belongs to the user."""
        if affirmation.user_id != user_id:
            logger.warning(f"User {user_id} attempted to edit affirmation {affirmation.id} owned by user {affirmation.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this affirmation"
            )
    
    def _preprocess_request_data(self):
        """Validate and update affirmation in database."""
        session = self._get_session()
        try:
            # Get the affirmation repository
            affirmation_repo = self.dependencies.affirmation_repository(session=session)
            
            # Fetch the affirmation
            affirmation = affirmation_repo.get_affirmation_by_id(self.affirmation_id)
            if not affirmation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Affirmation not found"
                )
            
            # Verify ownership
            self._verify_ownership(affirmation, self.user_id)
            
            # Prepare update data (only include fields that are present in the request)
            update_data = {}
            
            if hasattr(self.request, 'text') and self.request.text:
                update_data['content'] = self.request.text.strip()
            
            if hasattr(self.request, 'category'):
                update_data['category'] = self.request.category
            
            if hasattr(self.request, 'voice_enabled'):
                update_data['voice_enabled'] = self.request.voice_enabled
            
            if hasattr(self.request, 'playing_voice'):
                update_data['voice_id'] = self.request.playing_voice
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            # Update the affirmation
            updated_affirmation = affirmation_repo.update_affirmation(
                affirmation_id=self.affirmation_id,
                **update_data
            )
            
            # Extract data while session is still open
            self.updated_affirmation_data = {
                'id': updated_affirmation.id,
                'content': updated_affirmation.content,
                'voice_id': updated_affirmation.voice_id,
                'updated_at': updated_affirmation.updated_at
            }
            
            logger.debug(f"Successfully updated affirmation {self.affirmation_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating affirmation: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to update affirmation")
        finally:
            session.close()
    
    def _process_request(self):
        """Build the response with updated affirmation."""
        # Build response with the expected fields
        self.response = EditAffirmation200Response(
            affirmation_id=str(self.updated_affirmation_data['id']),
            text=self.updated_affirmation_data['content'],
            playing_voice=self.updated_affirmation_data['voice_id'],
            updated_at=self.updated_affirmation_data['updated_at']
        )