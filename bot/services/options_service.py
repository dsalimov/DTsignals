import yfinance as yf
import numpy as np
import pandas as pd
import logging
from scipy.stats import norm
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def black_scholes(
    S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call"
) -> Dict[str, float]:
    """Calculate Black-Scholes option price and Greeks."""
    if T <= 0 or sigma <= 0:
        return {"price": 0, "delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type.lower() == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = -norm.cdf(-d1)
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    theta = (
        -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        - r * K * np.exp(-r * T) * norm.cdf(d2 if option_type.lower() == "call" else -d2)
    ) / 365
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100

    return {
        "price": float(price),
        "delta": float(delta),
        "gamma": float(gamma),
        "theta": float(theta),
        "vega": float(vega),
        "rho": float(rho),
    }


def calculate_iv_rank(ticker: str) -> Dict[str, Any]:
    """Calculate IV Rank and IV Percentile using historical volatility."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y", interval="1d")

        if len(hist) < 30:
            return {"iv_rank": None, "iv_percentile": None, "hv30": None, "hv252": None}

        log_returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
        hv30 = float(log_returns.tail(30).std() * np.sqrt(252) * 100)
        hv252 = float(log_returns.std() * np.sqrt(252) * 100)

        options = stock.options
        if not options:
            return {"iv_rank": None, "iv_percentile": None, "hv30": hv30, "hv252": hv252}

        try:
            chain = stock.option_chain(options[0])
            calls = chain.calls
            puts = chain.puts

            current_price = float(hist["Close"].iloc[-1])

            atm_calls = calls.iloc[(calls["strike"] - current_price).abs().argsort()[:1]]
            atm_puts = puts.iloc[(puts["strike"] - current_price).abs().argsort()[:1]]

            iv_call = float(atm_calls["impliedVolatility"].iloc[0]) * 100 if not atm_calls.empty else None
            iv_put = float(atm_puts["impliedVolatility"].iloc[0]) * 100 if not atm_puts.empty else None

            current_iv = (
                (iv_call + iv_put) / 2
                if (iv_call and iv_put)
                else (iv_call or iv_put or hv30)
            )

            rolling_hv = log_returns.rolling(30).std() * np.sqrt(252) * 100
            hv_min = float(rolling_hv.min())
            hv_max = float(rolling_hv.max())
            hv_vals = rolling_hv.dropna().values

            iv_rank = (
                (current_iv - hv_min) / (hv_max - hv_min) * 100
                if (hv_max - hv_min) > 0
                else 50.0
            )
            pct_below = float(np.mean(hv_vals < current_iv) * 100) if len(hv_vals) > 0 else 50.0

            return {
                "current_iv": current_iv,
                "iv_rank": float(iv_rank),
                "iv_percentile": pct_below,
                "hv30": hv30,
                "hv252": hv252,
            }
        except Exception:
            return {"iv_rank": None, "iv_percentile": None, "hv30": hv30, "hv252": hv252}
    except Exception as e:
        logger.error(f"Error calculating IV rank for {ticker}: {e}")
        return {"iv_rank": None, "iv_percentile": None, "hv30": None, "hv252": None}


def get_options_chain_summary(ticker: str) -> Dict[str, Any]:
    """Get summarized options chain data."""
    try:
        stock = yf.Ticker(ticker)
        options_dates = stock.options

        if not options_dates:
            return {"error": "No options data available"}

        hist = stock.history(period="2d")
        current_price = float(hist["Close"].iloc[-1]) if not hist.empty else 0

        nearest_exp = options_dates[0]
        chain = stock.option_chain(nearest_exp)
        calls = chain.calls
        puts = chain.puts

        total_call_vol = int(calls["volume"].sum()) if "volume" in calls else 0
        total_put_vol = int(puts["volume"].sum()) if "volume" in puts else 0
        total_call_oi = int(calls["openInterest"].sum()) if "openInterest" in calls else 0
        total_put_oi = int(puts["openInterest"].sum()) if "openInterest" in puts else 0

        pc_ratio_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 0
        pc_ratio_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0

        top_call_vol = (
            calls.nlargest(3, "volume")[["strike", "volume", "openInterest", "impliedVolatility"]].to_dict("records")
            if not calls.empty else []
        )
        top_put_vol = (
            puts.nlargest(3, "volume")[["strike", "volume", "openInterest", "impliedVolatility"]].to_dict("records")
            if not puts.empty else []
        )

        atm_call = calls.iloc[(calls["strike"] - current_price).abs().argsort()[:1]]
        atm_put = puts.iloc[(puts["strike"] - current_price).abs().argsort()[:1]]

        expected_move = 0.0
        if not atm_call.empty and not atm_put.empty:
            call_price = float(atm_call["lastPrice"].iloc[0]) if "lastPrice" in atm_call else 0
            put_price = float(atm_put["lastPrice"].iloc[0]) if "lastPrice" in atm_put else 0
            expected_move = call_price + put_price

        gex = 0.0
        if "gamma" in calls.columns and "openInterest" in calls.columns:
            calls_gex = (calls["gamma"] * calls["openInterest"] * 100 * current_price).sum()
            puts_gex = (puts["gamma"] * puts["openInterest"] * 100 * current_price).sum()
            gex = float(calls_gex - puts_gex)

        unusual_calls = []
        unusual_puts = []
        if "volume" in calls.columns and "openInterest" in calls.columns:
            calls_copy = calls.copy()
            calls_copy["vol_oi_ratio"] = calls_copy["volume"] / (calls_copy["openInterest"] + 1)
            unusual_calls = (
                calls_copy[calls_copy["vol_oi_ratio"] > 2]
                .nlargest(3, "volume")[["strike", "volume", "openInterest", "lastPrice"]]
                .to_dict("records")
            )

        if "volume" in puts.columns and "openInterest" in puts.columns:
            puts_copy = puts.copy()
            puts_copy["vol_oi_ratio"] = puts_copy["volume"] / (puts_copy["openInterest"] + 1)
            unusual_puts = (
                puts_copy[puts_copy["vol_oi_ratio"] > 2]
                .nlargest(3, "volume")[["strike", "volume", "openInterest", "lastPrice"]]
                .to_dict("records")
            )

        return {
            "ticker": ticker.upper(),
            "current_price": current_price,
            "nearest_expiry": nearest_exp,
            "available_expiries": list(options_dates[:5]),
            "total_call_vol": total_call_vol,
            "total_put_vol": total_put_vol,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "pc_ratio_vol": round(pc_ratio_vol, 2),
            "pc_ratio_oi": round(pc_ratio_oi, 2),
            "top_call_strikes": top_call_vol,
            "top_put_strikes": top_put_vol,
            "expected_move": round(expected_move, 2),
            "gex": gex,
            "unusual_calls": unusual_calls,
            "unusual_puts": unusual_puts,
        }
    except Exception as e:
        logger.error(f"Error getting options chain for {ticker}: {e}")
        return {"error": str(e)}


def get_options_flow(ticker: str) -> Dict[str, Any]:
    """Detect unusual options flow."""
    try:
        stock = yf.Ticker(ticker)
        options_dates = stock.options

        if not options_dates:
            return {"error": "No options data available"}

        hist = stock.history(period="2d")
        current_price = float(hist["Close"].iloc[-1]) if not hist.empty else 0

        sweeps = []
        blocks = []
        bullish_premium = 0.0
        bearish_premium = 0.0

        for exp in options_dates[:3]:
            try:
                chain = stock.option_chain(exp)
                calls = chain.calls
                puts = chain.puts

                for _, row in calls.iterrows():
                    premium = float(row.get("lastPrice", 0) or 0) * float(row.get("volume", 0) or 0) * 100
                    if premium > 50000:
                        flow_type = (
                            "sweep"
                            if float(row.get("volume", 0)) > float(row.get("openInterest", 1) or 1)
                            else "block"
                        )
                        entry = {
                            "type": "CALL",
                            "strike": float(row["strike"]),
                            "expiry": exp,
                            "premium": round(premium / 1000, 1),
                            "volume": int(row.get("volume", 0) or 0),
                            "flow_type": flow_type,
                        }
                        if flow_type == "sweep":
                            sweeps.append(entry)
                        else:
                            blocks.append(entry)
                        bullish_premium += premium

                for _, row in puts.iterrows():
                    premium = float(row.get("lastPrice", 0) or 0) * float(row.get("volume", 0) or 0) * 100
                    if premium > 50000:
                        flow_type = (
                            "sweep"
                            if float(row.get("volume", 0)) > float(row.get("openInterest", 1) or 1)
                            else "block"
                        )
                        entry = {
                            "type": "PUT",
                            "strike": float(row["strike"]),
                            "expiry": exp,
                            "premium": round(premium / 1000, 1),
                            "volume": int(row.get("volume", 0) or 0),
                            "flow_type": flow_type,
                        }
                        if flow_type == "sweep":
                            sweeps.append(entry)
                        else:
                            blocks.append(entry)
                        bearish_premium += premium
            except Exception:
                continue

        total_premium = bullish_premium + bearish_premium
        bull_ratio = (bullish_premium / total_premium * 100) if total_premium > 0 else 50.0

        sweeps = sorted(sweeps, key=lambda x: x["premium"], reverse=True)[:5]
        blocks = sorted(blocks, key=lambda x: x["premium"], reverse=True)[:5]

        return {
            "ticker": ticker.upper(),
            "current_price": current_price,
            "sweeps": sweeps,
            "blocks": blocks,
            "bullish_premium_pct": round(bull_ratio, 1),
            "bearish_premium_pct": round(100 - bull_ratio, 1),
            "total_premium_k": round(total_premium / 1000, 1),
        }
    except Exception as e:
        logger.error(f"Error getting options flow for {ticker}: {e}")
        return {"error": str(e)}
