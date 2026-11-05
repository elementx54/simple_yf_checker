"""Daily 10-calendar-day update or full quarterly refresh."""
import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import TICKERS, MARKET_TIMEZONE, DAILY_OVERLAP_CALENDAR_DAYS
from database import initialize_database
from market_data import download_and_store

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("daily", "quarterly"),
        default="daily",
        help="daily = overlapping recent window; quarterly = maximum history",
    )
    args = parser.parse_args()

    initialize_database()
    failures = []

    if args.mode == "quarterly":
        for ticker in TICKERS:
            try:
                added, updated = download_and_store(
                    ticker=ticker,
                    update_type="quarterly",
                    period="max",
                )
                print(f"{ticker}: {added} inserted, {updated} updated.")
            except Exception as exc:
                failures.append((ticker, str(exc)))
                print(f"{ticker}: FAILED: {exc}")
    else:
        today_market = datetime.now(ZoneInfo(MARKET_TIMEZONE)).date()
        start = today_market - timedelta(days=DAILY_OVERLAP_CALENDAR_DAYS)
        end = today_market + timedelta(days=1)  # yfinance end date is exclusive

        for ticker in TICKERS:
            try:
                added, updated = download_and_store(
                    ticker=ticker,
                    update_type="daily",
                    start=start.isoformat(),
                    end=end.isoformat(),
                )
                print(f"{ticker}: {added} inserted, {updated} updated.")
            except Exception as exc:
                failures.append((ticker, str(exc)))
                print(f"{ticker}: FAILED: {exc}")

    if failures:
        raise SystemExit(f"{len(failures)} ETF update(s) failed.")

if __name__ == "__main__":
    main()
