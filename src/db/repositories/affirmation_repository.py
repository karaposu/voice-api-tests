# db/repositories/affirmation_repository.py

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from db.models.affirmation import Affirmation

logger = logging.getLogger(__name__)


class AffirmationRepository:
    """
    Repository class for handling Affirmation database operations.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_affirmation(self, user_id: int, content: str, category: Optional[str] = None,
                          voice_enabled: bool = False, voice_id: Optional[str] = None) -> Affirmation:
        """
        Create a new affirmation for a user.
        
        Args:
            user_id: The ID of the user creating the affirmation
            content: The affirmation text content
            category: Optional category for the affirmation
            voice_enabled: Whether voice is enabled for this affirmation
            voice_id: Optional voice ID for TTS
            
        Returns:
            The created Affirmation object
        """
        try:
            affirmation = Affirmation(
                user_id=user_id,
                content=content,
                category=category,
                voice_enabled=voice_enabled,
                voice_id=voice_id,
                is_active=True,
                how_many_times_seen=0
            )
            
            self.session.add(affirmation)
            self.session.commit()
            self.session.refresh(affirmation)
            
            logger.debug(f"Created affirmation with ID: {affirmation.id}")
            return affirmation
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating affirmation: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create affirmation")
    
    def get_affirmation_by_id(self, affirmation_id: int) -> Optional[Affirmation]:
        """
        Get an affirmation by its ID.
        
        Args:
            affirmation_id: The ID of the affirmation
            
        Returns:
            The Affirmation object if found, None otherwise
        """
        try:
            return self.session.query(Affirmation).filter_by(id=affirmation_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error fetching affirmation: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch affirmation")
    
    def get_user_affirmations(self, user_id: int, category: Optional[str] = None,
                             scheduled_only: bool = False) -> List[Affirmation]:
        """
        Get all affirmations for a user with optional filters.
        
        Args:
            user_id: The ID of the user
            category: Optional category filter
            scheduled_only: If True, only return affirmations with schedule_config_id
            
        Returns:
            List of Affirmation objects
        """
        try:
            query = self.session.query(Affirmation).filter_by(user_id=user_id, is_active=True)
            
            if category:
                query = query.filter_by(category=category)
            
            if scheduled_only:
                query = query.filter(Affirmation.schedule_config_id.isnot(None))
            
            return query.order_by(Affirmation.created_at.desc()).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching user affirmations: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch affirmations")
    
    def update_affirmation(self, affirmation_id: int, **kwargs) -> Optional[Affirmation]:
        """
        Update an affirmation with the provided fields.
        
        Args:
            affirmation_id: The ID of the affirmation to update
            **kwargs: Fields to update
            
        Returns:
            The updated Affirmation object if found, None otherwise
        """
        try:
            affirmation = self.get_affirmation_by_id(affirmation_id)
            if not affirmation:
                return None
            
            # Update allowed fields
            updateable_fields = ['content', 'category', 'voice_enabled', 'voice_id', 
                               'schedule_config_id', 'is_active']
            
            for field, value in kwargs.items():
                if field in updateable_fields and value is not None:
                    setattr(affirmation, field, value)
            
            # Update the updated_at timestamp
            affirmation.updated_at = datetime.utcnow()
            
            self.session.commit()
            self.session.refresh(affirmation)
            
            logger.debug(f"Updated affirmation ID: {affirmation_id}")
            return affirmation
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating affirmation: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update affirmation")
    
    def delete_affirmation(self, affirmation_id: int) -> bool:
        """
        Soft delete an affirmation by setting is_active to False.
        
        Args:
            affirmation_id: The ID of the affirmation to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            affirmation = self.get_affirmation_by_id(affirmation_id)
            if not affirmation:
                return False
            
            affirmation.is_active = False
            affirmation.updated_at = datetime.utcnow()
            
            self.session.commit()
            logger.debug(f"Soft deleted affirmation ID: {affirmation_id}")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting affirmation: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete affirmation")
    
    def update_affirmation_stats(self, affirmation_id: int, seen: bool = False, played: bool = False) -> Optional[Affirmation]:
        """
        Update affirmation statistics (times seen, last seen, last played).
        
        Args:
            affirmation_id: The ID of the affirmation
            seen: If True, increment times seen and update last_time_seen
            played: If True, update last_time_played
            
        Returns:
            The updated Affirmation object if found, None otherwise
        """
        try:
            affirmation = self.get_affirmation_by_id(affirmation_id)
            if not affirmation:
                return None
            
            now = datetime.utcnow()
            
            if seen:
                affirmation.how_many_times_seen = (affirmation.how_many_times_seen or 0) + 1
                affirmation.last_time_seen = now
            
            if played:
                affirmation.last_time_played = now
            
            affirmation.updated_at = now
            
            self.session.commit()
            self.session.refresh(affirmation)
            
            logger.debug(f"Updated stats for affirmation ID: {affirmation_id}")
            return affirmation
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating affirmation stats: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update affirmation stats")