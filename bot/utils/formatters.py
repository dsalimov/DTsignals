from typing import Any


def fmt_price(price: Any) -> str:
    if price is None or price == 0:
        return "N/A"
    try:
        return f"${float(price):,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def fmt_pct(val: Any, decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"


def fmt_volume(vol: Any) -> str:
    if vol is None or vol == 0:
        return "N/A"
    try:
        v = float(vol)
        if v >= 1_000_000_000:
            return f"{v / 1_000_000_000:.2f}B"
        elif v >= 1_000_000:
            return f"{v / 1_000_000:.2f}M"
        elif v >= 1_000:
            return f"{v / 1_000:.1f}K"
        return str(int(v))
    except (ValueError, TypeError):
        return "N/A"


def fmt_marketcap(cap: Any) -> str:
    if cap is None or cap == 0:
        return "N/A"
    try:
        v = float(cap)
        if v >= 1_000_000_000_000:
            return f"${v / 1_000_000_000_000:.2f}T"
        elif v >= 1_000_000_000:
            return f"${v / 1_000_000_000:.2f}B"
        elif v >= 1_000_000:
            return f"${v / 1_000_000:.2f}M"
        return fmt_price(v)
    except (ValueError, TypeError):
        return "N/A"


def fmt_rsi(rsi: Any) -> str:
    if rsi is None:
        return "N/A"
    try:
        v = float(rsi)
        if v >= 70:
            return f"{v:.1f} (Overbought)"
        elif v <= 30:
            return f"{v:.1f} (Oversold)"
        return f"{v:.1f}"
    except (ValueError, TypeError):
        return "N/A"


def trend_emoji(trend: str) -> str:
    return "📈" if trend == "bullish" else "📉" if trend == "bearish" else "➡️"
