import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.options_service import get_options_chain_summary, calculate_iv_rank
from bot.utils.formatters import fmt_price, fmt_volume, fmt_pct

logger = logging.getLogger(__name__)


async def options_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /options TICKER\nExample: /options AAPL")
        return

    ticker = context.args[0].upper()
    msg = await update.message.reply_text(f"⚙️ Analyzing {ticker} options...")

    try:
        loop = asyncio.get_event_loop()

        chain_future = loop.run_in_executor(None, lambda: get_options_chain_summary(ticker))
        iv_future = loop.run_in_executor(None, lambda: calculate_iv_rank(ticker))

        chain, iv_data = await asyncio.gather(chain_future, iv_future)

        if "error" in chain:
            await msg.edit_text(f"❌ {chain['error']}")
            return

        pc_ratio_vol = chain.get("pc_ratio_vol", 0)
        pc_sentiment = (
            "Bullish" if pc_ratio_vol < 0.7 else "Bearish" if pc_ratio_vol > 1.3 else "Neutral"
        )

        iv_rank = iv_data.get("iv_rank")
        iv_pct = iv_data.get("iv_percentile")
        hv30 = iv_data.get("hv30")

        iv_rank_str = f"{iv_rank:.0f}%" if iv_rank is not None else "N/A"
        iv_pct_str = f"{iv_pct:.0f}%" if iv_pct is not None else "N/A"
        hv30_str = f"{hv30:.1f}%" if hv30 is not None else "N/A"

        text = (
            f"⚙️ *{ticker} Options Analysis*\n\n"
            f"💲 *Current Price:* {fmt_price(chain.get('current_price'))}\n"
            f"📅 *Nearest Expiry:* {chain.get('nearest_expiry', 'N/A')}\n\n"
            f"📊 *Volume Summary:*\n"
            f"  Calls: {fmt_volume(chain.get('total_call_vol'))}\n"
            f"  Puts: {fmt_volume(chain.get('total_put_vol'))}\n"
            f"  P/C Vol Ratio: {chain.get('pc_ratio_vol', 0):.2f} ({pc_sentiment})\n\n"
            f"💼 *Open Interest:*\n"
            f"  Calls: {fmt_volume(chain.get('total_call_oi'))}\n"
            f"  Puts: {fmt_volume(chain.get('total_put_oi'))}\n"
            f"  P/C OI Ratio: {chain.get('pc_ratio_oi', 0):.2f}\n\n"
            f"📈 *Expected Move:* ±{fmt_price(chain.get('expected_move'))}\n\n"
            f"🌡️ *Volatility:*\n"
            f"  IV Rank: {iv_rank_str}\n"
            f"  IV Percentile: {iv_pct_str}\n"
            f"  HV30: {hv30_str}\n"
        )

        if chain.get("top_call_strikes"):
            text += "\n📊 *Top Call Strikes by Volume:*\n"
            for s in chain["top_call_strikes"][:3]:
                text += (
                    f"  ${s.get('strike', 0):.0f} | "
                    f"Vol: {fmt_volume(s.get('volume'))} | "
                    f"OI: {fmt_volume(s.get('openInterest'))}\n"
                )

        if chain.get("top_put_strikes"):
            text += "\n📊 *Top Put Strikes by Volume:*\n"
            for s in chain["top_put_strikes"][:3]:
                text += (
                    f"  ${s.get('strike', 0):.0f} | "
                    f"Vol: {fmt_volume(s.get('volume'))} | "
                    f"OI: {fmt_volume(s.get('openInterest'))}\n"
                )

        unusual = chain.get("unusual_calls", []) + chain.get("unusual_puts", [])
        if unusual:
            text += "\n🚨 *Unusual Activity:*\n"
            unusual_call_strikes = {
                (u.get("strike"), u.get("openInterest")) for u in chain.get("unusual_calls", [])
            }
            for u in unusual[:4]:
                key = (u.get("strike"), u.get("openInterest"))
                opt_type = "CALL" if key in unusual_call_strikes else "PUT"
                text += f"  {opt_type} ${u.get('strike', 0):.0f} | Vol/OI spike\n"

        gex = chain.get("gex", 0)
        if gex != 0:
            gex_emoji = "🟢" if gex > 0 else "🔴"
            text += f"\n⚡ *Gamma Exposure (GEX):* {gex_emoji} ${gex / 1e6:.1f}M\n"

        await msg.edit_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in /options {ticker}: {e}")
        await msg.edit_text(f"❌ Error analyzing options for {ticker}: {str(e)}")
