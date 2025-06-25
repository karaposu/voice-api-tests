# coding: utf-8

# here is apis/auth_api.py

import logging
logger = logging.getLogger(__name__)

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil
from pydantic import Field, StrictStr, StrictInt
from fastapi import Response

# from my_package.apis.auth_api_base import BaseAuthApi
import impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    Path,
    Query,
    Response,
    Security,
    status,
)

from models.extra_models import TokenModel  # noqa: F401
from models.auth_login_post200_response import AuthLoginPost200Response
from models.auth_logout_post200_response import AuthLogoutPost200Response
from models.auth_private_get200_response import AuthPrivateGet200Response
from models.auth_register_post200_response import AuthRegisterPost200Response
from models.auth_register_post400_response import AuthRegisterPost400Response
from models.auth_register_post_request import AuthRegisterPostRequest
from models.auth_reset_password_post_request import AuthResetPasswordPostRequest
from models.error_response import ErrorResponse
from models.login200_response import Login200Response
from models.login_request import LoginRequest
from models.refresh_token200_response import RefreshToken200Response
from models.refresh_token400_response import RefreshToken400Response
from models.refresh_token_request import RefreshTokenRequest
from models.verify_email200_response import VerifyEmail200Response

from models.auth_login_with_refresh_logic_post200_response import AuthLoginWithRefreshLogicPost200Response
from security_api import get_token_bearerAuth


from impl.services.auth.register_service import RegisterService
from impl.services.auth.login_with_refresh_service import LoginWithRefreshService
from impl.services.auth.login_service import LoginService
from dotenv import load_dotenv

router = APIRouter()

ns_pkg = impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)



from fastapi import FastAPI, Request, HTTPException
from fastapi import BackgroundTasks


from fastapi import Depends

from core.containers import Services  # or wherever your container class lives



def get_services(request: Request) -> Services:
    return request.app.state.services     # access the container attached in startup


def get_app():
 from app import app
 return app



def get_request_handler():
    from app import app
    from impl.request_handler import RequestHandler
    return RequestHandler(app)



@router.post(
    "/auth/register",
    responses={
        200: {"model": AuthRegisterPost200Response, "description": "User registered successfully"},
        400: {"model": AuthRegisterPost400Response, "description": "Email already registered"},
    },
    tags=["auth"],
    summary="Register a new user",
    response_model_by_alias=True,
)
async def auth_register_post(
    auth_register_post_request: AuthRegisterPostRequest = Body(None, description=""),
) -> AuthRegisterPost200Response:
    try:
        logger.debug("auth_register_post is called")
        logger.debug(f"incoming data: {auth_register_post_request} ")
        # rh = get_request_handler()

        dependency=get_app().state.services
        
        # dependency = rh.app.state.services
        p = RegisterService(auth_register_post_request, dependencies=dependency)
        return p.response
        

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)  # Log the exception details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    




@router.post(
    "/auth/login_with_refresh_logic",
    responses={
        200: {"model": AuthLoginWithRefreshLogicPost200Response, "description": "Successful login; access token returned in the body and refresh token is set as an HttpOnly cookie."},
        401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
    },
    tags=["auth"],
    summary="Log in a user",
    response_model_by_alias=True,
)
async def auth_login_with_refresh_logic_post(
    response: Response,
    email: StrictStr = Form(..., description="User email"),
    password: StrictStr = Form(..., description="User password"),
    
) -> AuthLoginWithRefreshLogicPost200Response:
    try:
        logger.debug(f"[raw incoming package] email {email}, password {password}")
        # rh = get_request_handler()

        dependency=get_app().state.services

        class MyRequest:
            def __init__(self):
                self.email = email
                self.password = password
        
        mr = MyRequest()
        p = LoginWithRefreshService(mr, dependencies=dependency, response=response)
        
        return p.response

        # return rh.handle_login_with_refresh(email, password, response)
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


   

@router.post(
    "/auth/login",
    responses={
        200: {"model": AuthLoginPost200Response, "description": "Successful login"},
        401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
    },
    tags=["auth"],
    summary="Log in a user",
    response_model_by_alias=True,
)
async def auth_login_post(
    email: str = Form(None, description=""),
    password: str = Form(None, description=""),
    services: Services = Depends(get_services),

) -> AuthLoginPost200Response:
    try:

        class MyRequest:
            def __init__(self):
                self.email = email
                self.password = password
        
        mr = MyRequest()
        logger.debug(f" [raw incoming package] email {email}, password {password}")
        p= LoginService(mr ,dependencies=services) 
        return p.response

       

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)  # Log the exception details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post(
    "/auth/logout",
    responses={
        200: {"model": AuthLogoutPost200Response, "description": "Successful logout"},
        401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
    },
    tags=["auth"],
    summary="Log out a user",
    response_model_by_alias=True,
)
async def auth_logout_post(
) -> AuthLogoutPost200Response:
    ...


@router.get(
    "/auth/private",
    responses={
        200: {"model": AuthPrivateGet200Response, "description": "Successful access"},
        401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
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
    ...





@router.post(
    "/auth/reset-password",
    responses={
        200: {"model": AuthLogoutPost200Response, "description": "Password reset successfully"},
        400: {"model": AuthRegisterPost400Response, "description": "User not found"},
    },
    tags=["auth"],
    summary="Reset user&#39;s password",
    response_model_by_alias=True,
)
async def auth_reset_password_post(
    auth_reset_password_post_request: AuthResetPasswordPostRequest = Body(None, description=""),
) -> AuthLogoutPost200Response:
    try:
        
        dependency=get_app().state.services

        from impl.services.auth.user_services import ResetPasswordService
        p=ResetPasswordService(auth_reset_password_post_request)
        return p.response
    
        #return rh.handle_reset_password(auth_reset_password_post_request)

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)  # Log the exception details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

#
# @router.post(
#     "/api/login",
#     responses={
#         200: {"model": Login200Response, "description": "User authenticated successfully"},
#         400: {"model": ErrorResponse, "description": "Bad request. The request body is not correctly structured or contains invalid parameters."},
#         401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
#         500: {"model": ErrorResponse, "description": "Internal Server Error. An error occurred on the server while processing the request."},
#     },
#     tags=["auth"],
#     summary="Authenticate user",
#     response_model_by_alias=True,
# )
# async def login(
#     login_request: LoginRequest = Body(None, description=""),
# ) -> Login200Response:
#     ...


@router.post(
    "/auth/refresh-token",
    responses={
        200: {"model": RefreshToken200Response, "description": "Token refreshed successfully"},
        400: {"model": RefreshToken400Response, "description": "Bad request. The email is not found or is invalid."},
        401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
        500: {"model": ErrorResponse, "description": "Internal Server Error. An error occurred on the server while processing the request."},
    },
    tags=["auth"],
    summary="Refresh JWT token using email",
    response_model_by_alias=True,
)
async def refresh_token(
    refresh_token_request: RefreshTokenRequest = Body(None, description=""),
) -> RefreshToken200Response:
    """Regenerates a JWT token based on the provided email address."""
   
    load_dotenv()
    import os
    logging.basicConfig(level=logging.DEBUG)
    SECRET = os.getenv("SECRET_KEY")

    from fastapi_login import LoginManager
    manager = LoginManager(SECRET, token_url='/auth/login')
    access_token = manager.create_access_token(data={'sub': refresh_token_request.email})
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get(
    "/auth/verify-email",
    responses={
        200: {"model": VerifyEmail200Response, "description": "Email verified successfully"},
        400: {"model": ErrorResponse, "description": "Bad request. The request body is not correctly structured or contains invalid parameters."},
        401: {"model": ErrorResponse, "description": "Unauthorized. Authentication credentials are missing or invalid."},
        500: {"model": ErrorResponse, "description": "Internal Server Error. An error occurred on the server while processing the request."},
    },
    tags=["auth"],
    summary="Verify user&#39;s email",
    response_model_by_alias=True,
)
async def verify_email(
    token: str = Query(None, description="The token sent to the user&#39;s email address for verification.", alias="token"),
) -> VerifyEmail200Response:
    """Verifies a user&#39;s email address using a token sent via email."""
    try:

        # rh = get_request_handler()

        class MyRequest :
            def __init__(self):
                self.token=token
            
        mr = MyRequest()
        
        from impl.services.auth.user_services import VerifyService
        
        p= VerifyService(mr)
        return p.response
    
       # return rh.handle_verify_email(token)

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)  # Log the exception details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

