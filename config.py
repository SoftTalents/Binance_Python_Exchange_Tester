import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Exchange API keys (loaded from .env file)
MEXC_API_KEY = os.getenv('MEXC_API_KEY', '')
MEXC_API_SECRET = os.getenv('MEXC_API_SECRET', '')

KUCOIN_API_KEY = os.getenv('KUCOIN_API_KEY', '')
KUCOIN_API_SECRET = os.getenv('KUCOIN_API_SECRET', '')
KUCOIN_API_PASSPHRASE = os.getenv('KUCOIN_API_PASSPHRASE', '')
KUCOIN_API_PASSWORD = os.getenv('KUCOIN_API_PASSWORD', '')  # For KuCoin's 2FA

HTX_API_KEY = os.getenv('HTX_API_KEY', '')
HTX_API_SECRET = os.getenv('HTX_API_SECRET', '')

GATE_API_KEY = os.getenv('GATE_API_KEY', '')
GATE_API_SECRET = os.getenv('GATE_API_SECRET', '')

BITMART_API_KEY = os.getenv('BITMART_API_KEY', '')
BITMART_API_SECRET = os.getenv('BITMART_API_SECRET', '')
BITMART_MEMO = os.getenv('BITMART_MEMO', '')  # Some call it 'memo' or 'password'

BITGET_API_KEY = os.getenv('BITGET_API_KEY', '')
BITGET_API_SECRET = os.getenv('BITGET_API_SECRET', '')
BITGET_API_PASSPHRASE = os.getenv('BITGET_API_PASSPHRASE', '')

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# List of supported exchanges
SUPPORTED_EXCHANGES = [
    'mexc',
    'kucoin',
    'htx',  # Formerly Huobi
    'gateio',
    'bitmart',
    'bitget',
    'bybit'
]

# Default quote currency
QUOTE_CURRENCY = 'USDT'