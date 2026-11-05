"""Backtest ETF performance with adjusted-close or explicit dividend reinvestment.

- total-return uses Yahoo Finance Adj Close; do not add dividends again.
- share-accounting buys fractional shares at the first close and reinvests
  dividends at the ex-date close (a documented approximation).
- Yahoo Finance historical OHLC is split-adjusted; do not apply split ratios
  to the share count again when using this price history.
"""
import argparse
import pandas as pd
from config import TICKERS
from database import initialize_database, connect


def load_data(ticker, start, end):
    sql = """
        SELECT p.date, p.close, p.adj_close, COALESCE(d.dividend, 0.0) AS dividend
        FROM daily_prices AS p
        LEFT JOIN dividends AS d ON d.ticker = p.ticker AND d.date = p.date
        WHERE p.ticker = ? AND p.date >= ? AND p.date <= ?
        ORDER BY p.date
    """
    with connect() as conn:
        df = pd.read_sql_query(sql, conn, params=(ticker, start, end))
    if df.empty:
        raise ValueError(f"No price data for {ticker} from {start} through {end}.")
    df["date"] = pd.to_datetime(df["date"])
    return df.dropna(subset=["close"]).reset_index(drop=True)


def total_return_backtest(df, initial_capital):
    result = df.dropna(subset=["adj_close"]).copy().reset_index(drop=True)
    if result.empty:
        raise ValueError("No adjusted-close data is available for this period.")
    base = float(result.loc[0, "adj_close"])
    if base <= 0:
        raise ValueError("Starting adjusted close must be positive.")
    result["portfolio_value"] = initial_capital * result["adj_close"].astype(float) / base
    return result


def share_accounting_backtest(df, initial_capital):
    """Reinvest each distribution at its ex-date close using fractional shares."""
    result = df.copy().reset_index(drop=True)
    start_close = float(result.loc[0, "close"])
    if start_close <= 0:
        raise ValueError("Starting closing price must be positive.")

    shares = initial_capital / start_close
    cumulative_dividends = 0.0
    values, share_counts, dividend_totals = [], [], []

    for i, row in result.iterrows():
        dividend_per_share = float(row["dividend"] or 0.0)
        # Yahoo's action date is treated as the ex-dividend date. We model
        # reinvestment at that day's close; actual broker DRIP timing may differ.
        if i > 0 and dividend_per_share > 0:
            cash_distribution = shares * dividend_per_share
            reinvestment_price = float(row["close"])
            shares += cash_distribution / reinvestment_price
            cumulative_dividends += cash_distribution

        share_counts.append(shares)
        values.append(shares * float(row["close"]))
        dividend_totals.append(cumulative_dividends)

    result["shares"] = share_counts
    result["reinvested_dividends"] = dividend_totals
    result["portfolio_value"] = values
    return result


def print_summary(result, initial_capital, mode):
    ending_value = float(result.iloc[-1]["portfolio_value"])
    total_return = ending_value / initial_capital - 1
    elapsed_days = max((result.iloc[-1]["date"] - result.iloc[0]["date"]).days, 1)
    years = elapsed_days / 365.25
    cagr = (ending_value / initial_capital) ** (1 / years) - 1

    print(f"Mode:              {mode}")
    print(f"Actual data range: {result.iloc[0]['date'].date()} to {result.iloc[-1]['date'].date()}")
    print(f"Initial capital:   ${initial_capital:,.2f}")
    print(f"Ending value:      ${ending_value:,.2f}")
    print(f"Total return:      {total_return:.2%}")
    print(f"Annualized return: {cagr:.2%}")
    if "shares" in result.columns:
        print(f"Ending shares:     {float(result.iloc[-1]['shares']):,.6f}")
        print(f"Dividends reinvested (modeled): ${float(result.iloc[-1]['reinvested_dividends']):,.2f}")


def main():
    parser = argparse.ArgumentParser(description="ETF backtest with dividend reinvestment.")
    parser.add_argument("ticker", choices=TICKERS)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--initial-capital", type=float, default=10000.0)
    parser.add_argument("--mode", choices=("total-return", "share-accounting"), default="total-return")
    parser.add_argument("--csv", help="Optional CSV path for daily results")
    args = parser.parse_args()

    if args.initial_capital <= 0:
        parser.error("--initial-capital must be greater than zero")
    if args.start > args.end:
        parser.error("--start must be on or before --end")

    initialize_database()
    data = load_data(args.ticker, args.start, args.end)
    if args.mode == "total-return":
        result = total_return_backtest(data, args.initial_capital)
    else:
        result = share_accounting_backtest(data, args.initial_capital)

    print(f"\n{args.ticker} backtest")
    print_summary(result, args.initial_capital, args.mode)
    if args.csv:
        export = result.copy()
        export["date"] = export["date"].dt.strftime("%Y-%m-%d")
        export.to_csv(args.csv, index=False)
        print(f"Daily results exported to {args.csv}")


if __name__ == "__main__":
    main()
