import yfinance as yf
import pandas as pd
import numpy as np
import logging
import os
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")


async def get_stock_info(ticker: str) -> Dict[str, Any]:
    """Get comprehensive stock information."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="2d", interval="1d")

        if hist.empty:
            return {"error": f"No data found for {ticker}"}

        current_price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        change_pct = ((current_price - prev_close) / prev_close) * 100

        volume = int(hist["Volume"].iloc[-1]) if not hist["Volume"].empty else 0

        return {
            "ticker": ticker.upper(),
            "price": current_price,
            "change_pct": change_pct,
            "volume": volume,
            "market_cap": info.get("marketCap", 0),
            "float_shares": info.get("floatShares", 0),
            "short_interest": info.get("shortPercentOfFloat", 0),
            "avg_volume": info.get("averageVolume", 0),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "beta": info.get("beta", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "analyst_rating": info.get("recommendationKey", "N/A"),
        }
    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {e}")
        return {"error": str(e)}


def get_historical_data(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Get historical OHLCV data."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        logger.error(f"Error fetching historical data for {ticker}: {e}")
        return pd.DataFrame()


def get_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate technical indicators from OHLCV data."""
    if df.empty or len(df) < 20:
        return {}

    try:
        import pandas_ta as ta

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # RSI
        rsi = ta.rsi(close, length=14)
        rsi_val = float(rsi.iloc[-1]) if rsi is not None and not rsi.empty else None

        # MACD
        macd_df = ta.macd(close)
        macd_val = float(macd_df["MACD_12_26_9"].iloc[-1]) if macd_df is not None and not macd_df.empty else None
        macd_signal = float(macd_df["MACDs_12_26_9"].iloc[-1]) if macd_df is not None and not macd_df.empty else None
        macd_hist = float(macd_df["MACDh_12_26_9"].iloc[-1]) if macd_df is not None and not macd_df.empty else None

        # VWAP (rolling cumulative)
        typical_price = (high + low + close) / 3
        vwap_val = float((typical_price * volume).sum() / volume.sum()) if volume.sum() > 0 else None

        # Moving averages
        sma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
        sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
        sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

        # ATR
        atr = ta.atr(high, low, close, length=14)
        atr_val = float(atr.iloc[-1]) if atr is not None and not atr.empty else None

        # Bollinger Bands
        bb = ta.bbands(close, length=20)
        bb_upper = float(bb["BBU_20_2.0"].iloc[-1]) if bb is not None and not bb.empty else None
        bb_lower = float(bb["BBL_20_2.0"].iloc[-1]) if bb is not None and not bb.empty else None

        # Volume indicators
        vol_sma20 = float(volume.rolling(20).mean().iloc[-1]) if len(volume) >= 20 else None
        vol_ratio = float(volume.iloc[-1] / vol_sma20) if vol_sma20 and vol_sma20 > 0 else None

        # Trend determination
        current_price = float(close.iloc[-1])
        short_trend = "bullish" if sma20 and current_price > sma20 else "bearish"
        mid_trend = "bullish" if sma50 and current_price > sma50 else "bearish"
        long_trend = "bullish" if sma200 and current_price > sma200 else "bearish"

        # Support/Resistance (simple pivot points)
        pivot = float((high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3)
        resistance1 = 2 * pivot - float(low.iloc[-1])
        support1 = 2 * pivot - float(high.iloc[-1])

        return {
            "rsi": rsi_val,
            "macd": macd_val,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "vwap": vwap_val,
            "sma20": sma20,
            "sma50": sma50,
            "sma200": sma200,
            "atr": atr_val,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "vol_ratio": vol_ratio,
            "short_trend": short_trend,
            "mid_trend": mid_trend,
            "long_trend": long_trend,
            "support1": support1,
            "resistance1": resistance1,
            "pivot": pivot,
        }
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return {}


async def get_us_stock_universe() -> list:
    """Return a curated list of liquid US-listed stock tickers for scanning."""
    major_stocks = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
        "LLY", "JPM", "V", "UNH", "XOM", "MA", "JNJ", "PG", "HD", "MRK",
        "CVX", "ABBV", "KO", "PEP", "COST", "WMT", "BAC", "MCD", "ACN",
        "ORCL", "CRM", "AMD", "NFLX", "ADBE", "TXN", "INTC", "QCOM", "IBM",
        "NOW", "AMAT", "LRCX", "KLAC", "MRVL", "PANW", "CRWD", "FTNT",
        "SPY", "QQQ", "IWM", "DIA",
        "GS", "MS", "WFC", "C", "AXP", "BLK", "SCHW", "USB",
        "UNP", "UPS", "FDX", "DAL", "UAL", "AAL", "LUV",
        "BA", "GE", "CAT", "DE", "HON", "MMM", "RTX", "LMT",
        "PFE", "BMY", "AMGN", "GILD", "BIIB", "MRNA", "BNTX",
        "DIS", "CMCSA", "T", "VZ", "SPOT",
        "AMT", "PLD", "O", "SPG", "WELL",
        "FCX", "NEM", "GOLD", "CLF", "X",
        "UBER", "LYFT", "ABNB", "DASH",
        "COIN", "MSTR", "MARA", "RIOT",
        "SHOP", "SQ", "PYPL", "AFRM",
        "PLTR", "SOFI", "HOOD",
        "MU", "WDC", "STX",
        "ZM", "DOCN", "NET", "DDOG", "SNOW", "PATH",
    ]
    return list(set(major_stocks))
