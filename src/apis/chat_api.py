# here is apis/chat_api.py

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
)

from models.extra_models import TokenModel  # noqa: F401
from datetime import datetime
from pydantic import Field, StrictInt
from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from models.chat_full import ChatFull
from models.chat_post201_response import ChatPost201Response
from models.usage_metrics import UsageMetrics
from security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)



from core.containers import Services
from fastapi import FastAPI, Request, HTTPException

def get_services(request: Request) -> Services:
    return request.app.state.services     # access the container attached in startup


def get_app():
    from app import app
    return app


@router.delete(
    "/chat/{chat_id}",
    responses={
        204: {"description": "Deleted"},
    },
    tags=["chat"],
    summary="Delete a chat session",
    response_model_by_alias=True,
)
async def chat_chat_id_delete(
    chat_id: Annotated[StrictInt, Field(description="Target chat identifier")] = Path(..., description="Target chat identifier"),
) -> None:
    pass

@router.get(
    "/chat/{chat_id}",
    responses={
        200: {"model": ChatFull, "description": "Aggregated chat data"},
    },
    tags=["chat"],
    response_model_by_alias=True,
)
async def chat_chat_id_get(
    chat_id: Annotated[StrictInt, Field(description="ID of the chat session")] = Path(..., description="ID of the chat session"),
    offset: Annotated[Optional[StrictInt], Field(description="Messages to skip (pagination)")] = Query(0, description="Messages to skip (pagination)", alias="offset"),
    limit: Annotated[Optional[StrictInt], Field(description="Max messages to return")] = Query(50, description="Max messages to return", alias="limit"),
    var_from: Annotated[Optional[datetime], Field(description="Usage report start time")] = Query(None, description="Usage report start time", alias="from"),
    to: Annotated[Optional[datetime], Field(description="Usage report end time")] = Query(None, description="Usage report end time", alias="to"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ChatFull:
    pass


@router.get(
    "/chat/{chat_id}/settings",
    responses={
        200: {"model": Dict[str, object], "description": "Settings object"},
    },
    tags=["chat"],
    summary="Current settings for a chat",
    response_model_by_alias=True,
)
async def chat_chat_id_settings_get(
    chat_id: Annotated[StrictInt, Field(description="Target chat identifier")] = Path(..., description="Target chat identifier"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Dict[str, object]:
    pass


@router.patch(
    "/chat/{chat_id}/settings",
    responses={
        200: {"model": Dict[str, object], "description": "Updated settings"},
    },
    tags=["chat"],
    summary="Update selected settings fields",
    response_model_by_alias=True,
)
async def chat_chat_id_settings_patch(
    chat_id: Annotated[StrictInt, Field(description="Target chat identifier")] = Path(..., description="Target chat identifier"),
    request_body: Optional[Dict[str, Any]] = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> Dict[str, object]:
   pass


@router.get(
    "/chat/{chat_id}/usage",
    responses={
        200: {"model": UsageMetrics, "description": "Usage metrics"},
    },
    tags=["chat"],
    summary="Usage &amp; cost metrics for a chat",
    response_model_by_alias=True,
)
async def chat_chat_id_usage_get(
    chat_id: Annotated[StrictInt, Field(description="Target chat identifier")] = Path(..., description="Target chat identifier"),
    var_from: Annotated[Optional[datetime], Field(description="Start of reporting window")] = Query(None, description="Start of reporting window", alias="from"),
    to: Annotated[Optional[datetime], Field(description="End of reporting window")] = Query(None, description="End of reporting window", alias="to"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> UsageMetrics:
   pass

@router.get(
    "/chat",
    responses={
        200: {"model": List[int], "description": "Array of chat identifiers"},
    },
    tags=["chat"],
    summary="List all chat IDs",
    response_model_by_alias=True,
)
async def chat_get(
) -> List[int]:
   pass


@router.post(
    "/chat",
    responses={
        201: {"model": ChatPost201Response, "description": "Chat created"},
    },
    tags=["chat"],
    summary="Create a new chat session",
    response_model_by_alias=True,
)
async def chat_post(
    token_bearerAuth: TokenModel = Security(get_token_bearerAuth),
    services: Services = Depends(get_services),
) -> ChatPost201Response:
    

    
    if token_bearerAuth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid bearer token",
        )
    
    try:
        logger.debug(f"new chat creation request")
       
        user_id = token_bearerAuth.sub
        from impl.services.chat.create_chat_service import CreateChatService
        p = CreateChatService( user_id,  dependencies=services)
        
        return p.response

        # return rh.handle_login_with_refresh(email, password, response)
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
