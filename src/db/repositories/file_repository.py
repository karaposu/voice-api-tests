# db/repositories/file_repository.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from fastapi import HTTPException
import logging
from io import StringIO
import pandas as pd

from db.models import InitialData, ProcessedData
from db.repositories.exchange_rate_repository import ExchangeRateRepository

import tempfile
import os

def get_current_time():
    return datetime.now()
import logging
logger = logging.getLogger(__name__)


def parse_date(value):
    """Helper to convert an ISO date string to a datetime object."""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception as e:
        raise ValueError(f"Invalid date format: {value}") from e

class FileRepository:
    def __init__(self, session: Session):
        self.session = session
        # self.exchange_rate_repository = exchange_rate_repository

    def upload_snapshot(self, user_id: int, initial_data: dict, processed_data: list) -> int:
        """
        Uploads a snapshot (YAML/JSON) to restore processed data into the system.
        The provided YAML/JSON snapshot contains an "initial_data" dict and a "processed_data" list.
        Any user-specific fields such as "document_id" and "user_id" from the snapshot are removed
        to avoid security issues, and the authenticated user's ID is set instead.
        
        :param user_id: The authenticated user's ID.
        :param initial_data: A dict containing metadata about the file.
        :param processed_data: A list of dicts representing processed records.
        :return: The new document_id for the uploaded snapshot.
        :raises HTTPException: If any error occurs during the upload.
        """
        # Remove forbidden fields from initial_data and force user_id assignment.
        for field in ["document_id", "user_id"]:
            if field in initial_data:
                del initial_data[field]
        initial_data["user_id"] = user_id

        # Convert date strings to datetime objects for initial_data.
        date_fields = ["start_date", "end_date", "upload_timestamp", "process_started_at", "process_completed_at"]
        for field in date_fields:
            if field in initial_data and initial_data[field] is not None:
                try:
                    initial_data[field] = parse_date(initial_data[field])
                except ValueError as ve:
                    raise HTTPException(status_code=400, detail=str(ve))

        # Process each record in processed_data:
        for record in processed_data:
            # Remove forbidden fields from each record.
            for forbidden in ["record_id", "user_id", "document_id"]:
                if forbidden in record:
                    del record[forbidden]
            # Set the user_id from the authenticated user.
            record["user_id"] = user_id
            # Convert date fields in the record.
            for field in ["record_date", "processed_at"]:
                if field in record and record[field] is not None:
                    try:
                        record[field] = parse_date(record[field])
                    except ValueError as ve:
                        raise HTTPException(status_code=400, detail=str(ve))

        try:
            # Create an instance of InitialData from the initial_data dict.
            initial_instance = InitialData(**initial_data)
            self.session.add(initial_instance)
            # Flush to generate a new document_id.
            self.session.flush()

            # Insert each processed record.
            for record in processed_data:
                # Ensure the processed record gets the new document_id.
                record["document_id"] = initial_instance.document_id
                processed_instance = ProcessedData(**record)
                self.session.add(processed_instance)

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Error saving snapshot: {e}") from e

        return initial_instance.document_id
    
    def old_upload_snapshot(self, user_id: int, initial_data: dict, processed_data: list) -> int:
        """
        Uploads a YAML snapshot to restore file data back into the system.
        This method creates a new InitialData record and its associated ProcessedData records,
        ignoring any 'document_id' or 'user_id' coming from the snapshot to avoid tampering.
        
        Parameters:
            user_id (int): The authenticated user's ID.
            initial_data (dict): Dictionary containing initial file metadata.
            processed_data (list): List of dictionaries, each representing a processed record.
            
        Returns:
            int: The new document_id for the uploaded snapshot.
            
        Raises:
            Exception: Rolls back the session and re-raises any exceptions encountered.
        """
        try:
            # Define the allowed fields for the initial_data (fields that can be safely set)
            allowed_initial_fields = {
                'raw_data_format', 'associated_with', 'bank_id', 'start_date', 'end_date',
                'number_of_records', 'number_of_duplicate_records', 'upload_timestamp',
                'currency', 'country_code', 'bank_account_id', 'bank_account_alias',
                'number_of_processed_records', 'process_status', 'process_status_in_percentage',
                'process_started_at', 'process_completed_at', 'remaining_time_estimation',
                'remaining_time_estimation_str', 'number_of_cantcategorized', 'this_is_a_virgin_bank',
                'virgin_bank_status', 'user_proposed_bank_name'
            }
            # Remove unwanted keys (e.g., document_id, user_id) to prevent spoofing
            clean_initial = {k: v for k, v in initial_data.items() if k in allowed_initial_fields}
            # Enforce the authenticated user's id
            clean_initial['user_id'] = user_id
            # Optionally, you may override the upload_timestamp with the current time if desired:
            if 'upload_timestamp' not in clean_initial or clean_initial['upload_timestamp'] is None:
                clean_initial['upload_timestamp'] = datetime.utcnow()

            # Create a new InitialData record
            new_initial = InitialData(**clean_initial)
            self.session.add(new_initial)
            # Flush to assign a new document_id
            self.session.flush()
            new_document_id = new_initial.document_id

            # Define allowed fields for each processed record
            allowed_processed_fields = {
                'text', 'cleaned_text', 'amount', 'amount_in_dollar', 'amount_in_gold',
                'amount_in_chf', 'currency', 'keyword', 'rationale', 'refiner_output',
                'categorization_result', 'category', 'subcategory', 'categorized_by',
                'loaded_from_keyword_cache', 'record_date', 'associated_with', 'processed_at',
                'is_active', 'backup_category', 'backup_subcategory', 'parent_record_id', 'split_level',
                'is_split', 'apply_to_similar_records', 'attached_file_name', 'attached_file_type',
                'matched_auto_trigger_keyword', 'matched_metapattern', 'tax_deductable',
                'source_of_income', 'transfer_to_self', 'vetted_by_user', 'transfer_to_saving',
                # You may include other fields if needed.
            }

            new_processed_records = []
            for rec in processed_data:
                # Remove fields that should not be set (like record_id, user_id, document_id)
                clean_rec = {k: v for k, v in rec.items() if k in allowed_processed_fields}
                # Enforce the authenticated user's id and the new document id
                clean_rec['user_id'] = user_id
                clean_rec['document_id'] = new_document_id
                new_processed_records.append(clean_rec)

            if new_processed_records:
                # Use bulk_insert_mappings for efficiency (alternatively, add each ProcessedData instance individually)
                self.session.bulk_insert_mappings(ProcessedData, new_processed_records)

            # Return the newly created document id for reference
            return new_document_id

        except Exception as e:
            self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Error uploading snapshot: {e}")
    
    def get_file_snapshot(self, file_id: int) -> dict:
        """
        Retrieve a snapshot of file data for a given file_id.
        Only selected fields from the InitialData and associated ProcessedData records
        are returned (i.e. excluding raw binary and encoded data).
        """
        try:
            # Retrieve the InitialData record using document_id as file_id
            initial = self.session.query(InitialData).filter(InitialData.document_id == file_id).one_or_none()
            if not initial:
                return None

            # Build a dictionary of the initial data (excluding raw data fields)
            initial_data = {
                "document_id": initial.document_id,
                "user_id": initial.user_id,
                "family_member_id": initial.family_member_id,
                "raw_data_format": initial.raw_data_format,
                "associated_with": initial.associated_with,
                "bank_id": initial.bank_id,
                "start_date": initial.start_date,
                "end_date": initial.end_date,
                "number_of_records": initial.number_of_records,
                "number_of_duplicate_records": initial.number_of_duplicate_records,
                "upload_timestamp": initial.upload_timestamp.isoformat() if initial.upload_timestamp else None,
                "currency": initial.currency,
                "country_code": initial.country_code,
                "bank_account_id": initial.bank_account_id,
                "bank_account_alias": initial.bank_account_alias,
                "number_of_processed_records": initial.number_of_processed_records,
                "process_status": initial.process_status,
                "process_status_in_percentage": initial.process_status_in_percentage,
                "process_started_at": initial.process_started_at.isoformat() if initial.process_started_at else None,
                "process_completed_at": initial.process_completed_at.isoformat() if initial.process_completed_at else None,
                "remaining_time_estimation": initial.remaining_time_estimation,
                "remaining_time_estimation_str": initial.remaining_time_estimation_str,
                "number_of_cantcategorized": initial.number_of_cantcategorized,
                "this_is_a_virgin_bank": initial.this_is_a_virgin_bank,
                "virgin_bank_status": initial.virgin_bank_status,
                "user_proposed_bank_name": initial.user_proposed_bank_name,
            }

            # Retrieve all associated ProcessedData records
            processed_list = self.session.query(ProcessedData).filter(ProcessedData.document_id == file_id).all()
            processed_data = []
            for record in processed_list:
                rec = {
                    "record_id": record.record_id,
                    "user_id": record.user_id,
                    "family_member_id": record.family_member_id,
                    "document_id": record.document_id,
                    "text": record.text,
                    "cleaned_text": record.cleaned_text,
                    "amount": record.amount,
                    "amount_in_dollar": record.amount_in_dollar,
                    "amount_in_gold": record.amount_in_gold,
                    "amount_in_chf": record.amount_in_chf,
                    "currency": record.currency,
                    "keyword": record.keyword,
                    "rationale": record.rationale,
                    "refiner_output": record.refiner_output,
                    "categorization_result": record.categorization_result,
                    "category": record.category,
                    "subcategory": record.subcategory,
                    "categorized_by": record.categorized_by,
                    "loaded_from_keyword_cache": record.loaded_from_keyword_cache,
                    "record_date": record.record_date.isoformat() if record.record_date else None,
                    "associated_with": record.associated_with,
                    "processed_at": record.processed_at.isoformat() if record.processed_at else None,
                    "is_active": record.is_active,
                    "backup_category": record.backup_category,
                    "backup_subcategory": record.backup_subcategory,
                    "parent_record_id": record.parent_record_id,
                    "split_level": record.split_level,
                    "is_split": record.is_split,
                    "apply_to_similar_records": record.apply_to_similar_records,
                    "attached_file_name": record.attached_file_name,
                    "attached_file_type": record.attached_file_type,
                    "matched_auto_trigger_keyword": record.matched_auto_trigger_keyword,
                    "matched_metapattern": record.matched_metapattern,
                    "tax_deductable": record.tax_deductable,
                    "source_of_income": record.source_of_income,
                    "transfer_to_self": record.transfer_to_self,
                    "vetted_by_user": record.vetted_by_user,
                    "transfer_to_saving": record.transfer_to_saving,
                    "bank_account_id": record.bank_account_id
                }
                processed_data.append(rec)

            snapshot = {"initial_data": initial_data, "processed_data": processed_data}
            return snapshot

        except Exception as e:
            logger.error(f"Error in get_file_snapshot: {e}", exc_info=True)
            raise

    # def get_file_snapshot(self, file_id: int) -> dict:
    #     """
    #     Retrieve a snapshot of file data for a given file_id.
    #     Only selected fields from the InitialData and ProcessedData tables are returned,
    #     omitting raw data fields.
    #     """
    #     try:
    #         # Retrieve the initial_data record
    #         initial = self.session.query(InitialData).filter(InitialData.document_id == file_id).one_or_none()
    #         if not initial:
    #             return None

    #         # Build a dictionary of initial data (excluding raw data fields)
    #         initial_data = {
    #             "document_id": initial.document_id,
    #             "user_id": initial.user_id,
    #             "family_member_id": initial.family_member_id,
    #             "raw_data_format": initial.raw_data_format,
    #             "associated_with": initial.associated_with,
    #             "bank_id": initial.bank_id,
    #             "start_date": initial.start_date,
    #             "end_date": initial.end_date,
    #             "number_of_records": initial.number_of_records,
    #             "number_of_duplicate_records": initial.number_of_duplicate_records,
    #             "upload_timestamp": initial.upload_timestamp.isoformat() if initial.upload_timestamp else None,
    #             "currency": initial.currency,
    #             "country_code": initial.country_code,
    #             "bank_account_id": initial.bank_account_id,
    #             "bank_account_alias": initial.bank_account_alias,
    #             "number_of_processed_records": initial.number_of_processed_records,
    #             "process_status": initial.process_status,
    #             "process_status_in_percentage": initial.process_status_in_percentage,
    #             "process_started_at": initial.process_started_at.isoformat() if initial.process_started_at else None,
    #             "process_completed_at": initial.process_completed_at.isoformat() if initial.process_completed_at else None,
    #             "remaining_time_estimation": initial.remaining_time_estimation,
    #             "remaining_time_estimation_str": initial.remaining_time_estimation_str,
    #             "number_of_cantcategorized": initial.number_of_cantcategorized,
    #             "this_is_a_virgin_bank": initial.this_is_a_virgin_bank,
    #             "virgin_bank_status": initial.virgin_bank_status,
    #             "user_proposed_bank_name": initial.user_proposed_bank_name
    #         }

    #         # Retrieve all processed_data records associated with the file_id
    #         processed_list = self.session.query(ProcessedData).filter(ProcessedData.document_id == file_id).all()
    #         processed_data = []
    #         for record in processed_list:
    #             rec = {
    #                 "record_id": record.record_id,
    #                 "user_id": record.user_id,
    #                 "family_member_id": record.family_member_id,
    #                 "document_id": record.document_id,
    #                 "text": record.text,
    #                 "cleaned_text": record.cleaned_text,
    #                 "amount": record.amount,
    #                 "amount_in_dollar": record.amount_in_dollar,
    #                 "amount_in_gold": record.amount_in_gold,
    #                 "amount_in_chf": record.amount_in_chf,
    #                 "currency": record.currency,
    #                 "keyword": record.keyword,
    #                 "rationale": record.rationale,
    #                 "refiner_output": record.refiner_output,
    #                 "categorization_result": record.categorization_result,
    #                 "category": record.category,
    #                 "subcategory": record.subcategory,
    #                 "categorized_by": record.categorized_by,
    #                 "loaded_from_keyword_cache": record.loaded_from_keyword_cache,
    #                 "record_date": record.record_date.isoformat() if record.record_date else None,
    #                 "associated_with": record.associated_with,
    #                 "processed_at": record.processed_at.isoformat() if record.processed_at else None,
    #                 "is_active": record.is_active,
    #                 "backup_category": record.backup_category,
    #                 "backup_subcategory": record.backup_subcategory,
    #                 "parent_record_id": record.parent_record_id,
    #                 "split_level": record.split_level,
    #                 "is_split": record.is_split,
    #                 "apply_to_similar_records": record.apply_to_similar_records,
    #                 "attached_file_name": record.attached_file_name,
    #                 "attached_file_type": record.attached_file_type,
    #                 "matched_auto_trigger_keyword": record.matched_auto_trigger_keyword,
    #                 "matched_metapattern": record.matched_metapattern,
    #                 "tax_deductable": record.tax_deductable,
    #                 "source_of_income": record.source_of_income,
    #                 "transfer_to_self": record.transfer_to_self,
    #                 "vetted_by_user": record.vetted_by_user,
    #                 "transfer_to_saving": record.transfer_to_saving,
    #                 "bank_account_id": record.bank_account_id
    #             }
    #             processed_data.append(rec)

    #         snapshot = {"initial_data": initial_data, "processed_data": processed_data}
    #         return snapshot
    #     except Exception as e:
    #         logger.error(f"Error in get_file_snapshot: {e}", exc_info=True)
    #         raise




    def get_categorization_status(self, user_id: int, file_id: int):
        # Retrieve the InitialData record for the given user_id and file_id
        initial_data = self.session.query(InitialData).filter_by(user_id=user_id, document_id=file_id).first()

        if initial_data:
            # Prepare the status data
            remaining_time_estimation = initial_data.remaining_time_estimation or 0
            remaining_time_estimation_str = initial_data.remaining_time_estimation_str
            status_in_percentage = initial_data.process_status_in_percentage
            status = initial_data.process_status
            num_records = initial_data.number_of_records
            number_of_processed_records = initial_data.number_of_processed_records or 0
            upload_timestamp = initial_data.upload_timestamp.isoformat() if initial_data.upload_timestamp else None

            # Create a dictionary with the status data
            status_data = {
                'remaining_time_estimation': int(remaining_time_estimation),
                'remaining_time_estimation_str': remaining_time_estimation_str,
                'status_in_percentage': status_in_percentage,
                'status': status,
                'num_records': num_records,
                'number_of_processed_records': number_of_processed_records,
                'upload_timestamp': upload_timestamp
            }

            return status_data
        else:
            logger.error(f"File with id {file_id} for user {user_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

    def save_raw_binary_to_db(self,
                              bank_name,
                              bank_id,
                              user_id,
                              currency,
                              country_code,
                              binary_file,
                              extension, 
                              this_is_a_virgin_bank, 
                              virgin_bank_status, 
                              user_proposed_bank_name

                           

                              ) -> int:
        file_data = binary_file  # Use the binary file data directly

        # associated_with

        # Store the binary data directly for all file types
        initial_data_entry = InitialData(
            user_id=user_id,
            raw_data_format=extension,
            binary_data=file_data,
            associated_with=bank_name,
            bank_id=bank_id,
            upload_timestamp=get_current_time(),
            currency=currency,
            country_code=country_code,
            this_is_a_virgin_bank =this_is_a_virgin_bank,
            virgin_bank_status=  virgin_bank_status, 
            user_proposed_bank_name=user_proposed_bank_name

        )

        self.session.add(initial_data_entry)
        self.session.commit()
        return initial_data_entry.document_id

    # def save_raw_binary_to_db(self,
    #                           bank_name,
    #                           bank_id,
    #                           user_id,
    #                           currency,
    #                           country_code,
    #                           binary_file,
    #                           extension) -> int:
    #     file_data = binary_file  # Use the binary file data directly
    #
    #     if extension == 'pdf':
    #         # For PDFs, you may need to decode the binary data
    #         try:
    #             encoded_raw_data = file_data.decode('latin-1')
    #         except UnicodeDecodeError as e:
    #             logger.error(f"Error decoding PDF file data: {e}")
    #             raise HTTPException(status_code=400, detail="Failed to decode PDF file data")
    #
    #         initial_data_entry = InitialData(
    #             user_id=user_id,
    #             raw_data_format='pdf',
    #             encoded_raw_data=encoded_raw_data,
    #             associated_with=bank_name,
    #             bank_id=bank_id,
    #             upload_timestamp=get_current_time(),
    #             currency=currency,
    #             country_code=country_code,
    #         )
    #
    #     elif extension in ['xlsx', 'xls', 'csv']:
    #         initial_data_entry = InitialData(
    #             user_id=user_id,
    #             raw_data_format=extension,
    #             binary_data=file_data,
    #             associated_with=bank_name,
    #             bank_id=bank_id,
    #             upload_timestamp=get_current_time(),
    #             currency=currency,
    #             country_code=country_code
    #         )
    #     else:
    #         raise ValueError(f"Unsupported file format: {extension}")
    #
    #     self.session.add(initial_data_entry)
    #     self.session.commit()
    #     return initial_data_entry.document_id


    def get_any_file_admin(self, file_id: int) -> dict:
        """
        Retrieve the stored binary data (and possibly other relevant metadata)
        for the file with the given user_id and file_id.

        Returns a dictionary like:
            {
                "raw_data_format": str,
                "binary_data": bytes,
                "encoded_raw_data": Optional[str],  # if applicable
            }

        Raises HTTPException(404) if the file does not exist.
        """
        # Fetch the InitialData record
        file_record = self.get_file_by_file_id( file_id)
        if not file_record:
            logger.error(f"File with id {file_id} not found")
            raise HTTPException(status_code=404, detail="File not found")
        
        # Build the response dict
        file_info = {
            "raw_data_format": file_record.raw_data_format,
            "binary_data": file_record.binary_data,
            "encoded_raw_data": file_record.encoded_raw_data,  # might be None unless it's a PDF or something
        }
        return file_info

    def get_binary_file(self, user_id: int, file_id: int) -> dict:
        """
        Retrieve the stored binary data (and possibly other relevant metadata)
        for the file with the given user_id and file_id.

        Returns a dictionary like:
            {
                "raw_data_format": str,
                "binary_data": bytes,
                "encoded_raw_data": Optional[str],  # if applicable
            }

        Raises HTTPException(404) if the file does not exist.
        """
        # Fetch the InitialData record
        file_record = self.get_file_by_user_and_file_id(user_id, file_id)
        if not file_record:
            logger.error(f"File with id {file_id} for user {user_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

        # Build the response dict
        file_info = {
            "raw_data_format": file_record.raw_data_format,
            "binary_data": file_record.binary_data,
            "encoded_raw_data": file_record.encoded_raw_data,  # might be None unless it's a PDF or something
        }
        return file_info

    

    def get_file_by_file_id(self, file_id: int) -> InitialData:
        file_record = self.session.query(InitialData).filter_by(document_id=file_id).first()
        return file_record

    def get_file_by_user_and_file_id(self, user_id: int, file_id: int) -> InitialData:
        file_record = self.session.query(InitialData).filter_by(user_id=user_id, document_id=file_id).first()
        return file_record

    def delete_file(self, user_id: int, file_id: int, delete_records=True):
        file_to_delete = self.get_file_by_user_and_file_id(user_id, file_id)
        if not file_to_delete:
            logger.error(f"File with id {file_id} for user {user_id} not found")
            raise HTTPException(status_code=404, detail="File not found")

        if delete_records:
            # Delete associated ProcessedData records
            self.session.query(ProcessedData).filter_by(document_id=file_id).delete()
        else:
            # Check if there are any associated ProcessedData records
            count = self.session.query(ProcessedData).filter_by(document_id=file_id).count()
            if count > 0:
                logger.error(f"Cannot delete file {file_id} because there are associated ProcessedData records")
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete file because there are associated records. Set delete_records=True to delete them."
                )

        self.session.delete(file_to_delete)
        self.session.commit()
        logger.info(f"File with id {file_id} for user {user_id} deleted successfully")

    # def delete_file(self, user_id: int, file_id: int, delete_records=True):
    #
    #     file_to_delete = self.get_file_by_user_and_file_id(user_id, file_id)
    #     if not file_to_delete:
    #         logger.error(f"File with id {file_id} for user {user_id} not found")
    #         raise HTTPException(status_code=404, detail="File not found")
    #
    #     self.session.delete(file_to_delete)
    #     self.session.commit()
    #     logger.info(f"File with id {file_id} for user {user_id} deleted successfully")

    def should_log_progress(self, number_of_processed_records: int, total_records: int, n: int = 1) -> bool:
        return (number_of_processed_records % n == 0) or (number_of_processed_records == total_records)

    def log_progress(
            self,
            current_record: int,
            total_records: int,
            progress_percentage: float,
            remaining_time_seconds: int,
            remaining_time_str: str,
            user_id: int,
            file_id: int
    ):
        if self.should_log_progress(current_record, total_records):
            logger.debug(
                f"Processed {current_record}/{total_records} records ({progress_percentage:.2f}% complete), "
                f"remaining time: {remaining_time_str}"
            )

            try:
                selected_file_row = self.get_file_by_user_and_file_id(user_id, file_id)

                if selected_file_row:
                    selected_file_row.number_of_processed_records = current_record
                    selected_file_row.process_status_in_percentage = int(progress_percentage)
                    if remaining_time_seconds is not None:
                        selected_file_row.remaining_time_estimation = remaining_time_seconds  # Store remaining time in seconds
                        selected_file_row.remaining_time_estimation_str = remaining_time_str  # Optionally store the formatted string
                    self.session.add(selected_file_row)
                    self.session.commit()
                    logger.debug(f"Updated progress for file_id {file_id}")
                else:
                    logger.error(f"File with id {file_id} for user {user_id} not found")
                    raise HTTPException(status_code=404, detail="File not found")
            except Exception as e:
                logger.error(f"Error logging progress: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Failed to log progress")
            
    
    def update_processing_status(
        self,
        user_id: int,
        file_id: int,
        patch
    ):
        row = self.get_file_by_user_and_file_id(user_id, file_id)
        if not row:
            raise HTTPException(404, "File not found")

        # only the fields that were actually sent (even if null)
        for field in patch.__fields_set__:
            setattr(row, field, getattr(patch, field))

        self.session.add(row)
        self.session.commit()

    # def update_processing_status(
    #         self,
    #         user_id: int,
    #         file_id: int,
    #         process_status: str = None,
    #         percentage: int = None,
    #         started_at: datetime = None,
    #         completed_at: datetime = None,
    #         remaining_time: int = None
    # ):
    #     selected_file_row = self.get_file_by_user_and_file_id(user_id, file_id)
      

    #     if selected_file_row:
    #         if process_status is not None:
    #             selected_file_row.process_status = process_status
    #         if percentage is not None:
    #             selected_file_row.process_status_in_percentage = percentage
    #         if started_at is not None:
    #             selected_file_row.process_started_at = started_at
    #         if completed_at is not None:
    #             selected_file_row.process_completed_at = completed_at
    #         if remaining_time is not None:
    #             selected_file_row.remaining_time_estimation = remaining_time

    #         self.session.add(selected_file_row)
    #         self.session.commit()
    #         logger.info(f"Updated processing status for file_id {file_id} to {process_status}")
    #         logger.debug(f"Process status for file_id {file_id}: {selected_file_row.process_status}")
    #     else:
    #         logger.error(f"File with id {file_id} for user {user_id} not found")
    #         raise HTTPException(status_code=404, detail="File not found")

    def list_files(self, user_id: int):
        files = self.session.query(InitialData).filter(InitialData.user_id == user_id).all()
        return files

    def list_files_pagination(self, user_id: int, offset: int = 0, limit: int = 10, bank_name: str = None):
        # Build the base query
        if offset is None:
            offset= 0
        if offset < 0:
            offset = 0
        if limit <= 0:
            limit = 1  # Set a default limit if invalid

        query = self.session.query(InitialData).filter(InitialData.user_id == user_id)

        # Apply bank_name filter if provided
        if bank_name:
            query = query.filter(InitialData.associated_with == bank_name)

        # Get the total count before applying pagination
        total = query.count()

        # Apply ordering, offset, and limit for pagination
        files = query.order_by(InitialData.upload_timestamp.desc()).offset(offset).limit(limit).all()

        return files, total

    # def list_files_pagination(self, user_id: int, offset: int = 0, limit: int = 10):
    #     # Validate offset and limit
    #     if offset < 0:
    #         offset = 0
    #     if limit <= 0:
    #         limit = 10  # Set a default limit if invalid
    #
    #     # Query to get total count
    #     total = self.session.query(InitialData).filter(InitialData.user_id == user_id).count()
    #
    #     # Query to get paginated files
    #     files_query = (
    #         self.session.query(InitialData)
    #         .filter(InitialData.user_id == user_id)
    #         .order_by(InitialData.upload_timestamp.desc())
    #         .offset(offset)
    #         .limit(limit)
    #     )
    #     files = files_query.all()
    #
    #     return files, total

    def save_statements_df_to_db(
            self,
            user_id: int,
            start_date_str: str,
            end_date_str: str,
            num_records: int,
            records_df_serialized: str,
            exchange_rate_repository: ExchangeRateRepository
    ):
        last_entry = self.session.query(InitialData).filter_by(user_id=user_id).order_by(
            InitialData.document_id.desc()).first()

        if last_entry:
            last_entry.end_date = end_date_str
            last_entry.start_date = start_date_str
            last_entry.number_of_records = num_records
            last_entry.records_df = records_df_serialized

            self.session.add(last_entry)
            self.session.commit()
            logger.debug("Extracted dataframe is being transferred to processed data table")

            # Transfer data to processed table
            self.transfer_df_to_processed_table(
                document_id=last_entry.document_id,
                exchange_rate_repository=exchange_rate_repository,
                remove_duplicate_records=True
            )
        else:
            logger.error("No initial data entry found to save statements")
            raise HTTPException(status_code=404, detail="No initial data entry found")

    def exchange_rates_to_amounts(self, amount, exchange_rates, amount_is_usd=False):
        rate_to_usd = exchange_rates['rate_to_usd']
        usd_to_gold_rate = exchange_rates['usd_to_gold_rate']
        usd_to_chf_rate = exchange_rates['usd_to_chf_rate']

        amount_in_dollar = amount / rate_to_usd  # Converting to USD
        amount_in_gold = amount / (rate_to_usd * (1 / usd_to_gold_rate))  # Converting to Gold

        amount_in_chf = (amount / rate_to_usd) / usd_to_chf_rate

        return amount_in_dollar, amount_in_gold, amount_in_chf

    def is_duplicate_record(self, user_id: int, record_date_str: str, record_amount: float, record_text: str,
                            current_file_id: int) -> bool:
        """
        Check if there is an existing processed record that matches the given fields.
        Exclude records with the same file_id (as they're the same file).
        """
        # logger.debug(f"record_date_str: {record_date_str}")
        record_date = datetime.strptime(record_date_str, "%Y-%m-%d")

        # logger.debug(f"record_date_str: {record_date_str}")
        existing_record = self.session.query(ProcessedData).filter(
            ProcessedData.user_id == user_id,
            ProcessedData.record_date == record_date,
            ProcessedData.amount == record_amount,
            ProcessedData.text == record_text,
            ProcessedData.document_id != current_file_id
        ).first()

        return existing_record is not None

    def transfer_df_to_processed_table(self,
                                       document_id: int,
                                       exchange_rate_repository: ExchangeRateRepository,
                                       remove_duplicate_records: bool = False):
        initial_data_record = self.session.query(InitialData).filter(InitialData.document_id == document_id).first()
        if not initial_data_record:
            raise ValueError(f"No InitialData record found for document_id {document_id}")

        # Initialize a counter for duplicate records
        self.number_of_duplicate_records = 0

        records_df = pd.read_json(StringIO(initial_data_record.records_df))

        for _, row in records_df.iterrows():
            raw_row_values = row.to_dict()

            user_id = initial_data_record.user_id
            record_date_obj = raw_row_values.get('date')
            record_text = raw_row_values.get('text', '')
            record_amount = raw_row_values.get('amount', 0)
            record_currency = raw_row_values.get('currency', '')

            # Ensure record_date_obj is a datetime
            if isinstance(record_date_obj, str):
                record_date_obj = datetime.strptime(record_date_obj, "%Y-%m-%d")

            record_date_str = record_date_obj.strftime("%Y-%m-%d")
            # Validate the date format to ensure it's in YYYY-MM-DD
            try:
                datetime.strptime(record_date_str, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid date format for record: {record_date_str}. Expected format: YYYY-MM-DD")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid date format: {record_date_str}. Expected format: YYYY-MM-DD"
                )

            #logger.debug("Now exchange rates will be added to each record")

            # Use the provided exchange_rate_repository
            exchange_rates = exchange_rate_repository.get_or_update_exchange_rate(record_date_str, record_currency)
            #logger.debug(f"exchange_rates: {exchange_rates}")
            amount_in_dollar, amount_in_gold, amount_in_chf = self.exchange_rates_to_amounts(record_amount,
                                                                                             exchange_rates,
                                                                                             amount_is_usd=False)

            is_duplicate_record_flag = False
            if remove_duplicate_records:
                # Check if the record is a duplicate
                is_duplicate_record_flag = self.is_duplicate_record(user_id, record_date_str, record_amount,
                                                                    record_text, initial_data_record.document_id)
                if is_duplicate_record_flag:
                    logger.debug(
                        f"Marking duplicate record: user_id={user_id}, date={record_date_str}, amount={record_amount}, text={record_text}"
                    )
                    self.number_of_duplicate_records += 1

            processed_data_record = ProcessedData(
                user_id=initial_data_record.user_id,
                document_id=initial_data_record.document_id,
                text=record_text,
                cleaned_text=raw_row_values.get('cleaned_text', ''),
                keyword=raw_row_values.get('keyword', ''),
                amount=record_amount,
                amount_in_dollar=amount_in_dollar,
                amount_in_gold=amount_in_gold,
                amount_in_chf=amount_in_chf,
                currency=record_currency,
                record_date=record_date_obj,
                associated_with=initial_data_record.associated_with,
                # Mark the record as duplicate if needed
                is_duplicate=is_duplicate_record_flag
            )
            self.session.add(processed_data_record)

        self.session.commit()
        logger.info(f"ProcessedData table updated successfully for document_id {document_id}")

        # Log the count of duplicate records if duplicates were checked
        if remove_duplicate_records:
            logger.info(f"Number of duplicate records marked: {self.number_of_duplicate_records}")
