import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.data_service import get_stock_info, get_historical_data, get_technical_indicators
from bot.utils.formatters import fmt_price, fmt_pct, fmt_volume, fmt_marketcap, fmt_rsi, trend_emoji

logger = logging.getLogger(__name__)


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /stock TICKER\nExample: /stock AAPL")
        return

    ticker = context.args[0].upper()
    msg = await update.message.reply_text(f"🔍 Analyzing {ticker}...")

    try:
        loop = asyncio.get_event_loop()

        info_task = asyncio.create_task(get_stock_info(ticker))
        df_future = loop.run_in_executor(
            None, lambda: get_historical_data(ticker, period="6mo", interval="1d")
        )

        info = await info_task
        df = await df_future

        if "error" in info:
            await msg.edit_text(f"❌ Error: {info['error']}")
            return

        indicators = get_technical_indicators(df)

        rating_map = {
            "strongBuy": "Strong Buy ⭐⭐⭐",
            "buy": "Buy ⭐⭐",
            "hold": "Hold ➡️",
            "sell": "Sell 📉",
            "strongSell": "Strong Sell 📉📉",
        }
        analyst_rating = rating_map.get(
            info.get("analyst_rating", ""), info.get("analyst_rating", "N/A")
        )

        vol_ratio = ""
        if indicators.get("vol_ratio"):
            vr = indicators["vol_ratio"]
            vol_ratio = f" ({vr:.1f}x avg)"

        short = indicators.get("short_trend", "N/A")
        mid = indicators.get("mid_trend", "N/A")
        long_ = indicators.get("long_trend", "N/A")

        short_pct = info.get("short_interest", 0)
        short_pct_display = fmt_pct(short_pct * 100 if short_pct else None)

        text = (
            f"📊 *{ticker} Analysis*\n\n"
            f"💰 *Price:* {fmt_price(info['price'])} ({fmt_pct(info['change_pct'])})\n"
            f"📦 *Volume:* {fmt_volume(info['volume'])}{vol_ratio}\n"
            f"🏦 *Market Cap:* {fmt_marketcap(info['market_cap'])}\n"
            f"🔄 *Float:* {fmt_volume(info.get('float_shares'))}\n"
            f"📉 *Short Interest:* {short_pct_display}\n\n"
            f"📅 *52W Range:* {fmt_price(info.get('52w_low'))} - {fmt_price(info.get('52w_high'))}\n"
            f"🏭 *Sector:* {info.get('sector', 'N/A')}\n"
            f"⚡ *Beta:* {info.get('beta', 'N/A')}\n\n"
            f"📈 *Technical Indicators:*\n"
            f"  RSI(14): {fmt_rsi(indicators.get('rsi'))}\n"
            f"  MACD: {fmt_price(indicators.get('macd'))} | Signal: {fmt_price(indicators.get('macd_signal'))}\n"
            f"  VWAP: {fmt_price(indicators.get('vwap'))}\n"
            f"  MA20: {fmt_price(indicators.get('sma20'))} | MA50: {fmt_price(indicators.get('sma50'))}\n\n"
            f"🎯 *Key Levels:*\n"
            f"  Support: {fmt_price(indicators.get('support1'))}\n"
            f"  Resistance: {fmt_price(indicators.get('resistance1'))}\n"
            f"  Pivot: {fmt_price(indicators.get('pivot'))}\n\n"
            f"📊 *Trend:*\n"
            f"  Short: {trend_emoji(short)} {short.title()}\n"
            f"  Mid:   {trend_emoji(mid)} {mid.title()}\n"
            f"  Long:  {trend_emoji(long_)} {long_.title()}\n\n"
            f"⭐ *Analyst Consensus:* {analyst_rating}\n"
            f"💹 *P/E Ratio:* {info.get('pe_ratio', 'N/A')}"
        )

        await msg.edit_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in /stock {ticker}: {e}")
        await msg.edit_text(f"❌ Error analyzing {ticker}: {str(e)}")
