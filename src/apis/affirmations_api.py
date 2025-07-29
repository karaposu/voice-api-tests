# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil
import logging

logger = logging.getLogger(__name__)

import impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
    Request,
)

from models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictBool, StrictStr
from typing import Any, Optional
from typing_extensions import Annotated
from models.affirmation.affirmation_category import AffirmationCategory
from models.affirmation.ai_create_affirmations201_response import AiCreateAffirmations201Response
from models.affirmation.ai_create_affirmations_request import AiCreateAffirmationsRequest
from models.affirmation.create_affirmation201_response import CreateAffirmation201Response
from models.affirmation.create_affirmation400_response import CreateAffirmation400Response
from models.affirmation.create_affirmation_request import CreateAffirmationRequest
from models.affirmation.edit_affirmation200_response import EditAffirmation200Response
from models.affirmation.edit_affirmation404_response import EditAffirmation404Response
from models.affirmation.edit_affirmation_request import EditAffirmationRequest
from models.affirmation.get_affirmations200_response import GetAffirmations200Response
from models.affirmation.get_affirmations401_response import GetAffirmations401Response
from models.affirmation.schedule_affirmation200_response import ScheduleAffirmation200Response
from models.affirmation.schedule_affirmation_request import ScheduleAffirmationRequest
from security_api import get_token_bearerAuth

from core.containers import Services



router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


def get_services(request: Request) -> Services:
    return request.app.state.services




@router.post(
    "/affirmations/ai-create",
    responses={
        201: {"model": AiCreateAffirmations201Response, "description": "AI affirmations created successfully"},
        400: {"model": CreateAffirmation400Response, "description": "Bad request"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
    },
    tags=["Affirmations"],
    summary="Generate AI-powered affirmations",
    response_model_by_alias=True,
)
async def ai_create_affirmations(
    ai_create_affirmations_request: AiCreateAffirmationsRequest = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> AiCreateAffirmations201Response:
    """Create personalized affirmations using AI based on user context"""
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug("ai_create_affirmations is called")
        logger.debug(f"incoming data: {ai_create_affirmations_request}")
        
        user_id = int(token_bearerAuth.sub)
        
        # Import and use the service
        from impl.services.affirmations.ai_create_affirmations_service import AiCreateAffirmationsService
        service = AiCreateAffirmationsService(
            request=ai_create_affirmations_request,
            user_id=user_id,
            dependencies=services
        )
        
        return service.response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post(
    "/affirmations",
    responses={
        201: {"model": CreateAffirmation201Response, "description": "Affirmation created successfully"},
        400: {"model": CreateAffirmation400Response, "description": "Bad request"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
    },
    tags=["Affirmations"],
    summary="Create a new affirmation",
    response_model_by_alias=True,
)
async def create_affirmation(
    create_affirmation_request: CreateAffirmationRequest = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> CreateAffirmation201Response:
    """Creates a user-generated affirmation"""



    if token_bearerAuth is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid bearer token",
            )

    try:
        logger.debug("create_affirmation is called")
        logger.debug(f"incoming data: {create_affirmation_request}")
        
        # Get user_id from token
        user_id = int(token_bearerAuth.sub)
        #user_id = get_user_id_from_token(token_bearerAuth)
        
        # Import and use the service
        from impl.services.affirmations.create_affirmation_service import CreateAffirmationService
        service = CreateAffirmationService(
            request=create_affirmation_request,
            user_id=user_id,
            dependencies=services
        )
        
        return service.response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.delete(
    "/affirmations/{affirmation_id}",
    responses={
        204: {"description": "Affirmation deleted successfully"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
        404: {"model": EditAffirmation404Response, "description": "Resource not found"},
    },
    tags=["Affirmations"],
    summary="Delete an affirmation",
    response_model_by_alias=True,
)
async def delete_affirmation(
    affirmation_id: StrictStr = Path(..., description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> None:
    """Remove an affirmation from the user&#39;s collection"""
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug("delete_affirmation is called")
        logger.debug(f"affirmation_id: {affirmation_id}")
        
        # Get user_id from token
        user_id = int(token_bearerAuth.sub)
        
        # Create request object
        class DeleteAffirmationRequest:
            def __init__(self):
                self.affirmation_id = int(affirmation_id)
                self.user_id = int(user_id)
        
        request = DeleteAffirmationRequest()
        
        # Import and use the service
        from impl.services.affirmations.delete_affirmation_service import DeleteAffirmationService
        DeleteAffirmationService(
            request=request,
            dependencies=services
        )
        
        # Return 204 No Content for successful deletion
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.put(
    "/affirmations/{affirmation_id}",
    responses={
        200: {"model": EditAffirmation200Response, "description": "Affirmation updated successfully"},
        400: {"model": CreateAffirmation400Response, "description": "Bad request"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
        404: {"model": EditAffirmation404Response, "description": "Resource not found"},
    },
    tags=["Affirmations"],
    summary="Edit an affirmation",
    response_model_by_alias=True,
)
async def edit_affirmation(
    affirmation_id: StrictStr = Path(..., description=""),
    edit_affirmation_request: EditAffirmationRequest = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> EditAffirmation200Response:
    """Update an existing affirmation&#39;s text and voice settings"""
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug("edit_affirmation is called")
        logger.debug(f"affirmation_id: {affirmation_id}")
        logger.debug(f"incoming data: {edit_affirmation_request}")
        
        # Get user_id from token
        user_id = int(token_bearerAuth.sub)
        
        # Import and use the service
        from impl.services.affirmations.edit_affirmation_service import EditAffirmationService
        service = EditAffirmationService(
            request=edit_affirmation_request,
            affirmation_id=int(affirmation_id),
            user_id=user_id,
            dependencies=services
        )
        
        return service.response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get(
    "/affirmations",
    responses={
        200: {"model": GetAffirmations200Response, "description": "List of affirmations"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
    },
    tags=["Affirmations"],
    summary="Get user&#39;s affirmations",
    response_model_by_alias=True,
)
async def get_affirmations(
    category: Annotated[Optional[AffirmationCategory], Field(description="Filter by affirmation category")] = Query(None, description="Filter by affirmation category", alias="category"),
    scheduled_only: Annotated[Optional[StrictBool], Field(description="Return only scheduled affirmations")] = Query(False, description="Return only scheduled affirmations", alias="scheduled_only"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> GetAffirmations200Response:
    """Retrieve all affirmations for the authenticated user"""
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug("get_affirmations is called")
        logger.debug(f"filters - category: {category}, scheduled_only: {scheduled_only}")
        
        # Get user_id from token
        user_id = int(token_bearerAuth.sub)
        
        # Create request object for filters
        class GetAffirmationsRequest:
            def __init__(self):
                self.user_id = int(user_id)
                self.category = category
                self.scheduled_only = scheduled_only
        
        request = GetAffirmationsRequest()
        
        # Import and use the service
        from impl.services.affirmations.get_affirmations_service import GetAffirmationsService
        service = GetAffirmationsService(
            request=request,
            dependencies=services
        )
        
        return service.response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post(
    "/affirmations/{affirmation_id}/schedule",
    responses={
        200: {"model": ScheduleAffirmation200Response, "description": "Affirmation scheduled successfully"},
        400: {"model": CreateAffirmation400Response, "description": "Bad request"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
        404: {"model": EditAffirmation404Response, "description": "Resource not found"},
    },
    tags=["Affirmations"],
    summary="Schedule an affirmation",
    response_model_by_alias=True,
)
async def schedule_affirmation(
    affirmation_id: StrictStr = Path(..., description=""),
    schedule_affirmation_request: ScheduleAffirmationRequest = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> ScheduleAffirmation200Response:
    """Set up notification schedule for an affirmation"""
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug("schedule_affirmation is called")
        logger.debug(f"affirmation_id: {affirmation_id}")
        logger.debug(f"incoming data: {schedule_affirmation_request}")
        
        # Get user_id from token
        user_id = int(token_bearerAuth.sub)
        
        # Add affirmation_id and user_id to request
        schedule_affirmation_request.affirmation_id = int(affirmation_id)
        schedule_affirmation_request.user_id = user_id
        
        # Import and use the service
        from impl.services.affirmations.schedule_affirmation_service import ScheduleAffirmationService
        service = ScheduleAffirmationService(
            request=schedule_affirmation_request,
            dependencies=services
        )
        
        return service.response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.delete(
    "/affirmations/{affirmation_id}/schedule",
    responses={
        204: {"description": "Schedule removed successfully"},
        401: {"model": GetAffirmations401Response, "description": "Unauthorized"},
        404: {"model": EditAffirmation404Response, "description": "Resource not found"},
    },
    tags=["Affirmations"],
    summary="Remove affirmation schedule",
    response_model_by_alias=True,
)
async def unschedule_affirmation(
    affirmation_id: StrictStr = Path(..., description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
    services: Services = Depends(get_services),
) -> None:
    """Cancel scheduled notifications for an affirmation"""
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug("unschedule_affirmation is called")
        logger.debug(f"affirmation_id: {affirmation_id}")
        
        # Get user_id from token
        user_id = int(token_bearerAuth.sub)
        
        # Create request object
        class UnscheduleAffirmationRequest:
            def __init__(self):
                self.affirmation_id = int(affirmation_id)
                self.user_id = int(user_id)
        
        request = UnscheduleAffirmationRequest()
        
        # Import and use the service
        from impl.services.affirmations.unschedule_affirmation_service import UnscheduleAffirmationService
        UnscheduleAffirmationService(
            request=request,
            dependencies=services
        )
        
        # Return 204 No Content for successful unscheduling
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")