# db/repositories/admin_panel_report_repository.py

import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import asc, desc
from datetime import datetime, date
from typing import Optional, Dict, Any, List

from fastapi import HTTPException

from db.models import User, UserSettings, InitialData, ProcessedData

logger = logging.getLogger(__name__)

class AdminPanelReportRepository:
    """
    Special-purpose repository for admin panel report queries (line charts, etc.).
    """

    def __init__(self, session: Session):
        self.session = session

    def get_file_report_linechart(
        self,
        period_type: str,
        start_date: Optional[date],
        end_date: Optional[date],
        country: Optional[str],   # e.g. the user's 'default_country'
        bank_id: Optional[int],
        status: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Returns aggregated file upload counts over time (line chart),
        grouped by the given period_type (day, week, month, year),
        optionally filtered by date range, country, bank_id, and status.
        """

        # 1) Map period_type -> SQLite strftime pattern
        #    For example:
        period_map = {
            "day": "%Y-%m-%d",
            "week": "%Y-%W",  # or some variant for weekly grouping
            "month": "%Y-%m",
            "year": "%Y",
        }

        # If unrecognized period_type, raise error:
        if period_type not in period_map:
            logger.error(f"Invalid period_type: {period_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported period_type: {period_type}")

        # Choose the strftime pattern:
        strftime_pattern = period_map[period_type]

        # 2) Base query: aggregate count of InitialData rows, grouped by time
        #    Also join to UserSettings to filter by default_country if 'country' is provided
        #    isouter=True because not all users might have settings, but you'll skip them anyway if you filter by country
        query = (
            self.session.query(
                func.strftime(strftime_pattern, InitialData.upload_timestamp).label("period_label"),
                func.count(InitialData.document_id).label("files_count")
            )
            .outerjoin(UserSettings, UserSettings.user_id == InitialData.user_id)
        )

        # 3) Build filters:
        #    a) Date range filter
        if start_date:
            # Convert date to datetime if needed
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(InitialData.upload_timestamp >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time())
            query = query.filter(InitialData.upload_timestamp <= end_dt)

        #    b) Filter by user_settings.default_country if country is provided
        if country:
            # Use ilike for case-insensitive partial match, or equals if you want exact
            query = query.filter(UserSettings.default_country.ilike(f"%{country}%"))

        #    c) Filter by bank_id
        if bank_id is not None:
            query = query.filter(InitialData.bank_id == bank_id)

        #    d) Filter by status
        if status:
            query = query.filter(InitialData.process_status == status)

        # 4) Group by the date expression
        query = query.group_by("period_label")

        # 5) Order by date ascending for a typical line chart
        query = query.order_by(asc("period_label"))

        # 6) Execute
        results = query.all()

        # 7) Transform results into a list of dicts:
        linechart_data = []
        for row in results:
            # row is a tuple: (period_label, files_count)
            linechart_data.append({
                "period_label": row.period_label,     # e.g. "2024-01" or "2024-05-14" depending on period_type
                "files_count": row.files_count
            })

        return linechart_data
