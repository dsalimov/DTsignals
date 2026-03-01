from telegram.ext import CommandHandler
from bot.commands.stock import stock_command
from bot.commands.chart import chart_command
from bot.commands.scan import scan_command
from bot.commands.options import options_command
from bot.commands.flow import flow_command
from bot.commands.volume import volume_command
from bot.commands.alert import alert_command


async def start_command(update, context):
    await update.message.reply_text(
        "🤖 *DTSignals Trading Bot*\n\n"
        "Professional options flow & technical analysis bot.\n\n"
        "*Commands:*\n"
        "/stock TICKER - Full stock analysis\n"
        "/chart TICKER - Price chart with patterns\n"
        "/scan PATTERN - Scan US stocks for patterns\n"
        "/options TICKER - Options chain analysis\n"
        "/flow TICKER - Unusual options flow\n"
        "/volume TICKER - Volume analysis\n"
        "/alert TICKER TYPE - Set price alerts\n\n"
        "Example: /stock AAPL",
        parse_mode="Markdown",
    )


async def help_command(update, context):
    await update.message.reply_text(
        "*DTSignals Bot - Help*\n\n"
        "*/stock TICKER* - Full analysis:\n"
        "  Price, volume, indicators, key levels\n\n"
        "*/chart TICKER [1d|1wk|1mo]* - Chart:\n"
        "  Candlestick with patterns drawn\n\n"
        "*/scan PATTERN* - Scanner:\n"
        "  breakout, h&s, cup_handle, triangle,\n"
        "  unusual_volume, double_top, double_bottom\n\n"
        "*/options TICKER* - Options analysis:\n"
        "  Greeks, IV rank, unusual flow\n\n"
        "*/flow TICKER* - Options flow:\n"
        "  Sweeps, blocks, premium activity\n\n"
        "*/volume TICKER* - Volume analysis:\n"
        "  Spikes, accumulation/distribution\n\n"
        "*/alert TICKER TYPE* - Alerts:\n"
        "  breakout, unusual_volume, gamma_squeeze",
        parse_mode="Markdown",
    )


def register_handlers(application):
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("chart", chart_command))
    application.add_handler(CommandHandler("scan", scan_command))
    application.add_handler(CommandHandler("options", options_command))
    application.add_handler(CommandHandler("flow", flow_command))
    application.add_handler(CommandHandler("volume", volume_command))
    application.add_handler(CommandHandler("alert", alert_command))
