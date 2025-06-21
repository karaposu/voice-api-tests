# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

# from apis.chat_api_base import BaseChatApi
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
from pydantic import Field
from typing import List
from typing_extensions import Annotated
from models.api_chat_history_get500_response import ApiChatHistoryGet500Response
from models.api_chat_history_post200_response import ApiChatHistoryPost200Response
from models.chat_history_message import ChatHistoryMessage
from security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/chat/history",
    responses={
        200: {"model": List[ChatHistoryMessage], "description": "Successfully retrieved history messages."},
        500: {"model": ApiChatHistoryGet500Response, "description": "Internal Server Error"},
    },
    tags=["chat"],
    summary="Retrieve the list of historical messages.",
    response_model_by_alias=True,
)
async def api_chat_history_get(
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> List[ChatHistoryMessage]:
    if not BaseChatApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseChatApi.subclasses[0]().api_chat_history_get()


@router.post(
    "/api/chat/history",
    responses={
        200: {"model": ApiChatHistoryPost200Response, "description": "Successfully added the message to history."},
        500: {"model": ApiChatHistoryGet500Response, "description": "Internal Server Error"},
    },
    tags=["chat"],
    summary="Add a new message to the history.",
    response_model_by_alias=True,
)
async def api_chat_history_post(
    chat_history_message: Annotated[ChatHistoryMessage, Field(description="Historical message to store.")] = Body(None, description="Historical message to store."),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> ApiChatHistoryPost200Response:
    if not BaseChatApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseChatApi.subclasses[0]().api_chat_history_post(chat_history_message)
