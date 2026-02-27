import requests
from cachetools import TTLCache, cached
import logging

logger = logging.getLogger(__name__)

# Cache exchange rates for 12 hours (43200 seconds)
# NBU updates rates once a day.
rates_cache = TTLCache(maxsize=1, ttl=43200)

@cached(cache=rates_cache)
def get_nbu_rates() -> dict:
    """
    Fetches official exchange rates from the National Bank of Ukraine.
    Returns a dictionary of currency code to UAH rate.
    Example: {'USD': 41.5, 'EUR': 44.2}
    """
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rates = {}
        for item in data:
            if item.get('cc') in ['USD', 'EUR']:
                rates[item['cc']] = item['rate']
        
        if 'USD' not in rates:
            logger.warning("NBU API did not return USD rate. Using fallback.")
            rates['USD'] = 41.0
            
        if 'EUR' not in rates:
            logger.warning("NBU API did not return EUR rate. Using fallback.")
            rates['EUR'] = 44.0
            
        return rates
    except Exception as e:
        logger.error(f"Failed to fetch NBU rates: {e}")
        # Fallback rates in case NBU API is down
        return {'USD': 41.0, 'EUR': 44.0}


def convert_to_usd(price: float, currency: str) -> float:
    """
    Converts a given price in a given currency (UAH, EUR, USD) to USD
    using the latest official NBU exchange rates.
    """
    if not price or price <= 0:
        return 0.0
        
    currency = currency.upper().strip()
    if currency == 'USD':
        return float(price)
        
    rates = get_nbu_rates()
    usd_rate = rates['USD']
    
    if currency == 'UAH':
        return float(price / usd_rate)
    elif currency == 'EUR':
        # Convert EUR -> UAH -> USD
        eur_rate = rates['EUR']
        uah_value = price * eur_rate
        return float(uah_value / usd_rate)
    else:
        # Unknown currency, assume UAH fallback or just return as is
        logger.warning(f"Unknown currency '{currency}', assuming UAH for conversion fallback.")
        return float(price / usd_rate)
