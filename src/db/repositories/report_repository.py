# db/repositories/report_repository.py


from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, date, timedelta
import calendar
from typing import Dict, List, Any, Optional, Tuple
import logging

from fastapi import HTTPException

from db.models import ProcessedData
from models.selected_period_aggregation import SelectedPeriodAggregation
from db.repositories.user_repository import UserRepository  # Import UserRepository
from models.currency_config import CurrencyConfig
from models.scatter_report import ScatterReport

logger = logging.getLogger(__name__)

class IncomeAndSpending:
    def __init__(self, no_data_flag: bool, total_income: float, total_spending: float):
        self.no_data_flag = no_data_flag
        self.total_income = total_income
        self.total_spending = total_spending

class ReportRepository:
    def __init__(self, session: Session, currency_configs: Dict[str, Dict], user_repository: UserRepository):
        self.session = session
        self.currency_configs = currency_configs
        self.user_repository = user_repository

    # --- Helper Methods ---

    def determine_currency_code(self, user_id: int, currency: Optional[str]) -> str:
        """
        Determine the currency code.
        If a currency is provided, return its uppercase value;
        otherwise, fall back to the user's default currency or "USD".
        """
        if currency:
            return currency.upper()
        user_settings = self.user_repository.get_user_settings(user_id)
        if user_settings and user_settings.default_currency:
            return user_settings.default_currency.upper()
        return "USD"

    def get_currency_configuration(self, currency_code: str) -> CurrencyConfig:
        """
        Retrieve the CurrencyConfig for the given currency code.
        Raises an HTTPException if the configuration is not found.
        """
        currency_data = self.currency_configs.get(currency_code.upper())
        if currency_data:
            return CurrencyConfig(
                symbol=currency_data.get('symbol'),
                name=currency_data.get('name'),
                symbol_native=currency_data.get('symbol_native'),
                fractional_digits=currency_data.get('decimal_digits'),
                rounding=currency_data.get('rounding'),
                name_plural=currency_data.get('name_plural'),
                symbol_placement=currency_data.get('symbol_placement', 'front')
            )
        logger.warning(f"Currency config not found for {currency_code}")
        raise HTTPException(status_code=400, detail=f"Unsupported currency code: {currency_code}")

    def convert_date_filters(self, start_date_filter: Any, end_date_filter: Any) -> Tuple[datetime, datetime]:
        """
        Convert the provided date filters (if not strings) into datetime objects.
        """
        if start_date_filter and not isinstance(start_date_filter, str):
            start_date_filter = start_date_filter.isoformat()
        if end_date_filter and not isinstance(end_date_filter, str):
            end_date_filter = end_date_filter.isoformat()
        try:
            start_dt = datetime.fromisoformat(start_date_filter) if start_date_filter else datetime(2000, 1, 1)
        except Exception as e:
            logger.error(f"Error parsing start_date_filter: {e}")
            raise HTTPException(status_code=400, detail="Invalid start_date format. Expected ISO format (YYYY-MM-DD).")
        try:
            end_dt = datetime.fromisoformat(end_date_filter) if end_date_filter else datetime(2030, 1, 1)
        except Exception as e:
            logger.error(f"Error parsing end_date_filter: {e}")
            raise HTTPException(status_code=400, detail="Invalid end_date format. Expected ISO format (YYYY-MM-DD).")
        return start_dt, end_dt

    def get_strftime_pattern(self, period_type: str) -> str:
        """
        Given a period type, return the corresponding SQLite strftime pattern.
        Allowed period types are "daily", "weekly", "monthly", and "yearly".
        """
        period_map = {
            "daily": "%Y-%m-%d",
            "weekly": "%G-W%V",
            "monthly": "%Y-%m",
            "yearly": "%Y",
        }
        ptype = period_type.lower()
        if ptype not in period_map:
            logger.error(f"Invalid period_type: {period_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported period_type: {period_type}")
        pattern = period_map[ptype]
        logger.debug(f"Using strftime pattern: {pattern}")
        return pattern

    def get_period_query(self, user_id: int, bank_account_id: Optional[int], start_dt: datetime, end_dt: datetime, strftime_pattern: str) -> List[Any]:
        """
        Build and execute a query to group ProcessedData records by period.
        """
        query = self.session.query(
            func.strftime(strftime_pattern, ProcessedData.record_date).label("period"),
            func.count(ProcessedData.record_id).label("frequency")
        ).filter(
            ProcessedData.user_id == user_id,
            ProcessedData.record_date >= start_dt,
            ProcessedData.record_date <= end_dt
        )
        if bank_account_id is not None:
            query = query.filter(ProcessedData.document_id == bank_account_id)
        query = query.group_by("period").order_by("period")
        return query.all()

    def calculate_period_start_end_dates(self, period_type: str, period_label: str) -> Tuple[datetime, datetime]:
        """
        Calculate the start and end datetime for a given period type and period label.
        """
        ptype = period_type.lower()
        if ptype == "daily":
            try:
                period_start = datetime.strptime(period_label, "%Y-%m-%d")
                period_end = period_start + timedelta(days=1) - timedelta(microseconds=1)
            except Exception as e:
                logger.error(f"Error parsing daily period {period_label}: {e}")
                raise HTTPException(status_code=500, detail="Error parsing daily period.")
        elif ptype == "weekly":
            try:
                period_start = datetime.strptime(period_label + "-1", "%G-W%V-%u")
                period_end = datetime.strptime(period_label + "-7", "%G-W%V-%u")
            except Exception as e:
                logger.error(f"Error computing weekly boundaries for {period_label}: {e}")
                raise HTTPException(status_code=500, detail="Error computing weekly boundaries.")
        elif ptype == "monthly":
            period_start_str = f"{period_label}-01"
            try:
                year, month = map(int, period_label.split('-'))
                last_day = 31 if month == 12 else (datetime(year, month + 1, 1) - timedelta(days=1)).day
            except Exception as e:
                logger.error(f"Error calculating last day for month {period_label}: {e}")
                last_day = 31
            period_start = datetime.strptime(period_start_str, "%Y-%m-%d")
            period_end = datetime.strptime(f"{period_label}-{last_day:02d}", "%Y-%m-%d")
        elif ptype == "yearly":
            period_start = datetime.strptime(period_label + "-01-01", "%Y-%m-%d")
            period_end = datetime.strptime(period_label + "-12-31", "%Y-%m-%d")
        else:
            # Fallback: treat the label as full ISO dates.
            period_start = datetime.fromisoformat(period_label)
            period_end = datetime.fromisoformat(period_label)
        return period_start, period_end

    # --- Report Methods ---
    def create_a_custom_report(self, user_id: int, searches: List[str], start_date: datetime, end_date: datetime, currency_code: str) -> Dict[str, Any]:
        """
        For each search string, query ProcessedData records that match the search (case-insensitively)
        for the given user and date range. Compute average, sum, and count.
        """
        currency_column_map = {
            "USD": ProcessedData.amount_in_dollar,
            "XAU": ProcessedData.amount_in_gold,
            "CHF": ProcessedData.amount_in_chf,
            "TRY": ProcessedData.amount,
        }
        amount_column = currency_column_map.get(currency_code, ProcessedData.amount_in_dollar)

        results_list = []
        overall_sum = 0
        overall_freq = 0

        for search in searches:
            try:
                query = self.session.query(
                    func.avg(amount_column).label("avg"),
                    func.sum(amount_column).label("sum"),
                    func.count(ProcessedData.record_id).label("freq")
                ).filter(
                    ProcessedData.user_id == user_id,
                    ProcessedData.record_date >= start_date,
                    ProcessedData.record_date <= end_date,
                    ProcessedData.text.ilike(f"%{search}%")
                )
                result = query.one()
            except Exception as e:
                logger.error(f"Error querying custom report for search '{search}': {e}")
                raise HTTPException(status_code=500, detail="Error querying custom report data.")

            avg_value = result.avg if result.avg is not None else 0
            sum_value = result.sum if result.sum is not None else 0
            freq_value = result.freq if result.freq is not None else 0

            overall_sum += sum_value
            overall_freq += freq_value

            matched_string = search if freq_value > 0 else ""
            results_list.append({
                "searched_string": search,
                "matched_string": matched_string,
                "avg": avg_value,
                "sum": sum_value,
                "freq": freq_value
            })

        overall_avg = overall_sum / overall_freq if overall_freq > 0 else 0
        totals = {"avg": overall_avg, "sum": overall_sum, "freq": overall_freq}
        return {"results": results_list, "totals": totals}

    def create_a_scatter_report(
        self,
        user_id: int,
        bank_account_id: int,
        start_date: str,
        end_date: str,
        master_category_list: Dict[str, List[str]],
        currency: str,
        category: str = None,
        subcategory: str = None
    ) -> List[ScatterReport]:
        logger.debug("Creating scatter report")
        # Convert start and end dates to datetime objects, if needed.
        start_dt = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
        end_dt = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date

        curr_code = self.determine_currency_code(user_id, currency)
        currency_config = self.get_currency_configuration(curr_code)

        currency_column_map = {
            'USD': ProcessedData.amount_in_dollar,
            'XAU': ProcessedData.amount_in_gold,
            'CHF': ProcessedData.amount_in_chf,
            'TRY': ProcessedData.amount,
        }
        amount_column = currency_column_map.get(curr_code, ProcessedData.amount_in_dollar)

        query = self.session.query(
            func.date(ProcessedData.record_date).label('day'),
            ProcessedData.category,
            ProcessedData.subcategory,
            func.count(ProcessedData.record_id).label('frequency'),
            func.sum(amount_column).label('total_amount')
        ).filter(
            ProcessedData.user_id == user_id,
            ProcessedData.record_date >= start_dt,
            ProcessedData.record_date <= end_dt
        )

        if bank_account_id is not None:
            query = query.filter(ProcessedData.document_id == bank_account_id)
        if category:
            query = query.filter(ProcessedData.category == category)
        if subcategory:
            query = query.filter(ProcessedData.subcategory == subcategory)

        query = query.group_by(
            func.date(ProcessedData.record_date),
            ProcessedData.category,
            ProcessedData.subcategory
        )
        results = query.all()

        scatter_reports = []
        for day, cat, subcat, freq, total_amt in results:
            if isinstance(day, str):
                day_obj = datetime.strptime(day, "%Y-%m-%d")
            else:
                day_obj = day
            day_of_week = day_obj.strftime("%A")
            scatter_reports.append(ScatterReport(
                date=day_obj.strftime("%Y-%m-%d"),
                frequency=freq,
                day_of_week=day_of_week,
                category=cat,
                subcategory=subcat,
                total_amount=total_amt,
                currency=curr_code
            ))
        return scatter_reports

    def aggregate_income_and_spending(
        self,
        user_id: int,
        bank_account_id: int,
        start_date: str,
        end_date: str,
        currency_code: str
    ) -> IncomeAndSpending:
        if isinstance(start_date, str):
            try:
                start_date = datetime.fromisoformat(start_date)
            except Exception as e:
                logger.error(f"Error parsing start_date: {e}")
                raise HTTPException(status_code=400, detail="Invalid start_date format.")
        if isinstance(end_date, str):
            try:
                end_date = datetime.fromisoformat(end_date)
            except Exception as e:
                logger.error(f"Error parsing end_date: {e}")
                raise HTTPException(status_code=400, detail="Invalid end_date format.")

        logger.debug(f"Inside aggregate_income_and_spending: start_date={start_date}, type_of_start_date={type(start_date)}, end_date={end_date}")

        def apply_bank_account_filter(query):
            if bank_account_id is not None:
                return query.filter(ProcessedData.document_id == bank_account_id)
            return query

        data_exists = apply_bank_account_filter(
            self.session.query(ProcessedData.record_id)
            .filter(
                ProcessedData.user_id == user_id,
                ProcessedData.record_date >= start_date,
                ProcessedData.record_date <= end_date
            )
        ).first() is not None
        logger.debug(f"data_exists {data_exists}")
        if not data_exists:
            return IncomeAndSpending(no_data_flag=True, total_income=0, total_spending=0)

        currency_column_map = {
            'USD': ProcessedData.amount_in_dollar,
            'XAU': ProcessedData.amount_in_gold,
            'CHF': ProcessedData.amount_in_chf,
            'TRY': ProcessedData.amount,
        }
        amount_column = currency_column_map[currency_code]

        total_income = apply_bank_account_filter(
            self.session.query(func.sum(amount_column))
            .filter(
                ProcessedData.user_id == user_id,
                ProcessedData.record_date >= start_date,
                ProcessedData.record_date <= end_date,
                ProcessedData.amount > 0
            )
        ).scalar() or 0
        logger.debug("Calculated total_income")

        total_spending = apply_bank_account_filter(
            self.session.query(func.sum(amount_column))
            .filter(
                ProcessedData.user_id == user_id,
                ProcessedData.record_date >= start_date,
                ProcessedData.record_date <= end_date,
                ProcessedData.amount < 0
            )
        ).scalar() or 0
        logger.debug("Calculated total_spending")

        return IncomeAndSpending(no_data_flag=False, total_income=total_income, total_spending=total_spending)

    def query_category_totals(
        self,
        user_id: int,
        bank_account_id: int,
        start_date: str,
        end_date: str,
        currency_code: str
    ):
        logger.debug(f"Querying category totals for user_id: {user_id}, bank_account_id: {bank_account_id}, start_date: {start_date}, end_date: {end_date}")
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)

        currency_column_map = {
            'USD': ProcessedData.amount_in_dollar,
            'XAU': ProcessedData.amount_in_gold,
            'CHF': ProcessedData.amount_in_chf,
            'TRY': ProcessedData.amount,
        }
        if currency_code not in currency_column_map:
            logger.error(f"Unsupported currency code: {currency_code}")
            raise HTTPException(status_code=400, detail=f"Unsupported currency code: {currency_code}")
        amount_column = currency_column_map[currency_code]

        query = self.session.query(
            ProcessedData.category,
            ProcessedData.subcategory,
            func.sum(amount_column).label('total_amount')
        ).filter(
            ProcessedData.user_id == user_id,
            ProcessedData.record_date >= start_date,
            ProcessedData.record_date <= end_date
        )
        if bank_account_id is not None:
            query = query.filter(ProcessedData.document_id == bank_account_id)
        query = query.group_by(ProcessedData.category, ProcessedData.subcategory)

        try:
            from sqlalchemy.dialects import sqlite
            compiled_query = query.statement.compile(dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True})
            logger.debug("Compiled SQL Query: %s", compiled_query)
        except Exception as compile_exc:
            logger.debug("Could not compile query: %s", compile_exc)

        results = query.all()
        logger.debug(f"Raw query_category_totals results: {results}")
        return results

    def aggregate_and_format_categories(
        self,
        queried_data,
        master_category_list: Dict[str, List[str]],
        currency_code: str
    ):
        logger.debug("Aggregating and formatting categories from queried data.")
        logger.debug(f"Queried data: {queried_data}")

        currency_config = self.get_currency_configuration(currency_code)
        category_dict = {category: {"total": 0, "subcategories": []} for category in master_category_list}

        for category, subcategory, total_amount in queried_data:
            logger.debug(f"Processing category: {category}, subcategory: {subcategory}, total: {total_amount}")
            if category in category_dict and subcategory in master_category_list.get(category, []):
                category_dict[category]["total"] += total_amount
                category_dict[category]["subcategories"].append({
                    "name": subcategory,
                    "total_amount": total_amount,
                    "currency": currency_code,
                    "currency_config": currency_config
                })

        logger.debug(f"Category dictionary before formatting: {category_dict}")

        category_aggregations = []
        for category_name, data in category_dict.items():
            if data["total"] != 0:
                category_aggregations.append({
                    "category_name": category_name,
                    "total": data["total"],
                    "currency": currency_code,
                    "currency_config": currency_config,
                    "subcategories": data["subcategories"]
                })

        logger.debug(f"Final category aggregations: {category_aggregations}")
        return category_aggregations

    def aggregate_categories_and_subcategories(
        self,
        user_id: int,
        bank_account_id: int,
        start_date: str,
        end_date: str,
        master_category_list: Dict[str, List[str]],
        currency_code: str
    ):
        queried_data = self.query_category_totals(user_id, bank_account_id, start_date, end_date, currency_code)
        return self.aggregate_and_format_categories(queried_data, master_category_list, currency_code)

    def create_a_piechart_report(
        self,
        user_id: int,
        bank_account_id: int,
        start_date: str,
        end_date: str,
        master_category_list: Dict[str, List[str]],
        currency: str
    ) -> SelectedPeriodAggregation:
        logger.debug("Inside create_a_piechart_report")
        if start_date is None:
            start_date = datetime(2000, 1, 1)
        if end_date is None:
            end_date = datetime(2040, 1, 1)

        curr_code = self.determine_currency_code(user_id, currency)
        currency_config = self.get_currency_configuration(curr_code)

        income_and_spending = self.aggregate_income_and_spending(user_id, bank_account_id, start_date, end_date, curr_code)
        if income_and_spending.no_data_flag:
            return SelectedPeriodAggregation(
                category_aggregations=[],
                total_income=0,
                total_spending=0,
                currency=curr_code,
                currency_config=currency_config
            )

        category_aggregations = self.aggregate_categories_and_subcategories(user_id, bank_account_id, start_date, end_date, master_category_list, curr_code)

        return SelectedPeriodAggregation(
            category_aggregations=category_aggregations,
            total_income=income_and_spending.total_income,
            total_spending=income_and_spending.total_spending,
            currency=curr_code,
            currency_config=currency_config
        )

    def get_last_day_of_month(self, month: str) -> int:
        year, month_num = map(int, month.split('-'))
        return calendar.monthrange(year, month_num)[1]

    def query_category_frequency(
        self,
        user_id: int,
        bank_account_id: int,
        start_date: str,
        end_date: str
    ):
        logger.debug(f"Querying category frequency for user_id: {user_id}, bank_account_id: {bank_account_id}, start_date: {start_date}, end_date: {end_date}")
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        query = self.session.query(
            ProcessedData.category,
            ProcessedData.subcategory,
            func.count(ProcessedData.record_id).label('frequency')
        ).filter(
            ProcessedData.user_id == user_id,
            ProcessedData.record_date >= start_date,
            ProcessedData.record_date <= end_date
        )
        if bank_account_id is not None:
            query = query.filter(ProcessedData.document_id == bank_account_id)
        results = query.group_by(ProcessedData.category, ProcessedData.subcategory).all()
        return results

    def aggregate_and_format_categories_frequency(
        self,
        queried_data,
        master_category_list: Dict[str, List[str]]
    ):
        logger.debug("Aggregating and formatting categories by frequency.")
        category_dict = {
            category: {"frequency": 0, "subcategories": []} for category in master_category_list
        }
        for category, subcategory, freq in queried_data:
            if category in category_dict and subcategory in master_category_list.get(category, []):
                category_dict[category]["frequency"] += freq
                category_dict[category]["subcategories"].append({
                    "name": subcategory,
                    "frequency": freq
                })
        category_aggregations = []
        for category_name, data in category_dict.items():
            if data["frequency"] > 0:
                category_aggregations.append({
                    "category_name": category_name,
                    "total": None,
                    "currency": None,
                    "currency_config": None,
                    "frequency": data["frequency"],
                    "subcategories": [
                        {"name": s["name"], "frequency": s["frequency"], "total_amount": None}
                        for s in data["subcategories"]
                    ]
                })
        return category_aggregations

    def create_historical_freq_report(
        self,
        user_id: int,
        bank_account_id: int,
        master_category_list: Dict[str, List[str]],
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        logger.debug(f"Creating historical frequency report for user_id: {user_id}, bank_account_id: {bank_account_id}, start_date: {start_date}, end_date: {end_date}")
        if start_date is None:
            start_date_obj = datetime(2000, 1, 1)
        else:
            start_date_obj = datetime.fromisoformat(start_date)
        if end_date is None:
            end_date_obj = datetime(2040, 1, 1)
        else:
            end_date_obj = datetime.fromisoformat(end_date)

        months = self.session.query(
            func.strftime('%Y-%m', ProcessedData.record_date).label('month')
        ).filter(
            ProcessedData.user_id == user_id,
            ProcessedData.record_date >= start_date_obj,
            ProcessedData.record_date <= end_date_obj
        )
        if bank_account_id is not None:
            months = months.filter(ProcessedData.document_id == bank_account_id)
        months = months.group_by(func.strftime('%Y-%m', ProcessedData.record_date)).all()
        logger.debug(f"Found months: {months}")

        historical_frequencies = []
        for month_tuple in months:
            month = month_tuple[0]
            logger.debug(f"Processing month: {month}")
            month_start_date = f"{month}-01"
            month_end_date = f"{month}-{self.get_last_day_of_month(month)}"
            category_freq_data = self.query_category_totals(user_id, bank_account_id, month_start_date, month_end_date, "TRY")
            category_aggregations = self.aggregate_and_format_categories_frequency(category_freq_data, master_category_list)
            total_frequency = sum(cat.get("frequency", 0) for cat in category_aggregations if cat.get("frequency"))
            historical_frequencies.append({
                "month": month,
                "category_aggregations": category_aggregations,
                "total_frequency": total_frequency
            })
        logger.debug(f"Final historical frequency data: {historical_frequencies}")
        return historical_frequencies

    def create_periodic_report(
        self,
        user_id: int,
        paradigm: str,
        period_type: str,
        bank_account_id: Optional[int] = None,
        start_date_filter: Any = None,
        end_date_filter: Any = None,
        master_category_list: Dict[str, List[str]] = None,
        currency: str = None
    ) -> List[Dict[str, Any]]:
        logger.debug(
            f"Creating periodic report for user_id: {user_id}, bank_account_id: {bank_account_id}, "
            f"start_date_filter: {start_date_filter}, end_date_filter: {end_date_filter}, "
            f"paradigm: {paradigm}, period_type: {period_type}, currency: {currency}"
        )

        # Determine currency code and get configuration.
        curr_code = self.determine_currency_code(user_id, currency)
        currency_config = self.get_currency_configuration(curr_code)

        # Convert date filters to datetime objects.
        start_dt, end_dt = self.convert_date_filters(start_date_filter, end_date_filter)

        # Get the SQLite strftime pattern based on period type.
        strftime_pattern = self.get_strftime_pattern(period_type)

        # Build and execute the period query.
        results = self.get_period_query(user_id, bank_account_id, start_dt, end_dt, strftime_pattern)
        logger.debug(f"Query results: {results}")
        
        historical_aggregations = []
        for row in results:
            period_label = row.period
            frequency = row.frequency
            logger.debug(f"Processing period: {period_label} with frequency: {frequency}")
            period_start, period_end = self.calculate_period_start_end_dates(period_type, period_label)
            logger.debug(f"--- Computed boundaries for period {period_label}: start={period_start.isoformat()}, end={period_end.isoformat()}")
            
            if paradigm.lower() == "amount":
                income_and_spending = self.aggregate_income_and_spending(user_id, bank_account_id, period_start.isoformat(), period_end.isoformat(), curr_code)
                total_income = income_and_spending.total_income
                total_spending = income_and_spending.total_spending
                total_money_flow= total_income + abs(total_spending)
                freq_value = None
                category_aggs = self.aggregate_categories_and_subcategories(user_id, bank_account_id, period_start.isoformat(), period_end.isoformat(), master_category_list, curr_code)
                logger.debug(f"Amount paradigm for {period_label}: income={total_income}, spending={total_spending}, categories={category_aggs}")
            elif paradigm.lower() == "freq":
                total_income = None
                total_spending = None
                total_money_flow= None
                category_freq_data = self.query_category_frequency(user_id, bank_account_id, period_start.isoformat(), period_end.isoformat())
                category_aggs = self.aggregate_and_format_categories_frequency(category_freq_data, master_category_list)
                freq_value = sum(cat.get("frequency", 0) for cat in category_aggs)
                logger.debug(f"Frequency paradigm for {period_label}: aggregated frequency={freq_value}, categories={category_aggs}")
            else:
                logger.error(f"Invalid paradigm: {paradigm}")
                raise HTTPException(status_code=400, detail="Invalid paradigm. Allowed values are 'amount' or 'freq'.")

            aggregation = {
                "period": period_label,
                "frequency": freq_value,
                "category_aggregations": category_aggs,
                "total_income": total_income,
                "total_spending": total_spending,
                "total_money_flow": total_money_flow,
                "currency": curr_code,
                "currency_config": currency_config.model_dump()
            }
            historical_aggregations.append(aggregation)
            logger.debug(f"Aggregation for period {period_label}: {aggregation}")
        
        logger.debug(f"Final historical aggregations: {historical_aggregations}")
        return historical_aggregations
    