"""SQLite schema and database helpers."""
import sqlite3
from datetime import datetime, timezone
from config import DB_PATH, TICKERS, ETF_NAMES

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS etfs (
    ticker TEXT PRIMARY KEY,
    name TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS daily_prices (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,                 -- Exchange trading date: YYYY-MM-DD
    open REAL NOT NULL CHECK (open > 0),
    high REAL NOT NULL CHECK (high > 0),
    low REAL NOT NULL CHECK (low > 0),
    close REAL NOT NULL CHECK (close > 0),
    adj_close REAL CHECK (adj_close IS NULL OR adj_close > 0),
    volume INTEGER CHECK (volume IS NULL OR volume >= 0),
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES etfs(ticker),
    CHECK (high >= low)
);

CREATE INDEX IF NOT EXISTS idx_daily_prices_date
    ON daily_prices(date);

CREATE TABLE IF NOT EXISTS dividends (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    dividend REAL NOT NULL CHECK (dividend >= 0),
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES etfs(ticker)
);

CREATE TABLE IF NOT EXISTS stock_splits (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    split_ratio REAL NOT NULL CHECK (split_ratio > 0),
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES etfs(ticker)
);

CREATE TABLE IF NOT EXISTS expense_ratio_history (
    ticker TEXT NOT NULL,
    effective_date TEXT NOT NULL,       -- YYYY-MM-DD; date rate became effective
    expense_ratio REAL NOT NULL CHECK (expense_ratio >= 0 AND expense_ratio < 1),
    source TEXT NOT NULL,               -- Prefer issuer prospectus/fact sheet URL or title
    recorded_at TEXT NOT NULL,
    PRIMARY KEY (ticker, effective_date),
    FOREIGN KEY (ticker) REFERENCES etfs(ticker)
);

CREATE TABLE IF NOT EXISTS update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    update_type TEXT NOT NULL CHECK (update_type IN ('initial', 'daily', 'quarterly')),
    attempted_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed')),
    records_added INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (ticker) REFERENCES etfs(ticker)
);
"""

def connect():
    """Open a connection with foreign-key enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database():
    with connect() as conn:
        conn.executescript(SCHEMA)
        for ticker in TICKERS:
            conn.execute(
                """INSERT INTO etfs (ticker, name, active)
                   VALUES (?, ?, 1)
                   ON CONFLICT(ticker) DO UPDATE SET
                       name = COALESCE(excluded.name, etfs.name)""",
                (ticker, ETF_NAMES.get(ticker)),
            )

def start_log(conn, ticker, update_type):
    attempted = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cur = conn.execute(
        """INSERT INTO update_log
           (ticker, update_type, attempted_at, status)
           VALUES (?, ?, ?, 'running')""",
        (ticker, update_type, attempted),
    )
    return cur.lastrowid

def finish_log(conn, log_id, status, added=0, updated=0, error=None):
    completed = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        """UPDATE update_log
           SET completed_at=?, status=?, records_added=?,
               records_updated=?, error_message=?
           WHERE id=?""",
        (completed, status, added, updated, error, log_id),
    )
