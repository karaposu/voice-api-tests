# db/scripts/fill_budget_tracker_db.py

# to run this    python -m db.scripts.fill_budget_tracker_db

import pandas as pd
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.data import ProcessedData, InitialData
from db.models.user_details import UserSettings
from db.models.user import User
from werkzeug.security import generate_password_hash
from passlib.context import CryptContext
import os
# import logging
import logging
logging.getLogger('passlib').setLevel(logging.ERROR)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# logger.debug("Hashing password")



# Constants for JWT token creation
ALGORITHM = "HS256"
SECRET_KEY = os.getenv('SECRET_KEY')
# SECRET_KEY = "your_secret_key"  # Replace with your actual secret key
ACCESS_TOKEN_EXPIRE_MINUTES = 3000  # Set as per your requirement

# Function to generate a random date between two dates
def random_date(start, end):
    delta = end - start
    int_delta = delta.days
    random_day = random.randrange(int_delta + 1)  # include end date
    return start + timedelta(days=random_day)

def create_test_dataframe(num_rows ):
    # Define the categories and subcategories data
    categories_data = [
        {
            "category": "Food & Dining",
            "subcategories": ["Groceries", "Restaurants", "Coffee", "Takeout"]
        },
        {
            "category": "Utilities",
            "subcategories": ["Electricity and Water and Gas", "Internet and Mobile"]
        },
        {
            "category": "Accommodation",
            "subcategories": ["Accommodation"]
        },
        {
            "category": "Incoming P2P Transfers",
            "subcategories": ["Incoming Money"]
        },
        {
            "category": "Outgoing P2P Transfers",
            "subcategories": ["Outgoing Money"]
        },
        {
            "category": "Cash Withdrawal",
            "subcategories": ["Cash Withdrawal"]
        },
        {
            "category": "Cash Deposit",
            "subcategories": ["Cash Deposit"]
        },
        {
            "category": "Transportation",
            "subcategories": [
                "Fuel",
                "Taxi",
                "Travel Tickets",
                "Public Transportation",
                "Vehicle Maintenance",
                "Car Payments"
            ]
        },
        {
            "category": "Healthcare",
            "subcategories": ["Medical Bills", "Health Insurance", "Medications"]
        },
        {
            "category": "Retail Purchases",
            "subcategories": ["Clothes", "Technology Items", "Other"]
        },
        {
            "category": "Personal Care",
            "subcategories": ["Personal Grooming", "Fitness"]
        },
        {
            "category": "Leisure and Activities in Real Life",
            "subcategories": ["Movies", "Concerts"]
        },
        {
            "category": "Online Subscriptions & Services",
            "subcategories": [
                "Streaming & Digital Subscriptions",
                "Cloud Server Payments"
            ]
        }
    ]

    # Define the number of rows and date range
    # num_rows = 100  # You can change this number as needed
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 1)

    # Initialize lists to store the data
    document_ids = [1] * num_rows
    descriptions = ["test - Transaction from ABC AVM, 2024-xx-xx, 1002 TL "] * num_rows
    # amounts = [random.uniform(10, 10000) for _ in range(num_rows)]
    amounts = [random.randint(10, 1000) for _ in range(num_rows)]  # Generate integer amounts
    amounts_in_dollar = [amount / 3.33 for amount in amounts]  # Example conversion rate
    amounts_in_gold = [amount / 1000 for amount in amounts]  # Example conversion rate
    amounts_in_chf = [amount / 2.85 for amount in amounts]  # Example conversion rate
    currencies = ["TL"] * num_rows

    raw_amounts = [f"{amount:.2f} TL" for amount in amounts]
    associated_with_list = ["test"] * num_rows
    processed_ats = [datetime.now()] * num_rows
    is_actives = [True] * num_rows

    # Generate random data for record_date, category, and subcategory
    record_dates = [random_date(start_date, end_date) for _ in range(num_rows)]
    categories = []
    subcategories = []

    for _ in range(num_rows):
        category_dict = random.choice(categories_data)
        categories.append(category_dict["category"])
        subcategories.append(random.choice(category_dict["subcategories"]))

    # Create the DataFrame
    data = {
        "document_id": document_ids,
        "description": descriptions,
        "record_date": record_dates,
        "amount": amounts,
        "amount_in_dollar": amounts_in_dollar,
        "amount_in_gold": amounts_in_gold,
        "amount_in_chf": amounts_in_chf,
        "currency": currencies,
        "raw_amount": raw_amounts,
        "category": categories,
        "subcategory": subcategories,
        "associated_with": associated_with_list,
        "processed_at": processed_ats,
        "is_active": is_actives
    }

    df = pd.DataFrame(data)

    
    final_df = df.iloc[0:0].copy()

    # We will iterate over the df in chunks of 10 rows
    for start_idx in range(0, num_rows, 10):
        end_idx = start_idx + 10
        chunk = df.iloc[start_idx:end_idx]

        # If chunk is less than 10 rows (in case num_rows is not multiple of 10)
        if chunk.empty:
            continue

        # Random duplication factor between 2 and 5
        n = random.randint(2, 5)

        # Repeat the chunk n times and append to final_df
        repeated_chunk = pd.concat([chunk] * n, ignore_index=True)
        final_df = pd.concat([final_df, repeated_chunk], ignore_index=True)

    return final_df


   



def create_user_settings(session, user_id):
    """Create default user settings for the given user_id."""
    try:
        existing_settings = session.query(UserSettings).filter_by(user_id=user_id).first()
        if not existing_settings:
            settings = UserSettings(
                user_id=user_id,
                piechart_settings=None,
                notification_preferences=None,
                theme_preferences=None,
                default_currency='TRY',
                default_country='tr',
                default_bank='Test Bank'
            )
            session.add(settings)
            session.commit()
            print("User settings created successfully.")
        else:
            print("User settings for this user already exist.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred while creating user settings: {e}")


def create_test_user(session):
    """Create a test user with user_id=1."""
    try:
        # Check if user with user_id=1 already exists
        existing_user = session.query(User).filter_by(user_id=1).first()
        if not existing_user:
            user = User(
                user_id=1,
                name='Test User',
                email='e@hotmail.com',
                # password_hash=generate_password_hash('string'),
                password_hash=pwd_context.hash('string'),
                created_at=datetime.now(),
                is_verified=True,
                family_mode=False,
                plan_id=1  # Ensure that plan_id=1 exists in your 'plans' table
            )
            session.add(user)
            session.commit()
            print("User created successfully.")
        else:
            print("User with user_id=1 already exists.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred while creating the user: {e}")


def create_admin_user(session):
    """Create a test user with user_id=1."""
    try:
        # Check if user with user_id=1 already exists
        existing_user = session.query(User).filter_by(user_id=1).first()
        if not existing_user:
            user = User(
                user_id=2,
                name='Admin User',
                email='admin@budgety.ai',
                # password_hash=generate_password_hash('string'),
                password_hash=pwd_context.hash('string'),
                created_at=datetime.now(),
                is_verified=True,
                can_see_admin_panel=True,
                family_mode=False,
                plan_id=1  # Ensure that plan_id=1 exists in your 'plans' table
            )
            session.add(user)
            session.commit()
            print("User created successfully.")
        else:
            print("User with user_id=1 already exists.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred while creating the user: {e}")

def create_test_document(session, user_id,num_rows ):
    """Create a test InitialData entry with document_id=1."""
    try:
        # Check if InitialData with document_id=1 already exists
        existing_initial_data = session.query(InitialData).filter_by(document_id=1).first()
        if not existing_initial_data:

            fixed_start_date = datetime(2024, 1, 1).strftime('%Y-%m-%d')
            fixed_end_date = datetime(2024, 12, 1).strftime('%Y-%m-%d')


            current_date = datetime.now().date()  #
            initial_data_entry = InitialData(
                document_id=1,
                user_id=user_id,
                family_member_id=None,
                raw_data_format='json',  # Assuming 'json' as an example
                encoded_raw_data=None,
                binary_data=None,
                associated_with='test',
                bank_id=1,  # Ensure that bank_id=1 exists in your 'banks' table
                start_date=fixed_start_date,
                end_date=fixed_end_date,
                number_of_records=num_rows,
                number_of_duplicate_records=0,
                records_df=None,
                upload_timestamp=datetime.now(),
                currency='try',
                country_code='tr',
                bank_account_id=None,  # Adjust if necessary
                bank_account_alias=None,
                number_of_processed_records=num_rows,
                process_status='completed',
                process_status_in_percentage=100,
                process_started_at=None,
                process_completed_at=None,
                remaining_time_estimation=None,
                remaining_time_estimation_str=None,
                number_of_cantcategorized=None
            )
            session.add(initial_data_entry)
            session.commit()
            print("InitialData entry created successfully.")
        else:
            print("InitialData entry with document_id=1 already exists.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred while creating the InitialData entry: {e}")

def create_test_records(session, df, user_id):
    """Insert test ProcessedData records from the DataFrame."""
    # Insert ProcessedData entries
    for index, row in df.iterrows():
        try:
            new_record = ProcessedData(
                user_id=user_id,
                document_id=row['document_id'],
                text=row['description'],
                record_date=row['record_date'],
                amount=row['amount'],
                amount_in_dollar=row['amount_in_dollar'],
                amount_in_gold=row['amount_in_gold'],
                amount_in_chf=row['amount_in_chf'],
                currency=row['currency'],
                # raw_amount=row['raw_amount'],
                category=row['category'],
                subcategory=row['subcategory'],
                associated_with=row['associated_with'],
                processed_at=row['processed_at'],
                is_active=row['is_active']
            )
            session.add(new_record)
        except Exception as e:
            session.rollback()
            print(f"An error occurred at index {index}: {e}")

    # Commit the session after all records have been added
    try:
        session.commit()
        print("ProcessedData entries added successfully.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred during commit: {e}")

def main():
    # Database setup
    engine = create_engine('sqlite:///db/data/budget_tracker.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create test user
        create_test_user(session)
        create_admin_user(session)
        # num_rows = 100
        user_id = 1
        create_user_settings(session, user_id)
         
        # create_test_document(session, user_id,num_rows )

        # df = create_test_dataframe(num_rows)
        print("Test DataFrame created.")
        
        # Insert test records into ProcessedData
        # create_test_records(session, df, user_id)
        
        # ─────────────────────────────────────────────────────────────────────
        # VERIFICATION: PRINT ROW COUNT
        # ─────────────────────────────────────────────────────────────────────
        row_count = session.query(ProcessedData).count()
        print(f"Number of rows in ProcessedData: {row_count}")

        
        first_five = session.query(ProcessedData).limit(3).all()
        print("Here are 3 rows from ProcessedData:")
        for row in first_five:
            print(f"Record ID: {row.record_id}, Amount: {row.amount}, Category: {row.category}")
    
    finally:
        # Close the session
        session.close()

if __name__ == "__main__":
    main()
