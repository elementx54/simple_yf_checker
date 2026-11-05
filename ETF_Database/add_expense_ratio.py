"""Manually record a verified expense ratio and its effective date."""
import argparse
from datetime import datetime, timezone

from config import TICKERS
from database import initialize_database, connect

def main():
    parser = argparse.ArgumentParser(
        description="Record an expense ratio as a decimal (0.0020 = 0.20%)."
    )
    parser.add_argument("ticker", choices=TICKERS)
    parser.add_argument("effective_date", help="YYYY-MM-DD")
    parser.add_argument("expense_ratio", type=float, help="Decimal, not percent")
    parser.add_argument("source", help="Issuer document title or URL")
    args = parser.parse_args()

    initialize_database()
    recorded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with connect() as conn:
        conn.execute(
            """INSERT INTO expense_ratio_history
               (ticker, effective_date, expense_ratio, source, recorded_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(ticker, effective_date) DO UPDATE SET
                 expense_ratio=excluded.expense_ratio,
                 source=excluded.source,
                 recorded_at=excluded.recorded_at""",
            (
                args.ticker, args.effective_date, args.expense_ratio,
                args.source, recorded_at,
            ),
        )

    print(
        f"Saved {args.ticker}: {args.expense_ratio:.4%} "
        f"effective {args.effective_date}."
    )

if __name__ == "__main__":
    main()
