#!/usr/bin/env python
# insert_sample_dataset_to_db.py


# to run this    python -m db.scripts.insert_sample_dataset_to_db

import csv
import sys
import os
import logging
import calendar
from datetime import datetime, date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your models. Adjust the following import paths according to your project structure.
from db.models.data import InitialData, ProcessedData

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def random_date_in_month(year: int, month: int) -> date:
    """Generate a random date within a given month and year."""
    first_day = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    random_day = __import__('random').randint(1, last_day)
    return date(year, month, random_day)


def read_sample_csv(file_path: str) -> list:
    """Read sample records from CSV."""
    records = []
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            records.append(row)
    return records


def main():
    # Setup SQLAlchemy engine and session
    engine = create_engine('sqlite:///db/data/budget_tracker.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # --- READ CSV FILE ---
        
        #  python -m db.scripts.insert_sample_dataset_to_db
        csv_file_path = "db/scripts/sample_dataset.csv"  # Adjust the path as needed
        sample_records = read_sample_csv(csv_file_path)
        if not sample_records:
            logger.error("No records found in the CSV file.")
            sys.exit("No records found in the CSV file.")

        logger.debug(f"Read {len(sample_records)} records from CSV.")

        # --- ORDER RECORDS BY DATE ---
        from datetime import datetime
        sample_records = sorted(
            sample_records,
            key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
        )
        logger.debug("Records sorted by date.")

        # --- INSERT INITIAL DATA RECORD ---
        # Use the first and last record's date to determine the overall date range.
        start_date_str = sample_records[0]["date"]
        end_date_str = sample_records[-1]["date"]
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        # Create an InitialData object with the specified modifications:
        initial = InitialData(
            user_id=1,
            raw_data_format="csv",
            associated_with="sample_dataset",
            bank_id=99999,
            start_date=start_date_obj,
            end_date=end_date_obj,
            number_of_records=len(sample_records),
            number_of_duplicate_records=0,
            upload_timestamp=datetime.utcnow(),
            currency=sample_records[0]["currency"],
            country_code="US",
            bank_account_id=None,
            number_of_processed_records=len(sample_records),
            process_status="completed",
            process_status_in_percentage=100,
            process_started_at=datetime.utcnow(),
            process_completed_at=datetime.utcnow(),
            remaining_time_estimation=0,
            remaining_time_estimation_str="0",
            number_of_cantcategorized=None,
            this_is_a_virgin_bank=False,
            virgin_bank_status=None,
            user_proposed_bank_name=None,
            bank_account_alias=None
        )

        session.add(initial)
        session.commit()
        session.refresh(initial)
        document_id = initial.document_id
        logger.debug(f"Inserted InitialData record with document_id: {document_id}")

        # --- INSERT PROCESSED DATA RECORDS ---
        for row in sample_records:
            try:
                record_date_obj = datetime.strptime(row["date"], "%Y-%m-%d")
            except Exception as e:
                logger.error(f"Error parsing date '{row['date']}': {e}")
                continue

            processed = ProcessedData(
                user_id=1,
                document_id=document_id,
                text=row["desc"],
                cleaned_text=None,
                amount=float(row["amount"]),
                amount_in_dollar=float(row["amount"]),
                amount_in_gold=float(row["amount"]),
                amount_in_chf=float(row["amount"]),
                currency=row["currency"],
                keyword=None,
                rationale=None,
                refiner_output=None,
                categorization_result=None,
                category=row["cat"],
                subcategory=row["subcat"],
                categorized_by=None,
                loaded_from_keyword_cache=False,
                record_date=record_date_obj,
                associated_with="dummy_bank",
                processed_at=datetime.utcnow(),
                is_active=True,
                backup_category=None,
                backup_subcategory=None,
                parent_record_id=None,
                split_level=0,
                is_split=False,
                apply_to_similar_records=False,
                attached_file=None,
                attached_file_name=None,
                attached_file_type=None,
                matched_auto_trigger_keyword=None,
                matched_metapattern=None,
                tax_deductable=False,
                source_of_income=False,
                transfer_to_self=False,
                vetted_by_user=False,
                transfer_to_saving=False,
                bank_account_id=None
            )
            session.add(processed)

        session.commit()
        logger.info(f"Inserted {len(sample_records)} ProcessedData records for document_id {document_id}")
        print(f"Inserted InitialData with document_id: {document_id} and {len(sample_records)} processed records.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error inserting sample dataset: {e}", exc_info=True)
        sys.exit(f"Error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    main()
