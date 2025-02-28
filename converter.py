import requests
from datetime import datetime, timedelta

API_KEY = "3028551a2fd5c87440a51801"

# Function to fetch the exchange rate
def get_exchange_rate(from_currency, to_currency, api_key=API_KEY):
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_currency}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and 'conversion_rates' in data:
        return data['conversion_rates'].get(to_currency, None)
    else:
        raise ValueError("Error fetching exchange rates or invalid currency code.")

# Function to convert currency
def convert_currency(amount, from_currency, to_currency, api_key=API_KEY):
    rate = get_exchange_rate(from_currency, to_currency, api_key)
    if rate:
        return amount * rate
    else:
        raise ValueError("Conversion rate not found.")

# Function to fetch all available currencies with names
def get_all_currencies(api_key=API_KEY):
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/codes"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and 'supported_codes' in data:
        return {code[0]: code[1] for code in data['supported_codes']}
    else:
        raise ValueError("Error fetching currency codes.")


