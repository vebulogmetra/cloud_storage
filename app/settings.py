import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = Path(".").joinpath("db.sqlite3")
CREATE_DB_SCRIPT_PATH = Path(".").joinpath("app/createdb.sql")
LOGS_PATH = Path(".").joinpath("logs/log.log")
