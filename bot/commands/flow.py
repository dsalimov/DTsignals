import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.options_service import get_options_flow
from bot.utils.formatters import fmt_price, fmt_volume

logger = logging.getLogger(__name__)


async def flow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /flow TICKER\nExample: /flow AAPL")
        return

    ticker = context.args[0].upper()
    msg = await update.message.reply_text(f"🌊 Analyzing {ticker} options flow...")

    try:
        loop = asyncio.get_event_loop()
        flow = await loop.run_in_executor(None, lambda: get_options_flow(ticker))

        if "error" in flow:
            await msg.edit_text(f"❌ {flow['error']}")
            return

        bull_pct = flow.get("bullish_premium_pct", 50)
        bear_pct = flow.get("bearish_premium_pct", 50)
        total_prem = flow.get("total_premium_k", 0)

        bull_bars = int(bull_pct / 20)
        bear_bars = int(bear_pct / 20)
        bias_bar = "🟢" * bull_bars + "🔴" * bear_bars
        overall_bias = "BULLISH" if bull_pct > 55 else "BEARISH" if bear_pct > 55 else "NEUTRAL"

        text = (
            f"🌊 *{ticker} Options Flow*\n\n"
            f"💲 Price: {fmt_price(flow.get('current_price'))}\n\n"
            f"📊 *Flow Bias:*\n"
            f"  {bias_bar}\n"
            f"  Bullish: {bull_pct:.0f}% | Bearish: {bear_pct:.0f}%\n"
            f"  Overall: *{overall_bias}*\n"
            f"  Total Premium: ${total_prem:.0f}K\n\n"
        )

        sweeps = flow.get("sweeps", [])
        if sweeps:
            text += "⚡ *Unusual Sweeps:*\n"
            for s in sweeps[:4]:
                opt_type = s.get("type", "")
                emoji = "🟢" if opt_type == "CALL" else "🔴"
                text += (
                    f"  {emoji} {opt_type} ${s.get('strike', 0):.0f} "
                    f"exp {s.get('expiry', 'N/A')}\n"
                    f"    Premium: ${s.get('premium', 0):.0f}K | "
                    f"Vol: {fmt_volume(s.get('volume'))}\n"
                )
        else:
            text += "⚡ *No unusual sweeps detected*\n"

        blocks = flow.get("blocks", [])
        if blocks:
            text += "\n🧱 *Block Trades:*\n"
            for b in blocks[:3]:
                opt_type = b.get("type", "")
                emoji = "🟢" if opt_type == "CALL" else "🔴"
                text += (
                    f"  {emoji} {opt_type} ${b.get('strike', 0):.0f} "
                    f"exp {b.get('expiry', 'N/A')}\n"
                    f"    Premium: ${b.get('premium', 0):.0f}K\n"
                )

        await msg.edit_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in /flow {ticker}: {e}")
        await msg.edit_text(f"❌ Error analyzing flow for {ticker}: {str(e)}")
