import asyncio
import logging
import json
from typing import List, Dict, Any
from bot.services.data_service import get_historical_data, get_us_stock_universe
from bot.services.pattern_engine import detect_pattern, detect_all_patterns, PATTERNS
from bot.database.db import save_scan_result

logger = logging.getLogger(__name__)


async def scan_for_pattern(pattern: str, max_stocks: int = 50) -> List[Dict[str, Any]]:
    """Scan US stock universe for a specific pattern."""
    universe = await get_us_stock_universe()
    results = []

    batch_size = 10
    for i in range(0, min(len(universe), max_stocks), batch_size):
        batch = universe[i: i + batch_size]
        batch_results = await asyncio.gather(
            *[_check_stock_pattern(ticker, pattern) for ticker in batch],
            return_exceptions=True,
        )
        for result in batch_results:
            if isinstance(result, dict) and result.get("detected"):
                results.append(result)
        await asyncio.sleep(0.5)

    results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return results[:10]


async def _check_stock_pattern(ticker: str, pattern: str) -> Dict[str, Any]:
    """Check a single stock for a pattern."""
    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, lambda: get_historical_data(ticker, period="3mo", interval="1d")
        )

        if df.empty or len(df) < 20:
            return {"detected": False}

        result = detect_pattern(pattern, df)
        if result.get("detected"):
            result["ticker"] = ticker
            result["price"] = float(df["Close"].iloc[-1])
            try:
                await save_scan_result(
                    pattern=result.get("pattern", pattern),
                    ticker=ticker,
                    confidence=result.get("confidence", 0),
                    details=json.dumps(
                        {k: v for k, v in result.items() if k not in ["detected", "ticker"]}
                    ),
                )
            except Exception:
                pass
        return result
    except Exception as e:
        logger.debug(f"Error checking {ticker} for {pattern}: {e}")
        return {"detected": False}


async def run_scheduled_scan(context):
    """Scheduled job to scan for common patterns."""
    logger.info("Running scheduled stock scan...")
    patterns_to_scan = ["breakout", "unusual_volume", "ascending_triangle"]
    for pattern in patterns_to_scan:
        try:
            results = await scan_for_pattern(pattern, max_stocks=30)
            logger.info(f"Scheduled scan for {pattern}: found {len(results)} matches")
        except Exception as e:
            logger.error(f"Error in scheduled scan for {pattern}: {e}")
