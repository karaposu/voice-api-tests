# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from apis.coach_api_base import BaseCoachApi
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
from models.coach_message_request import CoachMessageRequest
from models.coach_message_response import CoachMessageResponse
from security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/coach/message",
    responses={
        200: {"model": CoachMessageResponse, "description": "Coach response"},
    },
    tags=["coach"],
    summary="Send a user message to the coach and receive AI response",
    response_model_by_alias=True,
)
async def coach_message_post(
    coach_message_request: CoachMessageRequest = Body(None, description=""),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> CoachMessageResponse:
    if not BaseCoachApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCoachApi.subclasses[0]().coach_message_post(coach_message_request)
