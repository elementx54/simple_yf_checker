"""Download and persist Yahoo Finance daily history for one ETF."""
import sqlite3
import pandas as pd
import yfinance as yf

from database import connect, start_log, finish_log

PRICE_COLUMNS = ("Open", "High", "Low", "Close")

def _date_string(index_value):
    # yfinance indexes are exchange-local dates. Preserve the displayed
    # exchange date; do not convert it to UTC before extracting the date.
    if hasattr(index_value, "date"):
        return index_value.date().isoformat()
    return pd.Timestamp(index_value).date().isoformat()

def _upsert_history(ticker, frame, update_type):
    added = 0
    updated = 0

    with connect() as conn:
        log_id = start_log(conn, ticker, update_type)
        try:
            if frame is None or frame.empty:
                raise ValueError("Yahoo Finance returned no history.")

            for required in PRICE_COLUMNS:
                if required not in frame.columns:
                    raise ValueError(f"Yahoo Finance response is missing {required!r}.")

            for idx, row in frame.iterrows():
                values = [row.get(col) for col in PRICE_COLUMNS]
                if any(pd.isna(value) for value in values):
                    continue

                date = _date_string(idx)
                exists = conn.execute(
                    "SELECT 1 FROM daily_prices WHERE ticker=? AND date=?",
                    (ticker, date),
                ).fetchone() is not None

                adj = row.get("Adj Close")
                adj_close = None if pd.isna(adj) else float(adj)
                volume_value = row.get("Volume")
                volume = None if pd.isna(volume_value) else int(volume_value)

                conn.execute(
                    """INSERT INTO daily_prices
                       (ticker, date, open, high, low, close, adj_close, volume)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(ticker, date) DO UPDATE SET
                         open=excluded.open,
                         high=excluded.high,
                         low=excluded.low,
                         close=excluded.close,
                         adj_close=excluded.adj_close,
                         volume=excluded.volume""",
                    (
                        ticker, date,
                        float(row["Open"]), float(row["High"]),
                        float(row["Low"]), float(row["Close"]),
                        adj_close, volume,
                    ),
                )
                if exists:
                    updated += 1
                else:
                    added += 1

            # Record corporate actions returned with the same history.
            if "Dividends" in frame.columns:
                for idx, value in frame["Dividends"].items():
                    if pd.notna(value) and float(value) != 0:
                        conn.execute(
                            """INSERT INTO dividends (ticker, date, dividend)
                               VALUES (?, ?, ?)
                               ON CONFLICT(ticker, date) DO UPDATE SET
                                 dividend=excluded.dividend""",
                            (ticker, _date_string(idx), float(value)),
                        )

            if "Stock Splits" in frame.columns:
                for idx, value in frame["Stock Splits"].items():
                    if pd.notna(value) and float(value) != 0:
                        conn.execute(
                            """INSERT INTO stock_splits (ticker, date, split_ratio)
                               VALUES (?, ?, ?)
                               ON CONFLICT(ticker, date) DO UPDATE SET
                                 split_ratio=excluded.split_ratio""",
                            (ticker, _date_string(idx), float(value)),
                        )

            finish_log(conn, log_id, "success", added, updated)
        except Exception as exc:
            # The context manager rolls back all data changes for this ETF.
            # Log failure in a separate transaction after rollback.
            conn.rollback()
            with connect() as log_conn:
                log_id = start_log(log_conn, ticker, update_type)
                finish_log(log_conn, log_id, "failed", error=str(exc))
            raise

    return added, updated

def download_and_store(ticker, update_type, start=None, end=None, period=None):
    """Fetch one ticker. end is exclusive, as required by yfinance."""
    kwargs = {
        "auto_adjust": False,
        "actions": True,
        "repair": False,
        "raise_errors": True,
    }
    if period:
        kwargs["period"] = period
    else:
        kwargs["start"] = start
        kwargs["end"] = end

    history = yf.Ticker(ticker).history(interval="1d", **kwargs)
    return _upsert_history(ticker, history, update_type)
