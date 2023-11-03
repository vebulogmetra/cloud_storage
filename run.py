from aiogram import executor

from app import db
from app.bot import dp
from app.logger import logger


def run_bot():
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )


async def on_startup(dp):
    logger.info("Startup bot")


async def on_shutdown(dp):
    db.close_connection()
    logger.info("Shutdown bot")


if __name__ == "__main__":
    run_bot()
