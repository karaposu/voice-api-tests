# db/repositories/admin_panel_user_repository.py


from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import asc, desc
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from fastapi import HTTPException

from db.models import User, UserSettings, InitialData, ProcessedData

logger = logging.getLogger(__name__)

class AdminPanelUserRepository:
    """
    Special-purpose repository for admin panel user list queries.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_user_list_with_pagination(
        self,
        page: int = 1,
        page_size: int = 10,
        filter_country: Optional[str] = None,
        filter_user_id: Optional[int] = None,
        filter_email: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return a list of users, with optional filters (country, user_id, email),
        plus aggregates like file count & record count, and user settings data.
        """
        # 1) Base query from User
        query = self.session.query(User)

        # 2) Outerjoin to UserSettings if we want to filter or retrieve default_country
        query = query.outerjoin(UserSettings, User.user_id == UserSettings.user_id)

        # 3) Subquery for total_files
        file_count_subq = (
            self.session.query(
                InitialData.user_id,
                func.count(InitialData.document_id).label("file_count")
            )
            .group_by(InitialData.user_id)
            .subquery()
        )

        # Join that subquery on user_id
        query = query.outerjoin(file_count_subq, User.user_id == file_count_subq.c.user_id)

        # Subquery for total_records
        record_count_subq = (
            self.session.query(
                ProcessedData.user_id,
                func.count(ProcessedData.record_id).label("record_count")
            )
            .group_by(ProcessedData.user_id)
            .subquery()
        )

        query = query.outerjoin(record_count_subq, User.user_id == record_count_subq.c.user_id)

        # 4) Apply filters:
        if filter_user_id is not None:
            query = query.filter(User.user_id == filter_user_id)

        if filter_email:
            # partial match, case-insensitive
            query = query.filter(User.email.ilike(f"%{filter_email}%"))

        if filter_country:
            # The actual country is in `UserSettings.default_country`:
            query = query.filter(UserSettings.default_country.ilike(f"%{filter_country}%"))

        # 5) Sort logic
        sort_map = {
            "signup_date": User.created_at,
            "user_id": User.user_id,
            "email": User.email,
            "country": UserSettings.default_country,
            "total_files": file_count_subq.c.file_count,
            "total_records": record_count_subq.c.record_count,
        }

        if sort_by in sort_map:
            sort_column = sort_map[sort_by]
            if sort_order and sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # default sort
            query = query.order_by(desc(User.created_at))

        # 6) Count total
        total_count = query.count()

        # 7) Pagination
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10

        offset_value = (page - 1) * page_size
        query = query.offset(offset_value).limit(page_size)

        # 8) Fetch results, adding columns from subqueries + user settings
        rows = query.add_columns(
            file_count_subq.c.file_count,
            record_count_subq.c.record_count,
            UserSettings.default_country
        ).all()

        # rows: list of tuples: (User, file_count, record_count, default_country)
        items = []
        for (user_obj, file_count, record_count, default_country) in rows:
            item = {
                "user_id": user_obj.user_id,
                "user_email": user_obj.email,
                "country": default_country,
                "signup_date": user_obj.created_at,
                "last_activity_date": user_obj.last_login_at,
                "number_of_files": file_count if file_count else 0,
                "list_of_file_ids": [],
                "number_of_records": record_count if record_count else 0,
            }
            items.append(item)

        return {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "items": items
        }
