# impl/services/auth/login_service.py
import logging
from email_validator import validate_email, EmailNotValidError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException
import jwt
from traceback import format_exc

from models.auth_login_post200_response import AuthLoginPost200Response
from db.models.login_time_log import LoginTimeLog
from db.models.user_details import UserDetails

from dotenv import load_dotenv
import os
load_dotenv()

logger = logging.getLogger(__name__)

# Constants for JWT token creation
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = 3000  # Set as per your requirement

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None, unlimited: bool = False):
    """Utility function to create a JWT access token."""
    to_encode = data.copy()
    
    if unlimited:
        # Set a very far expiration date for "unlimited" tokens
        expire = datetime.utcnow() + timedelta(days=365 * 100)  # e.g. 100 years
    elif expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(days=7))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class LoginService:
    """
    Service class handling user login flow:
      1. Validate the email address.
      2. Verify the user's password.
      3. Generate a JWT token.
      4. Optionally log a 'login time' record if the user has settings.
    """

    def __init__(self, request, dependencies):
        self.request = request
        self.dependencies = dependencies
        self.response = None

        logger.debug("Inside LoginService")

        self._preprocess_request_data()
        self._process_request()
    
    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------
    def _validate_email_address(self, email: str) -> str:
        """Validate and normalize an incoming email address."""
        logger.debug(f"Validating email: {email}")
        try:
            # valid = validate_email(email)
            # normalized_email = valid.email
            normalized_email=email
            logger.debug(f"Email is valid: {normalized_email}")
            return normalized_email
        except EmailNotValidError as e:
            logger.error(f"Email validation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # def _get_db_session(self):
    #     """Obtain a SQLAlchemy session from the dependencies."""
    #     logger.debug("Accessing session_factory")
    #     session_factory = self.dependencies.session_factory()
    #     return session_factory
    
    
    def _get_db_session(self):
        logger.debug("Accessing session_factory")
     
        session_factory = self.dependencies.session_factory()
        # "session_factory" here is presumably a 'providers.Singleton(sessionmaker, bind=engine)'

        # To create a *session*, call it:
        return session_factory()  # This returns a Session object


    def _get_user_repository(self, session):
        """Obtain the user repository from dependencies, given a DB session."""
        user_repository_provider = self.dependencies.user_repository
        return user_repository_provider(session=session)

    def _fetch_user_by_email(self, user_repository, email: str):
        """Fetch a User by email or raise HTTP 400 if not found."""
        logger.debug(f"Retrieving user with email: {email}")
        db_user = user_repository.get_user_by_email(email)
        if not db_user:
            logger.error(f"User not found with email: {email}")
            raise HTTPException(status_code=400, detail="Invalid email or password")
        return db_user

    def _verify_user_password(self, db_user, password: str):
        """Verify that the given password matches the stored hash."""
        logger.debug("Verifying password")
        if not pwd_context.verify(password, db_user.password_hash):
            logger.error("Invalid password")
            raise HTTPException(status_code=400, detail="Invalid email or password")

    def _create_jwt_for_user(self, user_id: int) -> str:
        """Generate a JWT token for the given user_id."""
        logger.debug(f"Generating JWT token for user_id: {user_id}")
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # Build the JWT payload
        payload = {"sub": str(user_id)}
        # Actually create the token
        encoded_jwt = jwt.encode(
            self._add_exp_to_payload(payload, expires_delta),
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        logger.debug("Token generated successfully")
        return encoded_jwt

    def _add_exp_to_payload(self, data: dict, expires_delta: timedelta):
        """Helper to add `exp` field (expiration time) to a JWT payload."""
        to_encode = data.copy()
        expire_time = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire_time})
        return to_encode
    
    def _insert_login_log(self, session, user_id: int):
        logger.debug("Attempting to insert login_time_log.")
        try:
            # We already have a real Session, so no need for "with session() as db:"        
            user_settings = session.query(UserDetails).filter_by(user_id=user_id).first()
            if user_settings:
                new_log = LoginTimeLog(login_datetime=datetime.utcnow())
                user_settings.login_time_logs.append(new_log)
                session.add(user_settings)
                session.commit()
                logger.debug(f"Inserted new LoginTimeLog for user_id={user_id}")
            else:
                logger.debug(f"UserDetails not found for user_id={user_id}. "
                            "Skipping login_time_log insertion.")
        except Exception as e:
            logger.error(f"Error inserting login log: {e}")

    # def _insert_login_log(self, session, user_id: int):
    #     """
    #     Insert a new LoginTimeLog record for the given user_id,
    #     but only if a UserSettings row exists for them.
    #     """
    #     logger.debug("Attempting to insert login_time_log.")
    #     try:
    #         from sqlalchemy.orm import Session
    #         if not isinstance(session, Session):
    #             logger.warning("Invalid session provided to _insert_login_log. Aborting.")
    #             return

    #         with session() as db:
    #             user_settings = db.query(UserSettings).filter_by(user_id=user_id).first()
    #             if user_settings:
    #                 new_log = LoginTimeLog(login_datetime=datetime.utcnow())
    #                 user_settings.login_time_logs.append(new_log)
    #                 db.add(user_settings)
    #                 db.commit()
    #                 logger.debug(f"Inserted new LoginTimeLog for user_id={user_id}")
    #             else:
    #                 logger.debug(f"UserSettings not found for user_id={user_id}. "
    #                              "Skipping login_time_log insertion.")
    #     except Exception as e:
    #         logger.error(f"Error inserting login log: {e}")
            # Not re-raising here because a login log is optional.

    # -------------------------------------------------------------------------
    # Main Logic
    # -------------------------------------------------------------------------
    def _preprocess_request_data(self):
        """
        Main entry point for validating credentials and generating a token.
        Also writes a login-time log if the user has settings.
        """
        try:
            # 1) Validate email
            email = self._validate_email_address(self.request.email)

            # 2) Access the DB session and user repository
            session = self._get_db_session()


            logger.debug(type(session))

            


            user_repository = self._get_user_repository(session)

            # 3) Fetch the user by email
            db_user = self._fetch_user_by_email(user_repository, email)

            # 4) Verify the password
            self._verify_user_password(db_user, self.request.password)

            # 5) Create the JWT
            access_token = self._create_jwt_for_user(db_user.user_id)

            # 6) Insert the login log if user settings exist
            self._insert_login_log(session, db_user.user_id)

            # 7) Save the result for process_request
            self.preprocessed_data = access_token

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}\n{format_exc()}")
            
            raise HTTPException(status_code=500, detail="Internal server error")

    def _process_request(self):
        """Build the final response using the created token."""
        self.response = AuthLoginPost200Response(
            msg="Login successful",
            access_token=getattr(self, "preprocessed_data", None)
        )
