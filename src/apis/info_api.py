# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

# from apis.info_api_base import BaseInfoApi
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
from models.api_chat_history_get500_response import ApiChatHistoryGet500Response
from models.api_info_models_get200_response import ApiInfoModelsGet200Response


router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/info/models",
    responses={
        200: {"model": ApiInfoModelsGet200Response, "description": "Successful response with model data."},
        500: {"model": ApiChatHistoryGet500Response, "description": "Internal Server Error"},
    },
    tags=["info"],
    summary="Retrieve model data.",
    response_model_by_alias=True,
)
async def api_info_models_get(
) -> ApiInfoModelsGet200Response:
    if not BaseInfoApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInfoApi.subclasses[0]().api_info_models_get()
