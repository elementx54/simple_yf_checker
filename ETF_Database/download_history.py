"""One-time initial population using maximum available history."""
from config import TICKERS
from database import initialize_database
from market_data import download_and_store

def main():
    initialize_database()
    failures = []

    for ticker in TICKERS:
        try:
            added, updated = download_and_store(
                ticker=ticker,
                update_type="initial",
                period="max",
            )
            print(f"{ticker}: {added} inserted, {updated} updated.")
        except Exception as exc:
            failures.append((ticker, str(exc)))
            print(f"{ticker}: FAILED: {exc}")

    if failures:
        raise SystemExit(f"{len(failures)} ETF download(s) failed.")

if __name__ == "__main__":
    main()
