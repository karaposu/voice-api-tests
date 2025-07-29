# impl/services/affirmations/ai_create_affirmations_service.py

import logging
import json
from fastapi import HTTPException
from traceback import format_exc
from typing import List

from models.affirmation.ai_create_affirmations201_response import AiCreateAffirmations201Response
from models.affirmation.affirmation import Affirmation as AffirmationModel
from impl.myllmservice import MyLLMService

logger = logging.getLogger(__name__)


class AiCreateAffirmationsService:
    """
    Service class for creating AI-generated affirmations based on user context.
    """
    
    def __init__(self, request, user_id: int, dependencies):
        self.request = request
        self.user_id = user_id
        self.dependencies = dependencies
        self.response = None
        self.llm_service = MyLLMService()
        
        logger.debug(f"AiCreateAffirmationsService initialized for user_id: {user_id}")
        
        self._preprocess_request_data()
        self._process_request()
    
    def _get_session(self):
        """Get database session from dependencies."""
        return self.dependencies.session_factory()()
    
    def _preprocess_request_data(self):
        """Generate affirmations using LLM based on user context."""
        # Validate request has context
        if not hasattr(self.request, 'context_corpus') or not self.request.context_corpus.strip():
            raise HTTPException(status_code=400, detail="Context is required for AI affirmation generation")
        
        try:
            # Extract request parameters matching the request model field names
            context = self.request.context_corpus.strip()
            category = getattr(self.request, 'affirmation_category', None)
            count = getattr(self.request, 'amount', 5)  # Default to 5 affirmations
            style = self.request.style  # Required field
            uslub = self.request.uslub  # Required field
            
            # Call the LLM service method
            result = self.llm_service.generate_affirmations_with_llm(
                context=context,
                category=category,
                count=count
            )
            
            if not result.success:
                logger.error(f"LLM generation failed: {result.error_message}")
                raise HTTPException(status_code=500, detail="Failed to generate affirmations")
            
            # Parse the LLM response
            affirmations_data = result.content
            if isinstance(affirmations_data, str):
                affirmations_data = json.loads(affirmations_data)
            
            # Add additional fields to each affirmation
            for affirmation in affirmations_data:
                if category:
                    affirmation['category'] = category
                affirmation['voice_enabled'] = getattr(self.request, 'voice_enabled', False)
                affirmation['voice_id'] = getattr(self.request, 'voice_id', None)
            
            self.generated_affirmations = affirmations_data
            logger.debug(f"Generated {len(self.generated_affirmations)} affirmations from LLM")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise HTTPException(status_code=500, detail="Invalid response from AI service")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating affirmations with LLM: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to generate affirmations")
    
    def _save_affirmations_to_db(self, affirmations_data: List[dict]) -> List[dict]:
        """Save multiple affirmations to the database and return their data."""
        session = self._get_session()
        created_affirmations_data = []
        
        try:
            # Get the affirmation repository
            affirmation_repo = self.dependencies.affirmation_repository(session=session)
            
            # Create each affirmation in the database
            for affirmation_data in affirmations_data:
                affirmation = affirmation_repo.create_affirmation(
                    user_id=self.user_id,
                    content=affirmation_data['content'],
                    category=affirmation_data.get('category'),
                    voice_enabled=affirmation_data.get('voice_enabled', False),
                    voice_id=affirmation_data.get('voice_id')
                )
                
                # Extract data while session is still open
                affirmation_dict = {
                    'id': affirmation.id,
                    'content': affirmation.content,
                    'category': affirmation.category,
                    'voice_id': affirmation.voice_id,
                    'created_at': affirmation.created_at,
                    'updated_at': affirmation.updated_at
                }
                created_affirmations_data.append(affirmation_dict)
            
            logger.debug(f"Created {len(created_affirmations_data)} affirmations for user {self.user_id}")
            return created_affirmations_data
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving affirmations to database: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to save affirmations")
        finally:
            session.close()
    
    def _process_request(self):
        """Save generated affirmations and build the response."""
        # Save to database
        saved_affirmations = self._save_affirmations_to_db(self.generated_affirmations)
        
        # Convert saved data to Pydantic response models
        affirmation_responses = []
        affirmation_ids = []
        
        for affirmation_data in saved_affirmations:
            # Build the affirmation response using the correct field names
            affirmation_response = AffirmationModel(
                affirmation_id=str(affirmation_data['id']),
                text=affirmation_data['content'],
                category=affirmation_data['category'],
                source="ai_generated",  # Mark as AI generated
                playing_voice=affirmation_data['voice_id'],
                is_scheduled=False,
                schedule_config=None,
                created_at=affirmation_data['created_at'],
                updated_at=affirmation_data['updated_at']
            )
            affirmation_responses.append(affirmation_response)
            affirmation_ids.append(str(affirmation_data['id']))
        
        self.response = AiCreateAffirmations201Response(
            affirmation_ids=affirmation_ids,
            affirmations=affirmation_responses
        )