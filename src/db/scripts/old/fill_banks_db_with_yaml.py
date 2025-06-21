
# this is  db.scripts.fill_banks_db_with_yaml

#  to run this i  do python -m db.scripts.fill_banks_db_with_yaml


from datetime import datetime
import json
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models.bank_db_models import Bank, Base


def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def update_banks_from_yaml(file_path, Session):
    # Load the YAML data
    banks_data = load_yaml(file_path)

    session = Session()
    try:
        # Iterate over the countries and their banks
        for country_code, banks in banks_data.get('banks', {}).items():
            for bank in banks:
                # Normalize popularity
                popularity = bank.get('popularity', 5)
                popularity = max(1, min(10, popularity))  # Ensure it's between 1 and 10

                # Check if the bank already exists in the database by name and country
                existing_bank = session.query(Bank).filter_by(name=bank['name'], base_country=country_code).first()

                if existing_bank:
                    # Update the existing bank record
                    existing_bank.supported = bank.get('supported', existing_bank.supported)
                    existing_bank.soon_supported = bank.get('soon_supported', existing_bank.soon_supported)
                    existing_bank.support_note = bank.get('support_note', existing_bank.support_note)
                    existing_bank.logo = bank.get('logo', existing_bank.logo)
                    existing_bank.illustration = bank.get('illustration', existing_bank.illustration)
                    existing_bank.popularity = popularity
                    existing_bank.updated_at = datetime.utcnow()

                    # Update aliases if changed
                    new_aliases = bank.get('aliases', [])
                    if new_aliases != existing_bank.get_aliases():
                        existing_bank.set_aliases(new_aliases)

                    # Update supported file formats if changed
                    new_formats = bank.get('supported_file_formats', [])
                    if new_formats != existing_bank.get_supported_file_formats():
                        existing_bank.set_supported_file_formats(new_formats)

                    # Update available currencies if changed
                    new_currencies = bank.get('available_currencies', [])
                    if new_currencies != existing_bank.get_available_currencies():
                        existing_bank.set_available_currencies(new_currencies)
                else:
                    # Insert a new bank record
                    new_bank = Bank(
                        name=bank['name'],
                        string_id=bank['string_id'],
                        base_country=country_code,
                        supported=bank.get('supported', False),
                        soon_supported=bank.get('soon_supported', False),
                        support_note=bank.get('support_note', ''),
                        logo=bank.get('logo', ''),
                        illustration=bank.get('illustration', ''),
                        popularity=popularity,
                        updated_at=datetime.utcnow()
                    )
                    new_bank.set_aliases(bank.get('aliases', []))
                    new_bank.set_supported_file_formats(bank.get('supported_file_formats', []))
                    new_bank.set_available_currencies(bank.get('available_currencies', []))
                    session.add(new_bank)

        session.commit()
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


def main():
    # Database setup (replace with your actual database URI)
    engine = create_engine('sqlite:///db/data/banks_data.db')
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    # update_banks_from_yaml('assets/banks.yaml', Session)
    # update_banks_from_yaml('../../assets/config/banks.yaml', Session)
    update_banks_from_yaml('assets/config/banks.yaml', Session)


if __name__ == '__main__':
    main()