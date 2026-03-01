import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.data_service import get_historical_data, get_technical_indicators
from bot.services.pattern_engine import detect_unusual_volume
from bot.utils.formatters import fmt_volume, fmt_pct, fmt_price

logger = logging.getLogger(__name__)


async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /volume TICKER\nExample: /volume AAPL")
        return

    ticker = context.args[0].upper()
    msg = await update.message.reply_text(f"📊 Analyzing {ticker} volume...")

    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, lambda: get_historical_data(ticker, period="3mo", interval="1d")
        )

        if df.empty:
            await msg.edit_text(f"❌ No data found for {ticker}")
            return

        indicators = get_technical_indicators(df)
        vol_result = detect_unusual_volume(df)

        volume = df["Volume"]
        close = df["Close"]

        current_vol = int(volume.iloc[-1]) if not volume.empty else 0
        avg_vol_30 = float(volume.tail(30).mean()) if len(volume) >= 30 else float(volume.mean())
        avg_vol_10 = float(volume.tail(10).mean()) if len(volume) >= 10 else float(volume.mean())

        vol_ratio_30 = current_vol / avg_vol_30 if avg_vol_30 > 0 else 1.0
        vol_ratio_10 = current_vol / avg_vol_10 if avg_vol_10 > 0 else 1.0

        vol_expanding = avg_vol_10 > avg_vol_30 * 1.15
        vol_contracting = avg_vol_10 < avg_vol_30 * 0.85
        vol_trend = (
            "Expanding 📈" if vol_expanding else "Contracting 📉" if vol_contracting else "Normal ➡️"
        )

        # On-Balance Volume
        obv = 0
        obv_vals = []
        for i in range(len(close)):
            if i == 0:
                obv_vals.append(0)
            elif close.iloc[i] > close.iloc[i - 1]:
                obv += int(volume.iloc[i])
                obv_vals.append(obv)
            elif close.iloc[i] < close.iloc[i - 1]:
                obv -= int(volume.iloc[i])
                obv_vals.append(obv)
            else:
                obv_vals.append(obv)

        obv_trend = "Bullish" if len(obv_vals) >= 10 and obv_vals[-1] > obv_vals[-10] else "Bearish"

        current_price = float(close.iloc[-1])
        vwap = indicators.get("vwap")
        vwap_pos = (
            "Above VWAP 🟢"
            if vwap and current_price > vwap
            else "Below VWAP 🔴" if vwap else "N/A"
        )

        spike_alert = ""
        if vol_result.get("detected"):
            spike_alert = (
                f"\n🚨 *VOLUME SPIKE DETECTED*\n"
                f"  {vol_result.get('vol_ratio', 0):.1f}x average volume\n"
                f"  Price change: {fmt_pct(vol_result.get('price_change_pct'))}\n"
            )

        text = (
            f"📊 *{ticker} Volume Analysis*\n\n"
            f"💲 Price: {fmt_price(current_price)}\n\n"
            f"📦 *Volume:*\n"
            f"  Today: {fmt_volume(current_vol)}\n"
            f"  10-day avg: {fmt_volume(avg_vol_10)}\n"
            f"  30-day avg: {fmt_volume(avg_vol_30)}\n"
            f"  vs 30-day: {vol_ratio_30:.2f}x\n"
            f"  Trend: {vol_trend}\n"
            f"{spike_alert}\n"
            f"📈 *Accumulation/Distribution:*\n"
            f"  OBV Trend: {obv_trend}\n"
            f"  VWAP Position: {vwap_pos}\n\n"
            f"💡 *Analysis:*\n"
        )

        analysis = []
        if vol_ratio_30 > 3:
            analysis.append("• Extreme volume surge — watch for major move")
        elif vol_ratio_30 > 2:
            analysis.append("• Strong volume spike — high interest")
        elif vol_ratio_30 < 0.5:
            analysis.append("• Very low volume — low conviction")

        if obv_trend == "Bullish" and vol_expanding:
            analysis.append("• Rising OBV + expanding volume = accumulation")
        elif obv_trend == "Bearish" and vol_expanding:
            analysis.append("• Falling OBV + expanding volume = distribution")

        if not analysis:
            analysis.append("• Volume within normal range")

        text += "\n".join(analysis)

        await msg.edit_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in /volume {ticker}: {e}")
        await msg.edit_text(f"❌ Error analyzing volume for {ticker}: {str(e)}")
