import logging
from bot.database.db import get_alerts, deactivate_alert
from bot.services.data_service import get_historical_data
from bot.services.pattern_engine import detect_breakout, detect_unusual_volume

logger = logging.getLogger(__name__)


async def check_alerts(context):
    """Check all active alerts and send notifications."""
    try:
        alerts = await get_alerts()
        if not alerts:
            return

        for alert in alerts:
            alert_id, chat_id, ticker, alert_type, active, created_at = alert
            try:
                await _process_alert(context, alert_id, chat_id, ticker, alert_type)
            except Exception as e:
                logger.error(f"Error processing alert {alert_id}: {e}")
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")


async def _process_alert(context, alert_id: int, chat_id: int, ticker: str, alert_type: str):
    """Process a single alert."""
    import asyncio

    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(
        None, lambda: get_historical_data(ticker, period="1mo", interval="1d")
    )

    if df.empty:
        return

    triggered = False
    message = ""

    if alert_type == "breakout":
        result = detect_breakout(df)
        if result.get("detected"):
            triggered = True
            message = (
                f"🚨 *{ticker} Breakout Alert!*\n\n"
                f"Pattern: {result['pattern']}\n"
                f"Bias: {result['bias'].upper()}\n"
                f"Confidence: {result.get('confidence', 0)}%\n"
                f"Target: ${result.get('target', 'N/A')}\n"
                f"Vol Confirmed: {'✅' if result.get('vol_confirmed') else '❌'}"
            )

    elif alert_type == "unusual_volume":
        result = detect_unusual_volume(df)
        if result.get("detected"):
            triggered = True
            message = (
                f"📊 *{ticker} Unusual Volume Alert!*\n\n"
                f"Volume Ratio: {result.get('vol_ratio', 0)}x average\n"
                f"Price Change: {result.get('price_change_pct', 0):+.2f}%\n"
                f"Bias: {result.get('bias', '').upper()}"
            )

    elif alert_type == "gamma_squeeze":
        # Placeholder — monitoring logic can be expanded later
        triggered = False

    if triggered and message:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error sending alert to {chat_id}: {e}")
