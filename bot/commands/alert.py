import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import add_alert, get_alerts

logger = logging.getLogger(__name__)

VALID_ALERT_TYPES = ["breakout", "unusual_volume", "gamma_squeeze"]


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /alert TICKER TYPE\n\n"
            "Alert types:\n"
            "• breakout\n"
            "• unusual_volume\n"
            "• gamma_squeeze _(coming soon)_\n\n"
            "Example: /alert AAPL breakout",
            parse_mode="Markdown",
        )
        return

    ticker = context.args[0].upper()
    alert_type = context.args[1].lower()

    if alert_type not in VALID_ALERT_TYPES:
        await update.message.reply_text(
            f"❌ Invalid alert type: {alert_type}\n\n"
            f"Valid types: {', '.join(VALID_ALERT_TYPES)}"
        )
        return

    chat_id = update.effective_chat.id

    try:
        await add_alert(chat_id, ticker, alert_type)

        type_descriptions = {
            "breakout": "price breakout",
            "unusual_volume": "unusual volume spike",
            "gamma_squeeze": "gamma squeeze watch (notifications coming soon)",
        }

        note = ""
        if alert_type == "gamma_squeeze":
            note = "\n⚠️ _Gamma squeeze detection is in development. Alert registered but will not trigger until available._\n"

        await update.message.reply_text(
            f"✅ *Alert Set!*\n\n"
            f"📌 Ticker: *{ticker}*\n"
            f"🔔 Alert: {type_descriptions[alert_type]}\n"
            f"{note}\n"
            f"You'll be notified when conditions are met.\n"
            f"Bot checks every minute.",
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Error setting alert: {e}")
        await update.message.reply_text(f"❌ Error setting alert: {str(e)}")
