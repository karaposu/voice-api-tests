# coding: utf-8

from typing import List

from fastapi import Depends, Security  # noqa: F401
from fastapi.openapi.models import OAuthFlowImplicit, OAuthFlows  # noqa: F401
from fastapi.security import (  # noqa: F401
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
    OAuth2,
    OAuth2AuthorizationCodeBearer,
    OAuth2PasswordBearer,
    SecurityScopes,
)
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery
from fastapi import Depends, HTTPException, Security

from models.extra_models import TokenModel


bearer_auth = HTTPBearer()

from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()
import os
# logging.basicConfig(level=logging.DEBUG)
SECRET_KEY = os.getenv("SECRET_KEY")

import logging
logger = logging.getLogger(__name__)


def get_token_bearerAuth(credentials: HTTPAuthorizationCredentials = Depends(bearer_auth)) -> TokenModel:
    """
    Check and retrieve authentication information from custom bearer token.

    :param credentials: Credentials provided by Authorization header
    :type credentials: HTTPAuthorizationCredentials
    :return: Decoded token information or None if token is invalid
    :rtype: TokenModel | None
    """
    try:

        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Populate TokenModel with the relevant information
        return TokenModel(sub=user_id)
        # return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# def get_token_bearerAuth(credentials: HTTPAuthorizationCredentials = Depends(bearer_auth)) -> TokenModel:
#     """
#     Check and retrieve authentication information from custom bearer token.
#
#     :param credentials Credentials provided by Authorization header
#     :type credentials: HTTPAuthorizationCredentials
#     :return: Decoded token information or None if token is invalid
#     :rtype: TokenModel | None
#     """
#
#     ...


def get_token_ApiKeyAuth(
    token_api_key_header: str = Security(
        APIKeyHeader(name="X-API-KEY", auto_error=False)
    ),
) -> TokenModel:
    """
    Check and retrieve authentication information from api_key.

    :param token_api_key_header API key provided by Authorization[X-API-KEY] header
    
    
    :type token_api_key_header: str
    :return: Information attached to provided api_key or None if api_key is invalid or does not allow access to called API
    :rtype: TokenModel | None
    """

    ...

