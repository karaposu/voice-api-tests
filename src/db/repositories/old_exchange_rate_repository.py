# repositories/exchange_rate_repository.py

from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
import logging
import requests

from db.models.exchange_db_definition import HistoricalCurrencyRates

logger = logging.getLogger(__name__)

class ExchangeRateRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_update_exchange_rate(self, date: str, currency: str) -> dict:
        exchange_rate_record = self.session.query(HistoricalCurrencyRates).filter_by(
            date=date,
            currency=currency
        ).first()
        # logger.debug("exchange_rate_record.... ")

        date_obj = datetime.strptime(date, "%Y-%m-%d").date()

        if exchange_rate_record:
            # Return rates from the database
            return {
                'rate_to_usd': exchange_rate_record.rate_to_usd,
                'usd_to_gold_rate': exchange_rate_record.usd_to_gold_rate,
                'usd_to_chf_rate': exchange_rate_record.usd_to_chf_rate
            }
        else:
            # Fetch from the API and store in the database
            fetched_rates = self.fetch_exchange_rates_from_api(date, currency)
            new_exchange_rate = HistoricalCurrencyRates(
                date=date_obj,
                currency=currency,
                rate_to_usd=fetched_rates['rate_to_usd'],
                usd_to_gold_rate=fetched_rates['usd_to_gold_rate'],
                usd_to_chf_rate=fetched_rates['usd_to_chf_rate']
            )
            self.session.add(new_exchange_rate)
            self.session.commit()

            return fetched_rates

    def fetch_exchange_rates_from_api(self, date: str, currency: str) -> dict:
        api_key = "f76057debb5215fbad5bc6b3e72ea349"  # Replace with your actual API key
        url = "http://apilayer.net/api/historical"
        params = {
            "access_key": api_key,
            "date": date,
            "format": 2
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                logger.error(f"API error: {data.get('error')}")
                raise HTTPException(status_code=500, detail="Failed to fetch exchange rates from API")

            if 'quotes' not in data:
                logger.error("quotes not found")
                logger.error(f"Missing 'quotes' in the API response for date: {date} and currency: {currency}")
                return {
                    'rate_to_usd': None,
                    'usd_to_gold_rate': None,
                    'usd_to_chf_rate': None
                }

            else:

                quotes = data.get('quotes', {})
                rate_to_usd = quotes.get(f'USD{currency.upper()}')
                usd_to_chf_rate = quotes.get('USDCHF')
                usd_to_gold_rate = quotes.get('USDXAU')

            # if rate_to_usd is None:
            #     logger.error(f"Exchange rate for USD to {currency.upper()} not found.")
            #     raise HTTPException(status_code=500, detail="Exchange rate not found in API response")

            return {
                'rate_to_usd': rate_to_usd,
                'usd_to_gold_rate': usd_to_gold_rate,
                'usd_to_chf_rate': usd_to_chf_rate
            }

        else:
            logger.error(f"Failed to fetch exchange rates from API. Status code: {response.status_code}")
            raise HTTPException(status_code=500, detail="Failed to fetch exchange rates from API")
