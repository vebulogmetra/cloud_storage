from loguru import logger

from app.settings import LOGS_PATH

logger.add(
    encoding="u8",
    sink=LOGS_PATH,
    format="{time:DD-MM-YYYY at HH:mm:ss} | {level} | {message}",
    rotation="1 week",
    compression="zip",
    backtrace=False,
)
