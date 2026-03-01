import asyncio
import logging
import io
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.data_service import get_historical_data, get_technical_indicators
from bot.services.pattern_engine import detect_all_patterns
from bot.services.chart_service import generate_chart

logger = logging.getLogger(__name__)

PERIOD_MAP = {
    "1d": ("5d", "15m"),
    "1w": ("1mo", "1h"),
    "1wk": ("1mo", "1h"),
    "1mo": ("6mo", "1d"),
    "3mo": ("1y", "1d"),
    "6mo": ("2y", "1wk"),
    "1y": ("5y", "1wk"),
}


async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /chart TICKER [1d|1wk|1mo|3mo|6mo|1y]\nExample: /chart AAPL 1mo"
        )
        return

    ticker = context.args[0].upper()
    timeframe = context.args[1].lower() if len(context.args) > 1 else "3mo"

    period, interval = PERIOD_MAP.get(timeframe, ("6mo", "1d"))

    msg = await update.message.reply_text(f"📊 Generating {ticker} chart ({timeframe})...")

    try:
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, lambda: get_historical_data(ticker, period=period, interval=interval)
        )

        if df.empty:
            await msg.edit_text(f"❌ No data found for {ticker}")
            return

        patterns = detect_all_patterns(df)
        best_pattern = patterns[0] if patterns else None
        indicators = get_technical_indicators(df)

        chart_bytes = await loop.run_in_executor(
            None, lambda: generate_chart(df, ticker, best_pattern, indicators)
        )

        if not chart_bytes:
            await msg.edit_text(f"❌ Failed to generate chart for {ticker}")
            return

        caption = f"📊 *{ticker}* — {timeframe.upper()} Chart\n"
        if best_pattern:
            confidence = best_pattern.get("confidence", 0)
            bias = best_pattern.get("bias", "").upper()
            pattern_name = best_pattern.get("pattern", "Pattern")
            target = best_pattern.get("target")
            invalidation = best_pattern.get("invalidation")
            vol_confirmed = best_pattern.get("vol_confirmed", False)

            bias_emoji = "🟢" if bias == "BULLISH" else "🔴"
            caption += (
                f"\n{bias_emoji} *{pattern_name}* detected with *{confidence}%* confidence\n"
                f"Bias: {bias}\n"
            )
            if target:
                caption += f"Target: ${target:.2f}\n"
            if invalidation:
                caption += f"Invalidation: ${invalidation:.2f}\n"
            if vol_confirmed:
                caption += "✅ Volume confirmed\n"
        else:
            caption += "\nNo major pattern detected"

        await msg.delete()
        await update.message.reply_photo(
            photo=io.BytesIO(chart_bytes),
            caption=caption,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error in /chart {ticker}: {e}")
        await msg.edit_text(f"❌ Error generating chart for {ticker}: {str(e)}")
