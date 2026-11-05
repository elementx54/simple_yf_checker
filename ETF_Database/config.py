"""Project configuration."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "etf_prices.db"

TICKERS = ("UPRO", "VT", "AVGE", "DFAW")
MARKET_TIMEZONE = "America/New_York"
DAILY_OVERLAP_CALENDAR_DAYS = 10

# Names are intentionally left blank until verified from issuer documentation.
ETF_NAMES = {ticker: None for ticker in TICKERS}
