"""Small command-line query/export utility."""
import argparse
import pandas as pd
from config import TICKERS
from database import initialize_database, connect

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", choices=TICKERS)
    parser.add_argument("--start", help="YYYY-MM-DD")
    parser.add_argument("--end", help="YYYY-MM-DD, inclusive")
    parser.add_argument("--csv", help="Optional CSV output filename")
    args = parser.parse_args()

    initialize_database()
    sql = """SELECT date, open, high, low, close, adj_close, volume
             FROM daily_prices WHERE ticker=?"""
    params = [args.ticker]

    if args.start:
        sql += " AND date >= ?"
        params.append(args.start)
    if args.end:
        sql += " AND date <= ?"
        params.append(args.end)
    sql += " ORDER BY date"

    with connect() as conn:
        df = pd.read_sql_query(sql, conn, params=params)

    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"Exported {len(df)} rows to {args.csv}")
    else:
        print(df.to_string(index=False))
        print(f"\nRows: {len(df)}")

if __name__ == "__main__":
    main()
