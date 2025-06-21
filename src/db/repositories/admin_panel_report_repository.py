# db/repositories/admin_panel_report_repository.py

import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import asc, desc
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

from fastapi import HTTPException

from db.models import User, UserSettings, InitialData

logger = logging.getLogger(__name__)

class AdminPanelReportRepository:
    """
    Special-purpose repository for admin panel report queries (line charts, etc.).
    """

    def __init__(self, session: Session):
        self.session = session

    def get_new_bank_requests(
        self,
        start_dt: datetime,
        end_dt: datetime,
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the InitialData table for rows where `this_is_a_virgin_bank == True`
        within the given date range (upload_timestamp between start_dt and end_dt).
        Optionally filter by `country`.
        
        Return a list of dicts with the keys:
            file_id, bank_name, country, request_time
        where request_time is the `upload_timestamp` from InitialData.
        """

        query = (
            self.session.query(
                InitialData.document_id.label("file_id"),
                InitialData.associated_with.label("bank_name"),
                UserSettings.default_country.label("country"),
                InitialData.upload_timestamp.label("request_time")
            )
            .outerjoin(UserSettings, UserSettings.user_id == InitialData.user_id)
            .filter(InitialData.this_is_a_virgin_bank == True)
            .filter(InitialData.upload_timestamp >= start_dt)
            .filter(InitialData.upload_timestamp <= end_dt)
        )

        if country:
            query = query.filter(UserSettings.default_country.ilike(f"%{country}%"))

        # Optionally order by upload timestamp descending
        query = query.order_by(InitialData.upload_timestamp.desc())

        rows = query.all()

        results = []
        for row in rows:
            # row is a tuple with (file_id, bank_name, country, request_time)
            results.append({
                "file_id": row.file_id,
                "bank_name": row.bank_name,
                "country": row.country,
                # Convert datetime to ISO string
                "request_time": row.request_time.isoformat() if row.request_time else None
            })

        return results


    def get_file_report_total(
        self,
        start_dt: datetime,
        end_dt: datetime,
        country: Optional[str],
        bank_id: Optional[int],
        status: Optional[str]
    ) -> Dict[str, int]:
        """
        Returns a dictionary with aggregated counts, e.g.:
        {
          "total_files": int,
          "processed_files": int,
          "failed_files": int
        }
        over the specified date range and optional filters (country, bank, status).
        """

        # Base query
        query = (
            self.session.query(InitialData)
            .outerjoin(UserSettings, UserSettings.user_id == InitialData.user_id)
            .filter(InitialData.upload_timestamp >= start_dt)
            .filter(InitialData.upload_timestamp <= end_dt)
        )

        if country:
            query = query.filter(UserSettings.default_country.ilike(f"%{country}%"))

        if bank_id is not None:
            query = query.filter(InitialData.bank_id == bank_id)

        if status:
            query = query.filter(InitialData.process_status == status)

        # total_files
        total_files = query.count()

        # processed_files: e.g. how you define "processed"? Maybe `process_status='completed'` or `process_status_in_percentage=100`.
        # For example:
        processed_files = query.filter(InitialData.process_status == "completed").count()

        # failed_files:
        failed_files = query.filter(InitialData.process_status == "failed").count()

        return {
            "total_files": total_files,
            "processed_files": processed_files,
            "failed_files": failed_files
        }

    def get_file_report_linechart(
        self,
        period_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        country: Optional[str] = None,   # e.g. the user's 'default_country'
        bank_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns aggregated file upload counts over time (line chart),
        grouped by the given period_type (day, week, month, year),
        optionally filtered by date range, country, bank_id, and status.

        If period_type is None, default to "month".
        If start_date/end_date are not provided, we use a fallback range.
        """

        # (1) Default period_type:
        if not period_type:
            period_type = "month"
            logger.debug("No period_type provided; defaulting to 'month'")

        period_map = {
            "day":   "%Y-%m-%d",
            "week":  "%Y-%W",
            "month": "%Y-%m",
            "year":  "%Y",
        }

        if period_type not in period_map:
            logger.error(f"Invalid period_type: {period_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported period_type: {period_type}")

        strftime_pattern = period_map[period_type]

        # (2) Fallback date range
        if not start_date:
            start_date = date.today().replace(day=1) - timedelta(days=3650)
            logger.debug(f"No start_date given; defaulting to approx 10 years back: {start_date}")

        if not end_date:
            end_date = date.today() + timedelta(days=10)
            logger.debug(f"No end_date given; defaulting to today+10 days: {end_date}")

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt   = datetime.combine(end_date,   datetime.max.time())

        logger.debug("=== Debugging get_file_report_linechart ===")
        logger.debug(f"period_type={period_type}, start_dt={start_dt}, end_dt={end_dt}, "
                     f"country={country}, bank_id={bank_id}, status={status}")

        # (3) Build the base query
        query = (
            self.session.query(
                func.strftime(strftime_pattern, InitialData.upload_timestamp).label("period_label"),
                func.count(InitialData.document_id).label("files_count")
            )
            .outerjoin(UserSettings, UserSettings.user_id == InitialData.user_id)
        )

        # (4) Apply filters
        logger.debug("Applying filters to the query...")

        logger.debug("Filtering by upload_timestamp >= %s and <= %s", start_dt, end_dt)
        query = query.filter(InitialData.upload_timestamp >= start_dt)
        query = query.filter(InitialData.upload_timestamp <= end_dt)

        if country:
            logger.debug(f"Filtering by country (UserSettings.default_country ilike '%{country}%')")
            query = query.filter(UserSettings.default_country.ilike(f"%{country}%"))

        if bank_id is not None:
            logger.debug(f"Filtering by bank_id = {bank_id}")
            query = query.filter(InitialData.bank_id == bank_id)

        if status:
            logger.debug(f"Filtering by process_status = {status}")
            query = query.filter(InitialData.process_status == status)

        # (5) Group & order
        query = query.group_by("period_label").order_by(asc("period_label"))

        # (Optional) If you'd like to see the final SQL, do something like:
        # from sqlalchemy.dialects import sqlite
        # logger.debug("Final SQL: %s", str(query.statement.compile(dialect=sqlite.dialect())))

        # (6) Execute the query
        results = query.all()

        # Debug: what rows did we get from DB?
        logger.debug(f"Raw results from DB => {results}")
        if not results:
            logger.debug("No rows returned from this query => returning empty list later.")

        # (7) Transform each row
        linechart_data = []
        for row in results:
            # row is typically a tuple or Row object: (period_label, files_count)
            logger.debug(f"Row => period_label={row.period_label}, files_count={row.files_count}")
            linechart_data.append({
                "period_label": row.period_label,
                "files_count": row.files_count,
                # If you need more stats, add them here
            })

        logger.debug(f"linechart_data prepared => {linechart_data}")
        return linechart_data
