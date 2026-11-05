# ETF Database

_Disclaimer:_ I'm trying out the free ChatGPT to help me with this code.
But I am learning so I'm going slow and reading
and looking up the parts of the code I don't understand.

SQLite database for UPRO, VT, AVGE, and DFAW daily history.

## Contents

- `etfs`: tracked ETF symbols
- `daily_prices`: raw OHLC, adjusted close, and volume
- `dividends`: distributions reported by Yahoo Finance
- `stock_splits`: split events reported by Yahoo Finance
- `expense_ratio_history`: manually entered, historically effective expense ratios
- `update_log`: per-ETF update attempts and outcomes

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
pip install -r requirements.txt
```

## Initial historical download

```bash
python download_history.py
```

This creates `etf_prices.db` and downloads maximum available daily history for each ETF.

## Daily update

Run after the US market close:

```bash
python update_prices.py --mode daily
```

It requests a 10-calendar-day overlapping window. Weekends and market holidays naturally produce no rows.

## Quarterly full refresh

Run approximately once every three months:

```bash
python update_prices.py --mode quarterly
```

This re-downloads maximum available history and UPSERTs it. It does not delete existing records before the download.

## Expense ratios

Expense ratios are stored as decimals, not percentage numbers. For example, 0.20% is entered as `0.002`.

Use a verified effective date and source:

```bash
python add_expense_ratio.py VT 2026-02-01 0.0017 "Issuer prospectus URL or document title"
```

This is a manual process by design: yfinance does not provide a dependable historical time series of expense-ratio changes. Add a new row when a verified rate becomes effective; do not replace an older effective-date row.

## Query and CSV export

```bash
python query_prices.py UPRO
python query_prices.py VT --start 2020-01-01 --end 2025-12-31 --csv vt_prices.csv
```

## Backtesting notes

- Raw `open`, `high`, `low`, and `close` are unadjusted market prices.
- `adj_close` is Yahoo Finance's dividend/split-adjusted close series.
- Actual ETF price performance already reflects fund operating expenses. Do not subtract the expense ratio again when using actual ETF returns.
- For dividend-reinvestment total-return analysis, use adjusted close consistently, or explicitly model distributions and reinvestment. Do not add dividends to adjusted-close returns a second time.
- Market prices can differ from NAV and can trade at premiums or discounts.
- Yahoo Finance data is third-party data and may be revised or unavailable. Keep backups of the SQLite file.

## Important first-run validation

After the initial download, inspect row counts and date ranges for all four ETFs. Confirm that the newest daily bar is for a completed trading session before relying on it in a backtest. This starter project logs a successful Yahoo response, but does not independently certify that the response contains the final official closing bar.
