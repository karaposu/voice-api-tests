# db/repositories/bank_information_repository.py

from sqlalchemy.orm import Session
import logging
import json

# from db.models.info_db_definitions import BankInformation
from db.models.bank_db_models import Bank

logger = logging.getLogger(__name__)

class BankInformationRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_bank_with_bank_id(self, bank_id: int) -> str:
        bank = self.session.query(Bank).filter(Bank.id == bank_id).first()
        if bank:
            return bank.string_id, bank.works_only_with_auto_parser
        else:
            return None, True  # Or raise an exception if the bank is not found

    def get_bank_information(self, country: str = None, supported: bool = None) -> list:
        query = self.session.query(Bank)

        from sqlalchemy import func

        if country:
            query = query.filter(func.lower(Bank.base_country) == country.lower())

        if supported is not None:
            query = query.filter(Bank.supported == supported)

        results = query.all()

        banks = []



        for bank in results:
            banks.append({
                'id': bank.id,
                'name': bank.name,
                'string_id': bank.string_id,
                'support_note': bank.support_note,
                'base_country': bank.base_country,
                'available_currencies': bank.available_currencies,
                'supported': bank.supported,
                'soon_supported': bank.soon_supported,
                'popularity': bank.popularity,
                'updated_at': bank.updated_at,
                'logo': bank.logo,
                'illustration': bank.illustration,
                'aliases': json.loads(bank.aliases) if bank.aliases else [],
                'is_international': bank.is_international,
                'supported_file_formats': json.loads(bank.supported_file_formats) if bank.supported_file_formats else [],
                # 'currency_code': bank.currency_code,


            })

        return banks
