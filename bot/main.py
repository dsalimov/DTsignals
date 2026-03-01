import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application
from bot.handlers import register_handlers
from bot.database.db import init_db
from bot.services.scanner_service import run_scheduled_scan
from bot.services.alert_service import check_alerts

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=os.getenv("LOG_LEVEL", "INFO"),
)
logger = logging.getLogger(__name__)


async def post_init(application):
    await init_db()
    logger.info("Database initialized")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

    application = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    register_handlers(application)

    interval = int(os.getenv("SCAN_INTERVAL_MINUTES", "30")) * 60
    application.job_queue.run_repeating(run_scheduled_scan, interval=interval, first=60)
    application.job_queue.run_repeating(check_alerts, interval=60, first=10)

    logger.info("Starting bot...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
