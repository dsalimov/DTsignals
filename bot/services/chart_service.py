import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import mplfinance as mpf
import pandas as pd
import numpy as np
import io
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def generate_chart(
    df: pd.DataFrame,
    ticker: str,
    pattern_info: Optional[Dict[str, Any]] = None,
    indicators: Optional[Dict[str, Any]] = None,
) -> Optional[bytes]:
    """Generate a professional candlestick chart and return as PNG bytes."""
    if df is None or df.empty or len(df) < 5:
        return None

    try:
        df = df.copy()
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df.columns:
                return None

        close = df["Close"]
        volume = df["Volume"]

        add_plots = []
        colors_style = {
            "ma20": "#2196F3",
            "ma50": "#FF9800",
            "ma200": "#9C27B0",
            "vwap": "#00BCD4",
        }

        if len(close) >= 20:
            ma20 = close.rolling(20).mean()
            add_plots.append(mpf.make_addplot(ma20, color=colors_style["ma20"], width=1.2))

        if len(close) >= 50:
            ma50 = close.rolling(50).mean()
            add_plots.append(mpf.make_addplot(ma50, color=colors_style["ma50"], width=1.2))

        if len(close) >= 200:
            ma200 = close.rolling(200).mean()
            add_plots.append(mpf.make_addplot(ma200, color=colors_style["ma200"], width=1.2))

        typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
        if volume.sum() > 0:
            vwap = (typical_price * volume).cumsum() / volume.cumsum()
            add_plots.append(
                mpf.make_addplot(vwap, color=colors_style["vwap"], width=1.5, linestyle="--")
            )

        mc = mpf.make_marketcolors(
            up="#26A69A",
            down="#EF5350",
            edge="inherit",
            wick={"up": "#26A69A", "down": "#EF5350"},
            volume={"up": "#26A69A", "down": "#EF5350"},
        )
        style = mpf.make_mpf_style(
            marketcolors=mc,
            facecolor="#131722",
            edgecolor="#2A2E39",
            figcolor="#131722",
            gridcolor="#2A2E39",
            gridstyle="--",
            y_on_right=True,
            rc={
                "axes.labelcolor": "#D1D4DC",
                "xtick.color": "#D1D4DC",
                "ytick.color": "#D1D4DC",
                "text.color": "#D1D4DC",
            },
        )

        fig, axes = mpf.plot(
            df,
            type="candle",
            style=style,
            title=f"\n{ticker} - Price Chart",
            volume=True,
            addplot=add_plots if add_plots else None,
            figsize=(14, 9),
            tight_layout=True,
            returnfig=True,
            warn_too_much_data=10000,
        )

        ax_main = axes[0]

        if pattern_info and pattern_info.get("detected"):
            _draw_pattern_annotations(ax_main, df, pattern_info)

        legend_elements = []
        if len(close) >= 20:
            legend_elements.append(mpatches.Patch(color=colors_style["ma20"], label="MA20"))
        if len(close) >= 50:
            legend_elements.append(mpatches.Patch(color=colors_style["ma50"], label="MA50"))
        if len(close) >= 200:
            legend_elements.append(mpatches.Patch(color=colors_style["ma200"], label="MA200"))
        legend_elements.append(mpatches.Patch(color=colors_style["vwap"], label="VWAP"))

        if legend_elements:
            ax_main.legend(
                handles=legend_elements,
                loc="upper left",
                facecolor="#1E2130",
                edgecolor="#2A2E39",
                labelcolor="#D1D4DC",
                fontsize=8,
            )

        if pattern_info and pattern_info.get("detected"):
            pattern_name = pattern_info.get("pattern", "Pattern")
            confidence = pattern_info.get("confidence", 0)
            bias = pattern_info.get("bias", "").upper()
            color = "#26A69A" if bias == "BULLISH" else "#EF5350"
            ax_main.set_title(
                f"{ticker}  |  {pattern_name}  |  {bias}  |  {confidence}% confidence",
                color=color,
                fontsize=11,
                pad=5,
                fontweight="bold",
            )

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        logger.error(f"Error generating chart for {ticker}: {e}")
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _draw_pattern_annotations(ax, df: pd.DataFrame, pattern_info: Dict[str, Any]):
    """Draw pattern-specific annotations on the chart."""
    try:
        n = len(df)
        x_end = n - 1
        bias = pattern_info.get("bias", "bullish")
        color = "#26A69A" if bias == "bullish" else "#EF5350"

        if "target" in pattern_info:
            ax.axhline(
                y=pattern_info["target"],
                color="#FFD700",
                linestyle="--",
                alpha=0.8,
                linewidth=1.2,
            )
            ax.annotate(
                f"🎯 ${pattern_info['target']:.2f}",
                xy=(x_end, pattern_info["target"]),
                xycoords="data",
                color="#FFD700",
                fontsize=8,
                fontweight="bold",
            )

        if "invalidation" in pattern_info:
            ax.axhline(
                y=pattern_info["invalidation"],
                color="#FF4444",
                linestyle=":",
                alpha=0.7,
                linewidth=1.0,
            )
            ax.annotate(
                f"❌ ${pattern_info['invalidation']:.2f}",
                xy=(x_end, pattern_info["invalidation"]),
                xycoords="data",
                color="#FF4444",
                fontsize=8,
            )

        if "neckline" in pattern_info:
            ax.axhline(
                y=pattern_info["neckline"],
                color="#FFA500",
                linestyle="-.",
                alpha=0.8,
                linewidth=1.2,
            )

        if "resistance" in pattern_info:
            ax.axhline(
                y=pattern_info["resistance"],
                color=color,
                linestyle="--",
                alpha=0.7,
                linewidth=1.0,
            )

        if "support" in pattern_info:
            ax.axhline(
                y=pattern_info["support"],
                color=color,
                linestyle="--",
                alpha=0.7,
                linewidth=1.0,
            )
    except Exception as e:
        logger.warning(f"Error drawing pattern annotations: {e}")
