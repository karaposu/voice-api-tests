# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

# from apis.auth_api_base import BaseAuthApi
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
from pydantic import StrictStr
from models.api_chat_history_get500_response import ApiChatHistoryGet500Response
from models.auth_login_with_refresh_logic_post200_response import AuthLoginWithRefreshLogicPost200Response
from models.auth_login_with_refresh_logic_post401_response import AuthLoginWithRefreshLogicPost401Response
from models.auth_logout_post200_response import AuthLogoutPost200Response
from models.auth_private_get200_response import AuthPrivateGet200Response
from models.auth_register_post200_response import AuthRegisterPost200Response
from models.auth_register_post_request import AuthRegisterPostRequest
from models.auth_reset_password_post_request import AuthResetPasswordPostRequest
from models.login200_response import Login200Response
from models.login400_response import Login400Response
from models.login_request import LoginRequest
from models.refresh_token200_response import RefreshToken200Response
from models.refresh_token400_response import RefreshToken400Response
from models.refresh_token500_response import RefreshToken500Response
from models.refresh_token_request import RefreshTokenRequest
from security_api import get_token_bearerAuth

router = APIRouter()

ns_pkg =impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/auth/login",
    responses={
        200: {"model": AuthLoginWithRefreshLogicPost200Response, "description": "Successful login"},
        401: {"model": AuthLoginWithRefreshLogicPost401Response, "description": "Authentication information is missing or invalid."},
    },
    tags=["auth"],
    summary="Log in a user",
    response_model_by_alias=True,
)
async def auth_login_post(
    email: StrictStr = Form(None, description=""),
    password: StrictStr = Form(None, description=""),
) -> AuthLoginWithRefreshLogicPost200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_login_post(email, password)


@router.post(
    "/auth/login_with_refresh_logic",
    responses={
        200: {"model": AuthLoginWithRefreshLogicPost200Response, "description": "Successful login; access token returned in the body and refresh token is set as an HttpOnly cookie."},
        401: {"model": AuthLoginWithRefreshLogicPost401Response, "description": "Authentication information is missing or invalid."},
    },
    tags=["auth"],
    summary="Log in a user",
    response_model_by_alias=True,
)
async def auth_login_with_refresh_logic_post(
    email: StrictStr = Form(None, description=""),
    password: StrictStr = Form(None, description=""),
) -> AuthLoginWithRefreshLogicPost200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_login_with_refresh_logic_post(email, password)


@router.post(
    "/auth/logout",
    responses={
        200: {"model": AuthLogoutPost200Response, "description": "Successful logout"},
        401: {"model": AuthLoginWithRefreshLogicPost401Response, "description": "Authentication information is missing or invalid."},
    },
    tags=["auth"],
    summary="Log out a user",
    response_model_by_alias=True,
)
async def auth_logout_post(
) -> AuthLogoutPost200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_logout_post()


@router.get(
    "/auth/private",
    responses={
        200: {"model": AuthPrivateGet200Response, "description": "Successful access"},
        401: {"model": AuthLoginWithRefreshLogicPost401Response, "description": "Authentication information is missing or invalid."},
    },
    tags=["auth"],
    summary="Access protected route",
    response_model_by_alias=True,
)
async def auth_private_get(
    token_bearerAuth: TokenModel = Security(
        get_token_bearerAuth
    ),
) -> AuthPrivateGet200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_private_get()


@router.post(
    "/auth/register",
    responses={
        200: {"model": AuthRegisterPost200Response, "description": "User registered successfully"},
        400: {"model": ApiChatHistoryGet500Response, "description": "Email already registered"},
    },
    tags=["auth"],
    summary="Register a new user",
    response_model_by_alias=True,
)
async def auth_register_post(
    auth_register_post_request: AuthRegisterPostRequest = Body(None, description=""),
) -> AuthRegisterPost200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_register_post(auth_register_post_request)


@router.post(
    "/auth/reset-password",
    responses={
        200: {"model": AuthLogoutPost200Response, "description": "Password reset successfully"},
        400: {"model": ApiChatHistoryGet500Response, "description": "User not found"},
    },
    tags=["auth"],
    summary="Reset user&#39;s password",
    response_model_by_alias=True,
)
async def auth_reset_password_post(
    auth_reset_password_post_request: AuthResetPasswordPostRequest = Body(None, description=""),
) -> AuthLogoutPost200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_reset_password_post(auth_reset_password_post_request)


@router.post(
    "/api/login",
    responses={
        200: {"model": Login200Response, "description": "User authenticated successfully"},
        400: {"model": Login400Response, "description": "Bad request."},
        401: {"model": AuthLoginWithRefreshLogicPost401Response, "description": "Authentication information is missing or invalid."},
        500: {"model": RefreshToken500Response, "description": "Internal server error."},
    },
    tags=["auth"],
    summary="Authenticate user",
    response_model_by_alias=True,
)
async def login(
    login_request: LoginRequest = Body(None, description=""),
) -> Login200Response:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().login(login_request)


@router.post(
    "/auth/refresh-token",
    responses={
        200: {"model": RefreshToken200Response, "description": "Token refreshed successfully"},
        400: {"model": RefreshToken400Response, "description": "Bad request. The email is not found or is invalid."},
        401: {"model": AuthLoginWithRefreshLogicPost401Response, "description": "Authentication information is missing or invalid."},
        500: {"model": RefreshToken500Response, "description": "Internal server error."},
    },
    tags=["auth"],
    summary="Ref/authresh JWT token using email",
    response_model_by_alias=True,
)
async def refresh_token(
    refresh_token_request: RefreshTokenRequest = Body(None, description=""),
) -> RefreshToken200Response:
    """Regenerates a JWT token based on the provided email address."""
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().refresh_token(refresh_token_request)
