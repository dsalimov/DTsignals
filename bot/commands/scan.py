import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.scanner_service import scan_for_pattern
from bot.utils.formatters import fmt_price

logger = logging.getLogger(__name__)

PATTERN_ALIASES = {
    "breakout": "breakout",
    "breakdown": "breakout",
    "h&s": "h&s",
    "hs": "h&s",
    "head_shoulders": "h&s",
    "inverse_hs": "inverse_hs",
    "double_top": "double_top",
    "double_bottom": "double_bottom",
    "cup_handle": "cup_handle",
    "cup": "cup_handle",
    "triangle": "ascending_triangle",
    "ascending_triangle": "ascending_triangle",
    "descending_triangle": "descending_triangle",
    "flag": "flag",
    "bull_flag": "flag",
    "unusual_volume": "unusual_volume",
    "volume": "unusual_volume",
}


async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /scan PATTERN\n\n"
            "Available patterns:\n"
            "• breakout\n• h&s\n• inverse_hs\n"
            "• double_top\n• double_bottom\n"
            "• cup_handle\n• triangle\n"
            "• flag\n• unusual_volume"
        )
        return

    pattern_input = context.args[0].lower()
    pattern = PATTERN_ALIASES.get(pattern_input, pattern_input)

    msg = await update.message.reply_text(
        f"🔍 Scanning US stocks for *{pattern}* pattern...\nThis may take 1-2 minutes.",
        parse_mode="Markdown",
    )

    try:
        results = await scan_for_pattern(pattern, max_stocks=60)

        if not results:
            await msg.edit_text(
                f"No stocks found matching *{pattern}* pattern.", parse_mode="Markdown"
            )
            return

        lines = [f"🔍 *Scan Results: {pattern.replace('_', ' ').title()}*\n"]
        lines.append(f"Found {len(results)} match(es)\n")

        for i, r in enumerate(results[:8], 1):
            ticker = r.get("ticker", "?")
            confidence = r.get("confidence", 0)
            bias = r.get("bias", "").upper()
            price = r.get("price")
            target = r.get("target")
            vol_ratio = r.get("vol_ratio")
            vol_confirmed = r.get("vol_confirmed", False)

            bias_emoji = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "🟡"

            line = f"{i}. {bias_emoji} *{ticker}*"
            if price:
                line += f" @ {fmt_price(price)}"
            line += f" — {confidence}% conf\n"

            if target:
                line += f"   Target: {fmt_price(target)}"
            if vol_ratio:
                line += f" | Vol: {vol_ratio}x"
            if vol_confirmed:
                line += " ✅"
            line += "\n"

            lines.append(line)

        lines.append("\nUse /chart TICKER to see the chart.")

        await msg.edit_text("".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in /scan {pattern}: {e}")
        await msg.edit_text(f"❌ Error during scan: {str(e)}")
