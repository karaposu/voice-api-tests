# impl/services/auth/login_with_refresh_service.py

import logging
from email_validator import validate_email, EmailNotValidError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, Response
import jwt
from traceback import format_exc

from models.auth_login_with_refresh_logic_post200_response import AuthLoginWithRefreshLogicPost200Response
from db.models.login_time_log import LoginTimeLog
from db.models.user_details import UserDetails



from dotenv import load_dotenv
import os
load_dotenv()

logger = logging.getLogger(__name__)

# Constants for token creation
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECRET_KEY')
# Expiration: 15 minutes for the access token; 7 days for the refresh token.
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: timedelta = None, unlimited: bool = False) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if unlimited:
        expire = datetime.utcnow() + timedelta(days=365 * 100)
    elif expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class LoginWithRefreshService:
    """
    Service class that handles login with refresh token logic.
    
    Steps:
      1. Validate and normalize the email.
      2. Verify the user's password.
      3. Generate both an access token (short-lived) and a refresh token (long-lived).
      4. Log the login time (if user settings exist).
      5. Set the refresh token as an HttpOnly cookie on the Response.
      6. Return a response model containing the access token and token type.
    
    **Usage:**
    The endpoint that uses this service must pass the FastAPI Response object as a parameter so that the refresh token can be set as a cookie.
    """

   
    
    def __init__(self, request, dependencies, response: Response):
        """
        :param request: an object with attributes `email` and `password`
        :param dependencies: dependency container (with session_factory, user_repository, etc.)
        :param response: FastAPI Response object to which the refresh token cookie will be attached.
        """
        self.request = request
        self.dependencies = dependencies
        self.response_obj = response
        self.response = None
        self.refresh_token = None

        logger.debug("Inside LoginWithRefreshService")
        self._preprocess_request_data()
        self._process_request()

    def _validate_email_address(self, email: str) -> str:
        logger.debug(f"Validating email: {email}")
        try:
            valid = validate_email(email)
            normalized_email = valid.email
            logger.debug(f"Email is valid: {normalized_email}")
            return normalized_email
        except EmailNotValidError as e:
            logger.error(f"Email validation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def _get_db_session(self):
        logger.debug("Accessing session_factory")
        session_factory = self.dependencies.session_factory()
        return session_factory()

    def _get_user_repository(self, session):
        user_repository_provider = self.dependencies.user_repository
        return user_repository_provider(session=session)
    
    def _fetch_user_by_email(self, user_repository, email: str):
        logger.debug(f"Retrieving user with email: {email}")
        db_user = user_repository.get_user_by_email(email)
        if not db_user:
            logger.error(f"User not found with email: {email}")
            raise HTTPException(status_code=400, detail="Invalid email or password")
        return db_user
    
    def _verify_user_password(self, db_user, password: str):
        logger.debug("Verifying password")
        if not pwd_context.verify(password, db_user.password_hash):
            logger.error("Invalid password")
            raise HTTPException(status_code=400, detail="Invalid email or password")

    def _create_tokens_for_user(self, user_id: int):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {"sub": str(user_id)}
        access_token = create_access_token(payload, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(payload, expires_delta=refresh_token_expires)
        return access_token, refresh_token

    def _insert_login_log(self, session, user_id: int):
        logger.debug("Attempting to insert login_time_log.")
        try:
            user_settings = session.query(UserDetails).filter_by(user_id=user_id).first()
            if user_settings:
                new_log = LoginTimeLog(login_datetime=datetime.utcnow())
                user_settings.login_time_logs.append(new_log)
                session.add(user_settings)
                session.commit()
                logger.debug(f"Inserted new LoginTimeLog for user_id={user_id}")
            else:
                logger.debug(f"UserDetails not found for user_id={user_id}. Skipping login_time_log insertion.")
        except Exception as e:
            logger.error(f"Error inserting login log: {e}")

    def _preprocess_request_data(self):
        try:
            # Validate and normalize email
            email = self._validate_email_address(self.request.email)
            # Get DB session and user repository
            session = self._get_db_session()
            user_repository = self._get_user_repository(session)
            # Fetch user by email and verify password
            db_user = self._fetch_user_by_email(user_repository, email)
            self._verify_user_password(db_user, self.request.password)
            # Insert login log if user settings exist
            self._insert_login_log(session, db_user.user_id)
            # session.close()
            # Generate tokens
            self.access_token, self.refresh_token = self._create_tokens_for_user(db_user.user_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}\n{format_exc()}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def _process_request(self):
        # Set the refresh token as an HttpOnly cookie on the Response object.
        self.response_obj.set_cookie(
            key="refresh_token",
            value=self.refresh_token,
            httponly=True,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,  # seconds
            path="/"
        )
        # Build the final response model containing only the access token and token type.
        self.response = AuthLoginWithRefreshLogicPost200Response(
            access_token=self.access_token,
            token_type="bearer"
        )
