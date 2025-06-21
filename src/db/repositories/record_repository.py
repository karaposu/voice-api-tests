# db/repositories/record_repository.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from fastapi import HTTPException
import logging
import pandas as pd
from typing import List, Optional

from db.models import ProcessedData, InitialData
from models.split_record_dto import SplitRecordDTO

from sqlalchemy import func, distinct
from typing import List, Tuple
from datetime import date



from sqlalchemy import or_

logger = logging.getLogger(__name__)

class RecordRepository:
    def __init__(self, session: Session):
        self.session = session


    

    # get_selected_records_by_user_and_document
    def get_records_by_user_and_file(self, user_id: int, document_id: int,
                                                  selected_columns: Optional[List] = None) -> pd.DataFrame:
        """
        Retrieve selected records by user and document, returning a pandas DataFrame.

        Args:
            user_id (int): ID of the user.
            document_id (int): ID of the document.
            selected_columns (List): List of columns to retrieve. Defaults to a predefined set.

        Returns:
            pd.DataFrame: DataFrame containing the selected records.
        """
        try:
            # Specify the columns you want to include
            if selected_columns is None:
                selected_columns = [
                    ProcessedData.record_id,
                    ProcessedData.user_id,
                    ProcessedData.document_id,
                    ProcessedData.text,
                    ProcessedData.keyword,
                    ProcessedData.associated_with,
                    ProcessedData.is_active,
                    # Add other columns as necessary
                ]

            # Query the selected columns
            records = self.session.query(*selected_columns).filter_by(user_id=user_id, document_id=document_id).all()

            # Extract column names from the selected columns
            column_names = [column.key for column in selected_columns]

            # Create the data dictionary
            data = [
                {column_names[i]: value for i, value in enumerate(record)}
                for record in records
            ]

            # Create the DataFrame
            df = pd.DataFrame(data, columns=column_names)

            logger.debug(f"Retrieved {len(df)} records for user_id={user_id} and document_id={document_id}")

            return df

        except Exception as e:
            logger.error(f"Error retrieving selected records: {str(e)}")
            raise HTTPException(status_code=500, detail="Error retrieving selected records")

    def add_record(self, record_data: ProcessedData) -> int:
        try:
            if not record_data.processed_at:
                record_data.processed_at = datetime.utcnow()

            self.session.add(record_data)
            self.session.commit()
            return record_data.record_id
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding record: {str(e)}")
            raise HTTPException(status_code=500, detail="Error adding record")
        

    def get_records_with_pagination(
        self,
        user_id: int | None = None,
        document_id: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        associated_with: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str = "date",
        order: str = "desc",
        *,
        # ────────────────────────────────────────────────────────
        # NEW amount-range filters
        min_amount: float | None = None,
        max_amount: float | None = None,
        currency: str | None = None,
        # ────────────────────────────────────────────────────────
        keyword_search: str | None = None,
        exact_match: bool = False,
        by_category: str | None = None,
        by_subcategory: str | None = None,
        bring_cleaned_text: bool = False,
        bring_not_vetted: bool = False,
        bring_tax_deductible: bool = False,
        bring_failed_to_categorize: bool = False,
    ):
        logger.debug("Building query for get_records_with_pagination")

        qry = self.session.query(ProcessedData)

        # ─────────── basic filters (unchanged) ───────────
        if user_id is not None:
            qry = qry.filter(ProcessedData.user_id == user_id)
        if document_id is not None:
            qry = qry.filter(ProcessedData.document_id == document_id)
        if start_date is not None:
            qry = qry.filter(ProcessedData.record_date >= start_date)
        if end_date is not None:
            qry = qry.filter(ProcessedData.record_date <= end_date)
        if associated_with is not None:
            qry = qry.filter(ProcessedData.associated_with == associated_with)

        # ─────────── keyword & category filters (unchanged) ───────────
        if keyword_search:
            pattern = keyword_search if exact_match else f"%{keyword_search}%"
            cmp = ProcessedData.text if exact_match else ProcessedData.text.ilike(pattern)
            qry = qry.filter(cmp)
        if by_category:
            qry = qry.filter(ProcessedData.category == by_category)
        if by_subcategory:
            qry = qry.filter(ProcessedData.subcategory == by_subcategory)

        if bring_not_vetted:
            qry = qry.filter(ProcessedData.vetted_by_user.is_(False))
        if bring_tax_deductible:
            qry = qry.filter(ProcessedData.tax_deductable.is_(True))
        if bring_failed_to_categorize:
            qry = qry.filter(ProcessedData.categorization_result.is_(None))

        # ─────────── amount-range filter (NEW) ───────────
        if min_amount is not None or max_amount is not None:
            # Map ISO code → correct numeric column
            col_map = {
                "USD": ProcessedData.amount_in_dollar,
                "CHF": ProcessedData.amount_in_chf,
                "XAU": ProcessedData.amount_in_gold,
                "TRY": ProcessedData.amount,  # original currency
            }
            amount_col = col_map.get((currency or "TRY").upper(), ProcessedData.amount)
            
            if min_amount is not None:
                qry = qry.filter(amount_col >= min_amount)
            if max_amount is not None:
                qry = qry.filter(amount_col <= max_amount)

        # ─────────── sorting ───────────
        if sort_by == "amount":
            sort_col = (
                col_map.get((currency or "TRY").upper(), ProcessedData.amount)
                if "amount_col" in locals()
                else ProcessedData.amount
            )
        else:
            sort_col = ProcessedData.record_date

        qry = qry.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

        # ─────────── pagination & count ───────────
        total = qry.count()
        if limit is not None:
            qry = qry.limit(limit)
        if offset is not None:
            qry = qry.offset(offset)

        records = qry.all()
        return records, total


    # def get_records_with_pagination(
    #     self,
    #     user_id: int = None,
    #     document_id: int = None,
    #     start_date: str = None,
    #     end_date: str = None,
    #     associated_with: str = None,
    #     limit: int = None,
    #     offset: int = None,
    #     sort_by: str = 'date',
    #     order: str = 'desc',
    #     keyword_search: str = None,
    #     exact_match: bool = False,
    #     by_category: str = None,
    #     by_subcategory: str = None,
    #     bring_cleaned_text: bool = False,
    #     bring_not_vetted: bool = False,
    #     bring_tax_deductible: bool = False,
    #     bring_failed_to_categorize: bool = False
    # ):
    #     logger.debug("Building query for get_records_with_pagination")

    #     query = self.session.query(ProcessedData)

    #     # Apply filters based on provided parameters
    #     if user_id is not None:
    #         query = query.filter(ProcessedData.user_id == user_id)
    #         logger.debug(f"Filtered by user_id: {user_id}")

    #     if document_id is not None:
    #         query = query.filter(ProcessedData.document_id == document_id)
    #         logger.debug(f"Filtered by document_id: {document_id}")

    #     if start_date is not None:
    #         query = query.filter(ProcessedData.record_date >= start_date)
    #         logger.debug(f"Filtered by start_date: {start_date}")

    #     if end_date is not None:
    #         query = query.filter(ProcessedData.record_date <= end_date)
    #         logger.debug(f"Filtered by end_date: {end_date}")

    #     if associated_with is not None:
    #         query = query.filter(ProcessedData.associated_with == associated_with)
    #         logger.debug(f"Filtered by associated_with: {associated_with}")

    #     if keyword_search:
    #         logger.debug(f"Applying keyword search: {keyword_search}")
    #         if exact_match:
    #             logger.debug("Using exact match for keyword search")
    #             query = query.filter(ProcessedData.text == keyword_search)
    #         else:
    #             logger.debug("Using partial match for keyword search")
    #             keyword_pattern = f"%{keyword_search}%"
    #             query = query.filter(ProcessedData.text.ilike(keyword_pattern))

    #     if by_category:
    #         query = query.filter(ProcessedData.category == by_category)
    #         logger.debug(f"Filtered by category: {by_category}")

    #     if by_subcategory:
    #         query = query.filter(ProcessedData.subcategory == by_subcategory)
    #         logger.debug(f"Filtered by subcategory: {by_subcategory}")

    #     if bring_not_vetted:
    #         query = query.filter(ProcessedData.vetted_by_user == False)
    #         logger.debug("Filtered to bring not vetted records")

    #     if bring_tax_deductible:
    #         query = query.filter(ProcessedData.tax_deductable == True)
    #         logger.debug("Filtered to bring tax deductible records")

    #     if bring_failed_to_categorize:
    #         query = query.filter(ProcessedData.categorization_result == None)
    #         logger.debug("Filtered to bring records that failed to categorize")

    #     # Apply sorting
    #     if sort_by == 'amount':
    #         sort_column = ProcessedData.amount
    #         logger.debug("Sorting by amount")
    #     else:
    #         sort_column = ProcessedData.record_date
    #         logger.debug("Sorting by date")

    #     if order == 'asc':
    #         query = query.order_by(sort_column.asc())
    #         logger.debug("Order set to ascending")
    #     else:
    #         query = query.order_by(sort_column.desc())
    #         logger.debug("Order set to descending")

    #     # Get total count before applying limit and offset
    #     total = query.count()
    #     logger.debug(f"Total records found: {total}")

    #     # Apply pagination
    #     if limit is not None:
    #         query = query.limit(limit)
    #         logger.debug(f"Limit set to: {limit}")
        
    #     if offset is not None:
    #         query = query.offset(offset)
    #         logger.debug(f"Offset set to: {offset}")

    #     records = query.all()
    #     logger.debug(f"Number of records retrieved: {len(records)}")

    #     return records, total


    #this is in record_repository
    # def get_records_with_pagination(self,
    #                 user_id: int = None,
    #                 document_id: int = None,
    #                 start_date: str = None,
    #                 end_date: str = None,
    #                 associated_with: str = None,
    #                 limit: int = None,
    #                 offset: int = None):
    #
    #     query = self.session.query(ProcessedData)
    #
    #     if user_id is not None:
    #         query = query.filter(ProcessedData.user_id == user_id)
    #     if document_id is not None:
    #         query = query.filter(ProcessedData.document_id == document_id)
    #     if start_date is not None:
    #         query = query.filter(ProcessedData.record_date >= start_date)
    #     if end_date is not None:
    #         query = query.filter(ProcessedData.record_date <= end_date)
    #     if associated_with is not None:
    #         query = query.filter(ProcessedData.associated_with == associated_with)
    #
    #     total = query.count()
    #
    #     if limit is not None:
    #         query = query.limit(limit)
    #     if offset is not None:
    #         query = query.offset(offset)
    #
    #     records = query.all()
    #     return records, total

    def update_record(self, record_id: int, updates: dict):
        try:
            record_to_update = self.session.query(ProcessedData).filter_by(record_id=record_id).first()
            if record_to_update:
                for column, value in updates.items():
                    setattr(record_to_update, column, value)
                record_to_update.processed_at = datetime.utcnow()
                self.session.add(record_to_update)
                self.session.commit()
                logger.info(f"Record with record_id {record_id} updated successfully.")
            else:
                logger.error(f"Record with record_id {record_id} not found.")
                raise HTTPException(status_code=404, detail="Record not found")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating record with record_id {record_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error updating record")
    
    def get_records(self,
                    user_id: int = None,
                    document_id: int = None,
                    start_date: str = None,
                    end_date: str = None,
                    associated_with: str = None):

        query = self.session.query(ProcessedData)

        if user_id is not None:
            query = query.filter(ProcessedData.user_id == user_id)
        if document_id is not None:
            query = query.filter(ProcessedData.document_id == document_id)
        if start_date is not None:
            query = query.filter(ProcessedData.record_date >= start_date)
        if end_date is not None:
            query = query.filter(ProcessedData.record_date <= end_date)
        if associated_with is not None:
            query = query.filter(ProcessedData.associated_with == associated_with)

        # total = query.count()

        # if limit is not None:
        #     query = query.limit(limit)
        # if offset is not None:
        #     query = query.offset(offset)

        records = query.all()
        return records

    def update_processed_data(self, df: pd.DataFrame):
        try:
            for _, row in df.iterrows():
                record_id = row.get('record_id')
                if record_id is None:
                    logger.warning("Record ID not found in the data frame row. Skipping update.")
                    continue

                existing_record = self.session.query(ProcessedData).filter_by(record_id=record_id).first()

                if existing_record:
                    existing_record.amount = row.get('amount', existing_record.amount)
                    existing_record.rationale = row.get('rationale', existing_record.rationale)
                    existing_record.refiner_output = row.get('refiner_output', existing_record.refiner_output)
                    existing_record.category = row.get('lvl1', existing_record.category)
                    existing_record.subcategory = row.get('lvl2', existing_record.subcategory)
                    existing_record.categorized_by = row.get('categorized_by', existing_record.categorized_by)
                    existing_record.associated_with = row.get('associated_with', existing_record.associated_with)
                    existing_record.matched_auto_trigger_keyword = row.get('matched_auto_trigger_keyword',
                                                                           existing_record.matched_auto_trigger_keyword)
                    existing_record.matched_metapattern = row.get('matched_metapattern',
                                                                  existing_record.matched_metapattern)

                    self.session.add(existing_record)
                else:
                    logger.warning(f"Record not found for record_id {record_id}. Skipping update.")
                    continue

            self.session.commit()
            logger.info("ProcessedData table updated successfully.")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating ProcessedData: {str(e)}")
            raise HTTPException(status_code=500, detail="Error updating processed data")

    def delete_record(self, record_id: int):
        try:
            record_to_delete = self.session.query(ProcessedData).filter_by(record_id=record_id).first()

            if record_to_delete:
                self.session.delete(record_to_delete)
                self.session.commit()
                logger.info(f"Record with record_id {record_id} deleted successfully.")
            else:
                logger.error(f"Record with record_id {record_id} not found.")
                raise HTTPException(status_code=404, detail="Record not found")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting record with record_id {record_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error deleting record")

    def split_record(self, record_id: int, splits: List[SplitRecordDTO]):
        try:
            original_record = self.session.query(ProcessedData).filter_by(record_id=record_id).first()

            if not original_record:
                logger.error(f"Original record with record_id {record_id} not found.")
                raise HTTPException(status_code=404, detail="Original record not found")

            original_record.is_active = False
            original_record.is_split = True
            self.session.add(original_record)

            for split_data in splits:
                if not isinstance(split_data, SplitRecordDTO):
                    logger.error(f"Expected SplitRecordDTO, got {type(split_data)}")
                    raise HTTPException(status_code=400, detail="Invalid split data format")

                split_amount_in_dollar=(original_record.amount_in_dollar/ original_record.amount) * split_data.amount
                split_amount_in_gold=(original_record.amount_in_gold/ original_record.amount) * split_data.amount
                split_amount_in_chf=(original_record.amount_in_chf/ original_record.amount) * split_data.amount

                split_record = ProcessedData(
                    user_id=original_record.user_id,
                    document_id=original_record.document_id,
                    text=split_data.text,
                    cleaned_text=split_data.text,
                    amount=split_data.amount,
                    category=split_data.category,
                    subcategory=split_data.subcategory,
                    rationale="",
                    refiner_output="",
                    categorized_by="user",
                    record_date=datetime.utcnow(),
                    associated_with=original_record.associated_with,
                    parent_record_id=original_record.record_id,
                    split_level=original_record.split_level + 1,
                    is_active=True,
                    amount_in_dollar= split_amount_in_dollar,
                    amount_in_gold= split_amount_in_gold,
                    amount_in_chf= split_amount_in_chf

                )
                self.session.add(split_record)

            self.session.commit()
            logger.info(f"Record with record_id {original_record.record_id} split successfully into {len(splits)} records.")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error splitting record with record_id {record_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error splitting record")

    def merge_splits(self, original_record_id: int):
        try:
            original_record = self.session.query(ProcessedData).filter_by(record_id=original_record_id).first()

            if not original_record:
                logger.error(f"Original record with id {original_record_id} not found.")
                raise HTTPException(status_code=404, detail="Original record not found")

            split_records = self.session.query(ProcessedData).filter_by(parent_record_id=original_record_id,
                                                                        is_active=True).all()

            if not split_records:
                logger.error(f"No active split records found for original record id {original_record_id}.")
                raise HTTPException(status_code=404, detail="No active split records found")

            original_record.is_active = True
            original_record.is_split = False
            self.session.add(original_record)

            for split_record in split_records:
                split_record.is_active = False
                self.session.add(split_record)

            self.session.commit()
            logger.info(f"Record with record_id {original_record_id} merged successfully from {len(split_records)} split records.")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error merging record with record_id {original_record_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error merging records")

    def revert_split(self, record_id: int):
        try:
            original_record = self.session.query(ProcessedData).filter_by(record_id=record_id).first()

            if not original_record:
                logger.error(f"Original record with record_id {record_id} not found.")
                raise HTTPException(status_code=404, detail="Original record not found")

            split_records = self.session.query(ProcessedData).filter_by(parent_record_id=record_id).all()

            if not split_records:
                logger.warning(f"No split records found for original record_id {record_id}.")
                raise HTTPException(status_code=404, detail="No split records found")

            for record in split_records:
                record.is_active = False
                self.session.add(record)

            original_record.is_active = True
            original_record.is_split = False
            self.session.add(original_record)

            self.session.commit()
            logger.info(f"Reverted split for record_id {record_id} successfully.")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error reverting split for record_id {record_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error reverting split")
    

    # def monthly_stats_for_year(
    #     self,
    #     user_id: int,
    #     year: int
    # ) -> List[Tuple[int, int, int]]:
    #     """
    #     Returns list of tuples (month, record_total, file_count)
    #     for the given user & calendar year.
    #     """
    #     start_dt = date(year, 1, 1)
    #     end_dt   = date(year, 12, 31)

    #     rows = (self.session
    #             .query(
    #                 func.cast(func.strftime('%m', ProcessedData.record_date), int).label("month"),
    #                 func.count().label("record_total"),
    #                 func.count(distinct(ProcessedData.document_id)).label("file_count")
    #             )
    #             .filter(
    #                 ProcessedData.user_id == user_id,
    #                 ProcessedData.record_date >= start_dt,
    #                 ProcessedData.record_date <= end_dt
    #             )
    #             .group_by("month")
    #             .all())
    #     return rows
    


    def monthly_stats_for_year(self, user_id: int, year: str):
        return (
            self.session
                .query(
                    func.strftime('%Y-%m', ProcessedData.record_date).label('month'),
                    func.count(ProcessedData.record_id).label('total_records'),
                    func.count(func.distinct(ProcessedData.document_id)).label('unique_files')
                )
                .filter(
                    ProcessedData.user_id == user_id,
                    func.strftime('%Y', ProcessedData.record_date) == year
                )
                .group_by('month')
                .order_by('month')
                .all()
        )

