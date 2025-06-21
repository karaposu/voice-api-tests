# repositories/family_repository.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import logging

from db.models import User, FamilyGroup, UserFamilyGroup

logger = logging.getLogger(__name__)

class FamilyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_family(self, user_id: int, family_name: str) -> str:
        try:
            # Verify that the user exists
            user = self.session.query(User).filter_by(user_id=user_id).first()
            if not user:
                logger.error(f"User with id {user_id} not found.")
                raise HTTPException(status_code=404, detail="User not found")

            # Create the family group
            family_group = FamilyGroup(
                family_name=family_name,
                created_by_user_id=user_id
            )
            self.session.add(family_group)
            self.session.flush()  # To get family_group.family_group_id

            # Add the user to the family group
            user_family_group = UserFamilyGroup(
                user_id=user_id,
                family_group_id=family_group.family_group_id
            )
            self.session.add(user_family_group)

            # Commit the transaction
            self.session.commit()
            logger.info(f"Family group '{family_name}' created by user_id {user_id}.")

            return family_group.family_group_oid

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating family group: {str(e)}")
            raise HTTPException(status_code=500, detail="Error creating family group")
