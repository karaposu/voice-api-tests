# impl/services/affirmations/unschedule_affirmation_service.py

import logging
from fastapi import HTTPException, status
from traceback import format_exc

logger = logging.getLogger(__name__)


class UnscheduleAffirmationService:
    """
    Service class for removing schedule from an affirmation.
    """
    
    def __init__(self, request, dependencies):
        self.request = request
        self.dependencies = dependencies
        self.response = None
        
        logger.debug(f"UnscheduleAffirmationService initialized for affirmation_id: {request.affirmation_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _verify_ownership(self, affirmation, user_id):
        """Verify that the affirmation belongs to the user."""
        if affirmation.user_id != user_id:
            logger.warning(f"User {user_id} attempted to unschedule affirmation {affirmation.id} owned by user {affirmation.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to unschedule this affirmation"
            )
    
    def _preprocess_request_data(self):
        """Validate and remove schedule from affirmation."""
        session = self._get_session()
        try:
            # Get the affirmation repository
            affirmation_repo = self.dependencies.affirmation_repository(session=session)
            
            # Fetch the affirmation
            affirmation = affirmation_repo.get_affirmation_by_id(self.request.affirmation_id)
            if not affirmation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Affirmation not found"
                )
            
            # Verify ownership
            self._verify_ownership(affirmation, self.request.user_id)
            
            # Check if affirmation is scheduled
            if not affirmation.schedule_config_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Affirmation is not scheduled"
                )
            
            # Remove schedule by setting schedule_config_id to None
            updated_affirmation = affirmation_repo.update_affirmation(
                affirmation_id=self.request.affirmation_id,
                schedule_config_id=None
            )
            
            # In a real implementation, you might also want to:
            # 1. Delete or deactivate the schedule configuration
            # 2. Cancel any pending notifications
            
            logger.debug(f"Successfully unscheduled affirmation {self.request.affirmation_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error unscheduling affirmation: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to unschedule affirmation")
        finally:
            session.close()
    
    def _process_request(self):
        """Process is complete after unscheduling - no response body needed."""
        # For DELETE endpoints that return 204, we don't set self.response
        pass