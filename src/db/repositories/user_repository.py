# db/repositories/user_repository.py
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from fastapi import HTTPException
from passlib.context import CryptContext
import logging

from db.models import User
from typing import Optional

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, session: Session):
        self.session = session
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def add_new_user(self, email: str, hashed_password: str) -> int:
        
        try:
            db_user = User(
                email=email,
                password_hash=hashed_password,
                created_at=datetime.utcnow(),
                name=""
            )
            # Automatically link the details object
            from db.models.user_details import UserDetails
            db_user.user_details = UserDetails()

            self.session.add(db_user)
            self.session.commit()  # flush+commit in the right order

            return db_user.user_id

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding new user: {str(e)}")
            raise HTTPException(status_code=500, detail="Error adding new user")
            
            
    
        
        # try:
        #     db_user = User(
        #         email=email,
        #         password_hash=hashed_password,
        #         created_at=datetime.utcnow(),
        #         name=""  # Set name if needed
        #     )
        #     from db.models.user_details import UserDetails
        #     self.session.add(db_user)
        #     details = UserDetails(user_id=db_user.user_id)
        #     self.session.add(details)
            
        #     self.session.flush()


        #     self.session.commit()
        #     return db_user.user_id
        # except SQLAlchemyError as e:
        #     self.session.rollback()
        #     logger.error(f"Error adding new user: {str(e)}")
        #     raise HTTPException(status_code=500, detail="Error adding new user")
        
    def get_user_profile(self, user_id: int) -> Optional[User]:
        """
        Fetch a single User row by its primary-key ID.

        Returns
        -------
        User | None
            The user row if found, else ``None``.  (Service layer decides
            whether to raise 404.)
        """
        try:
            result=self.session.query(User) .filter(User.user_id == user_id) .first()
            return result 

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error while fetching user_id {user_id}: {e}")
            return None

    def get_user_by_email(self, email: str) -> User:
        try:
            db_user = self.session.query(User).filter(User.email == email).first()
            return db_user
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error: {e}")
            return None

    def check_user_by_email(self, email: str) -> bool:
        db_user = self.get_user_by_email(email)
        return db_user is not None
    

    def get_user_list_with_pagination(self, page, page_size, country,  user_id, email,sort_by, sort_order ):
        pass

    def change_password(self, email: str, new_password: str):
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        new_hashed_password = self.pwd_context.hash(new_password)
        user.password_hash = new_hashed_password
        self.session.add(user)
        self.session.commit()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def make_user_verified_from_email(self, email: str):
        db_user = self.get_user_by_email(email)
        if db_user:
            db_user.is_verified = True
            self.session.add(db_user)
            self.session.commit()

    def add_default_currency(self, user_id: int, default_currency: str):
        try:
            user_settings = self.session.query(UserSettings).filter_by(user_id=user_id).first()

            if user_settings:
                # Update existing settings
                user_settings.default_currency = default_currency
            else:
                # Create new settings entry
                user_settings = UserSettings(
                    user_id=user_id,
                    default_currency=default_currency
                )
                self.session.add(user_settings)

            self.session.commit()
            logger.info(f"Set default currency for user_id {user_id} to {default_currency}")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error setting default currency for user_id {user_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error setting default currency")



    # def update_user_settings(self, user_id: int, **kwargs):
    #     try:
    #         user_settings = self.session.query(UserSettings).filter_by(user_id=user_id).first()

    #         # Get all column names from the UserSettings model, excluding primary keys and foreign keys
    #         mapper = inspect(UserSettings)
    #         primary_keys = {column.key for column in mapper.primary_key}
    #         foreign_keys = {column.key for column in mapper.columns if column.foreign_keys}
    #         excluded_fields = primary_keys.union(foreign_keys)
    #         allowed_fields = set(mapper.columns.keys()).difference(excluded_fields)

    #         # Filter kwargs to only include allowed fields
    #         update_fields = {key: value for key, value in kwargs.items() if key in allowed_fields}

    #         if not update_fields:
    #             raise ValueError("No valid settings provided to update.")

    #         if user_settings:
    #             # Update existing settings
    #             for key, value in update_fields.items():
    #                 setattr(user_settings, key, value)
    #         else:
    #             # Create new settings entry
    #             user_settings = UserSettings(
    #                 user_id=user_id,
    #                 **update_fields
    #             )
    #             self.session.add(user_settings)

    #         self.session.commit()
    #         logger.info(f"Updated settings for user_id {user_id} with {update_fields}")
    #     except SQLAlchemyError as e:
    #         self.session.rollback()
    #         logger.error(f"Error updating settings for user_id {user_id}: {str(e)}")
    #         raise HTTPException(status_code=500, detail="Error updating user settings")
    #     except ValueError as ve:
    #         logger.error(f"Invalid update attempt for user_id {user_id}: {str(ve)}")
    #         raise HTTPException(status_code=400, detail=str(ve))
    
    # def get_user_settings(self, user_id: int) -> Optional[UserSettings]:
    #     try:
    #         user_settings = self.session.query(UserSettings).filter_by(user_id=user_id).first()
    #         return user_settings
    #     except SQLAlchemyError as e:
    #         self.session.rollback()
    #         logger.error(f"Error getting settings for user_id {user_id}: {str(e)}")
    #         raise HTTPException(status_code=500, detail="Error getting user settings")