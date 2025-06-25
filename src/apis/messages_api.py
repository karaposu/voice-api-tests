# here is messages_api.py

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
from typing import List, Optional
from typing_extensions import Annotated
from models.chat_message import ChatMessage
from models.new_message_request import NewMessageRequest
from models.new_message_response import NewMessageResponse
from security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)




from core.containers import Services
from fastapi import FastAPI, Request, HTTPException


def get_services(request: Request) -> Services:
    return request.app.state.services     # access the container attached in startup



@router.get(
    "/chat/{chat_id}/messages",
    responses={
        200: {"model": List[ChatMessage], "description": "Messages (oldest → newest)"},
    },
    tags=["messages"],
    summary="Paginated message history",
    response_model_by_alias=True,
)
async def chat_chat_id_messages_get(
    chat_id: int = Path(..., description="Target chat identifier"),          # ← int
    limit: int = Query(50, description="Max items to return"),               # ← int
    offset: int = Query(0, description="Items to skip"),            
    since: Annotated[Optional[datetime], Field(description="Return messages created after this timestamp")] = Query(None, description="Return messages created after this timestamp", alias="since"),
    token_bearerAuth: TokenModel = Security(get_token_bearerAuth),
    services: Services = Depends(get_services),
) -> List[ChatMessage]:
    
    # chat_id

    try:
        logger.debug(f"get messages endpoint called  ")
       
        # user_id = token_bearerAuth.sub
        user_id=int(token_bearerAuth.sub)  
        from impl.services.chat.bring_messages_service import BringMessagesService
        p = BringMessagesService(user_id, chat_id , dependencies=services)
        
        return p.response

       
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get(
    "/chat/{chat_id}/messages/{message_id}",
    responses={
        200: {"model": ChatMessage, "description": "Message details + logs"},
    },
    tags=["messages"],
    summary="Fetch a single message with full logs",
    response_model_by_alias=True,
)
async def chat_chat_id_messages_message_id_get(
    chat_id: Annotated[StrictInt, Field(description="Target chat identifier")] = Path(..., description="Target chat identifier"),
    message_id: StrictInt = Path(..., description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ChatMessage:
    if not BaseMessagesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseMessagesApi.subclasses[0]().chat_chat_id_messages_message_id_get(chat_id, message_id)


@router.post(
    "/chat/{chat_id}/messages",
    responses={
        201: {"model": NewMessageResponse, "description": "Message accepted"},
    },
    tags=["messages"],
    summary="Post a new message to a chat",
    response_model_by_alias=True,
)
async def chat_chat_id_messages_post(
    chat_id: Annotated[StrictInt, Field(description="Target chat identifier")] = Path(..., description="Target chat identifier"),
    new_message_request: Optional[NewMessageRequest] = Body(None, description=""),
    token_bearerAuth: TokenModel = Security( get_token_bearerAuth),
    services: Services = Depends(get_services),
) -> NewMessageResponse:
    try:
        logger.debug(f"new chat creation request")
       
        user_id = token_bearerAuth.sub
        from impl.services.messages.process_new_message_service import ProcessNewMessageService
        p = ProcessNewMessageService( user_id, chat_id, new_message_request,   dependencies=services)

        
        
        return p.response

       
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
