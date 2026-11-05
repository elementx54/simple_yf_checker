#!/usr/bin/env python3
"""
Read the latest available ETF prices from the sibling ETF_Database project.

Expected folder layout:
    parent_folder/
        ETF_Database/
            etf_prices.db
        dip_person/
            get_latest_etf_prices.py

The script does not contact Yahoo Finance. It reads the newest stored trading
date for each tracked ETF directly from SQLite.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

TICKERS = ("UPRO", "VT", "AVGE", "DFAW")

# This script lives in dip_person; the database lives in the sibling
# ETF_Database folder.
DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "ETF_Database"
    / "etf_prices.db"
)


def get_latest_etf_prices(
    db_path: str | Path = DEFAULT_DB_PATH,
) -> dict[str, dict[str, Any]]:
    """
    Return the latest stored daily price row for each tracked ETF.

    Each ETF's latest date is selected independently. Missing ETFs are
    included with a None value so callers can detect incomplete database data.
    """
    db_path = Path(db_path).expanduser().resolve()

    if not db_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {db_path}\n"
            "Check that ETF_Database/etf_prices.db exists, or pass --db."
        )

    results: dict[str, dict[str, Any] | None] = {
        ticker: None for ticker in TICKERS
    }

    query = """
        SELECT p.ticker, p.date, p.open, p.close, p.adj_close
        FROM daily_prices AS p
        INNER JOIN (
            SELECT ticker, MAX(date) AS latest_date
            FROM daily_prices
            WHERE ticker IN (?, ?, ?, ?)
            GROUP BY ticker
        ) AS latest
            ON latest.ticker = p.ticker
           AND latest.latest_date = p.date
        ORDER BY p.ticker
    """

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, TICKERS).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(f"Could not read ETF prices from {db_path}: {exc}") from exc

    for row in rows:
        results[row["ticker"]] = {
            "date": row["date"],
            "open": row["open"],
            "close": row["close"],
            "adj_close": row["adj_close"],
        }

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read the latest stored ETF prices from etf_prices.db."
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"Path to the SQLite database (default: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()

    try:
        prices = get_latest_etf_prices(args.db)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # JSON output is convenient for another Python script to consume or
    # redirect to a file.
    print(json.dumps(prices, indent=2))

    missing = [ticker for ticker, values in prices.items() if values is None]
    if missing:
        print(
            f"\nWarning: no price rows found for: {', '.join(missing)}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
