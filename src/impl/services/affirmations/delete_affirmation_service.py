# impl/services/affirmations/delete_affirmation_service.py

import logging
from fastapi import HTTPException, status
from traceback import format_exc

logger = logging.getLogger(__name__)


class DeleteAffirmationService:
    """
    Service class for deleting an affirmation (soft delete).
    """
    
    def __init__(self, request, dependencies):
        self.request = request
        self.dependencies = dependencies
        self.response = None
        
        logger.debug(f"DeleteAffirmationService initialized for affirmation_id: {request.affirmation_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _verify_ownership(self, affirmation, user_id):
        """Verify that the affirmation belongs to the user."""
        logger.debug(f"Checking ownership: affirmation.user_id={affirmation.user_id} (type: {type(affirmation.user_id)}), user_id={user_id} (type: {type(user_id)})")
        if affirmation.user_id != user_id:
            logger.warning(f"User {user_id} attempted to delete affirmation {affirmation.id} owned by user {affirmation.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this affirmation"
            )
    
    def _preprocess_request_data(self):
        """Validate and soft delete affirmation from database."""
        session = self._get_session()
        try:
            # Get the affirmation repository
            affirmation_repo = self.dependencies.affirmation_repository(session=session)
            
            # Fetch the affirmation to verify it exists and check ownership
            affirmation = affirmation_repo.get_affirmation_by_id(self.request.affirmation_id)
            if not affirmation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Affirmation not found"
                )
            
            # Verify ownership
            self._verify_ownership(affirmation, self.request.user_id)
            
            # Check if already deleted
            if not affirmation.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Affirmation already deleted"
                )
            
            # Perform soft delete
            success = affirmation_repo.delete_affirmation(self.request.affirmation_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete affirmation"
                )
            
            logger.debug(f"Successfully deleted affirmation {self.request.affirmation_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting affirmation: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to delete affirmation")
        finally:
            session.close()
    
    def _process_request(self):
        """Process is complete after deletion - no response body needed."""
        # For DELETE endpoints that return 204, we don't set self.response
        pass