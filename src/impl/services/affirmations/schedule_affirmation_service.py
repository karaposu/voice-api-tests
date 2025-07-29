# impl/services/affirmations/schedule_affirmation_service.py

import logging
from fastapi import HTTPException, status
from traceback import format_exc

from models.affirmation.schedule_affirmation200_response import ScheduleAffirmation200Response
from models.affirmation.schedule_config import ScheduleConfig

logger = logging.getLogger(__name__)


class ScheduleAffirmationService:
    """
    Service class for scheduling an affirmation with notification settings.
    """
    
    def __init__(self, request, dependencies):
        self.request = request
        self.dependencies = dependencies
        self.response = None
        
        logger.debug(f"ScheduleAffirmationService initialized for affirmation_id: {request.affirmation_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _verify_ownership(self, affirmation, user_id):
        """Verify that the affirmation belongs to the user."""
        if affirmation.user_id != user_id:
            logger.warning(f"User {user_id} attempted to schedule affirmation {affirmation.id} owned by user {affirmation.user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to schedule this affirmation"
            )
    
    def _create_or_update_schedule_config(self, schedule_data):
        """
        Create or update schedule configuration.
        Note: This is a placeholder - in a real implementation, you would:
        1. Have a separate ScheduleConfig table/model
        2. Create or update the schedule configuration
        3. Return the schedule_config_id
        """
        # For now, we'll simulate by returning a dummy ID
        # In real implementation, this would interact with a scheduling service/table
        return 1  # Dummy schedule_config_id
    
    def _preprocess_request_data(self):
        """Validate and set schedule for affirmation."""
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
            
            # Validate schedule data
            if not hasattr(self.request, 'schedule') or not self.request.schedule:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Schedule configuration is required"
                )
            
            # Create or update schedule configuration
            schedule_config_id = self._create_or_update_schedule_config(self.request.schedule)
            
            # Update affirmation with schedule_config_id
            updated_affirmation = affirmation_repo.update_affirmation(
                affirmation_id=self.request.affirmation_id,
                schedule_config_id=schedule_config_id
            )
            
            self.schedule_config_id = schedule_config_id
            logger.debug(f"Successfully scheduled affirmation {self.request.affirmation_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error scheduling affirmation: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to schedule affirmation")
        finally:
            session.close()
    
    def _process_request(self):
        """Build the response with schedule information."""
        # Build schedule config response
        # In a real implementation, this would fetch from the schedule config table
        schedule_config = ScheduleConfig(
            id=self.schedule_config_id,
            days=getattr(self.request.schedule, 'days', []),
            times=getattr(self.request.schedule, 'times', []),
            timezone=getattr(self.request.schedule, 'timezone', 'UTC'),
            is_active=True
        )
        
        self.response = ScheduleAffirmation200Response(
            message="Affirmation scheduled successfully",
            schedule_config=schedule_config
        )