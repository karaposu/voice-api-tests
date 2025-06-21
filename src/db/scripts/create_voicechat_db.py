# create_voicechat_db.py


#  python -m db.scripts.create_voicechat_db
from sqlalchemy import create_engine
from db.models import Base  # This imports all models via models/__init__.py
import os

def main():
    # Create the SQLite engine (you can change the URI as needed)
    base_dir = os.path.dirname(__file__)
    main_db_path = os.path.join(base_dir, "..",  "data", "voicechat.db")

    main_db_path = os.path.abspath(main_db_path)
    
    # Create database URLs
    main_db_url = f"sqlite:///{main_db_path}"

    engine = create_engine(main_db_url, echo=True)

    # Create all tables in the database
    Base.metadata.create_all(engine)

    print("Database schema created successfully.")

if __name__ == "__main__":
    main()
