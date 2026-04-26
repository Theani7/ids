import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    logger.info(".env file not found, using default configuration")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MODEL_PATH = os.getenv("MODEL_PATH", "models/ids_model.pkl")
FEATURE_COLUMNS_PATH = os.getenv("FEATURE_COLUMNS_PATH", "models/feature_columns.pkl")
NETWORK_INTERFACE = os.getenv("NETWORK_INTERFACE", "eth0")
FLOW_TIMEOUT = int(os.getenv("FLOW_TIMEOUT", "60"))
TELEGRAM_COOLDOWN = int(os.getenv("TELEGRAM_COOLDOWN", "10"))
TELEGRAM_NORMAL_INTERVAL = int(os.getenv("TELEGRAM_NORMAL_INTERVAL", "300"))

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-intruml-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")

TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Kolkata")
try:
    TIMEZONE = ZoneInfo(TIMEZONE_NAME)
except Exception:
    logger.warning(f"Invalid timezone '{TIMEZONE_NAME}', falling back to UTC")
    TIMEZONE = ZoneInfo("UTC")
