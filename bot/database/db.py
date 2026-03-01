import aiosqlite
import os
import logging

logger = logging.getLogger(__name__)
DB_PATH = os.getenv("DATABASE_PATH", "./bot.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_cache (
                ticker TEXT NOT NULL,
                interval TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL, volume INTEGER,
                PRIMARY KEY (ticker, interval, timestamp)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                ticker TEXT NOT NULL,
                confidence REAL,
                details TEXT,
                scanned_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS options_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                contract TEXT,
                strike REAL,
                expiry TEXT,
                type TEXT,
                premium REAL,
                volume INTEGER,
                open_interest INTEGER,
                iv REAL,
                flow_type TEXT,
                recorded_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                chat_id INTEGER PRIMARY KEY,
                default_timeframe TEXT DEFAULT '1d',
                scan_notifications INTEGER DEFAULT 1
            )
        """)
        await db.commit()
    logger.info("Database tables initialized")


async def save_scan_result(pattern: str, ticker: str, confidence: float, details: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scan_results (pattern, ticker, confidence, details) VALUES (?, ?, ?, ?)",
            (pattern, ticker, confidence, details),
        )
        await db.commit()


async def get_alerts(ticker: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if ticker:
            cursor = await db.execute(
                "SELECT * FROM alerts WHERE ticker=? AND active=1", (ticker,)
            )
        else:
            cursor = await db.execute("SELECT * FROM alerts WHERE active=1")
        return await cursor.fetchall()


async def add_alert(chat_id: int, ticker: str, alert_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO alerts (chat_id, ticker, alert_type) VALUES (?, ?, ?)",
            (chat_id, ticker, alert_type),
        )
        await db.commit()


async def deactivate_alert(alert_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE alerts SET active=0 WHERE id=?", (alert_id,))
        await db.commit()
