# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from apis.admin_panel_api_base import BaseAdminPanelApi
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
from pydantic import Field, StrictInt, StrictStr, field_validator
from typing import Optional
from typing_extensions import Annotated
from models.get_users_list200_response import GetUsersList200Response
from models.login400_response import Login400Response
from models.refresh_token500_response import RefreshToken500Response
from security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/admin/panel/users/list",
    responses={
        200: {"model": GetUsersList200Response, "description": "Paginated list of users retrieved successfully."},
        400: {"model": Login400Response, "description": "Bad request."},
        500: {"model": RefreshToken500Response, "description": "Internal server error."},
    },
    tags=["admin_panel"],
    summary="Retrieve a paginated list of users",
    response_model_by_alias=True,
)
async def get_users_list(
    page: Annotated[Optional[Annotated[int, Field(strict=True, ge=1)]], Field(description="The page number to retrieve (for pagination).")] = Query(1, description="The page number to retrieve (for pagination).", alias="page", ge=1),
    page_size: Annotated[Optional[Annotated[int, Field(strict=True, ge=1)]], Field(description="The number of users to return per page (for pagination).")] = Query(10, description="The number of users to return per page (for pagination).", alias="page_size", ge=1),
    country: Annotated[Optional[StrictStr], Field(description="Filter users by country.")] = Query(None, description="Filter users by country.", alias="country"),
    user_id: Annotated[Optional[StrictInt], Field(description="Filter by a specific user ID.")] = Query(None, description="Filter by a specific user ID.", alias="user_id"),
    email: Annotated[Optional[StrictStr], Field(description="Filter by email address (e.g., partial or exact match).")] = Query(None, description="Filter by email address (e.g., partial or exact match).", alias="email"),
    sort_by: Annotated[Optional[StrictStr], Field(description="Order results by user activity, signup date, country, total_files, or total_records.")] = Query(None, description="Order results by user activity, signup date, country, total_files, or total_records.", alias="sort_by"),
    sort_order: Annotated[Optional[StrictStr], Field(description="The sorting order (ascending or descending). Typically defaults to `desc` for dates.")] = Query(None, description="The sorting order (ascending or descending). Typically defaults to &#x60;desc&#x60; for dates.", alias="sort_order"),
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> GetUsersList200Response:
    """Returns a list of users with optional filters (country, user_id, email) and ordering (activity, signup_date, country, total_files, total_records)."""
    if not BaseAdminPanelApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAdminPanelApi.subclasses[0]().get_users_list(page, page_size, country, user_id, email, sort_by, sort_order)
