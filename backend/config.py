import os
import sys
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

def _get_default_interface() -> str:
    import psutil
    interfaces = list(psutil.net_if_addrs().keys())
    logger.info(f"Available network interfaces: {interfaces}")
    
    if sys.platform == "darwin":
        if "en0" in interfaces:
            return "en0"
        for iface in ["en1", "en2", "en3"]:
            if iface in interfaces:
                return iface
    
    for iface in interfaces:
        if iface.lower() in ["wifi", "wi-fi", "ethernet", "lan", "wan"]:
            return iface
    if sys.platform == "win32":
        for iface in interfaces:
            if not iface.startswith("\\"):
                return iface
        return interfaces[0] if interfaces else "\\Device\\NPF_Unknown"
    return interfaces[0] if interfaces else "eth0"

NETWORK_INTERFACE = os.getenv("NETWORK_INTERFACE", _get_default_interface())
MODEL_PATH = os.getenv("MODEL_PATH", "models/ids_model.pkl")
FEATURE_COLUMNS_PATH = os.getenv("FEATURE_COLUMNS_PATH", "models/feature_columns.pkl")
FLOW_TIMEOUT = int(os.getenv("FLOW_TIMEOUT", "60"))
TELEGRAM_COOLDOWN = int(os.getenv("TELEGRAM_COOLDOWN", "10"))
TELEGRAM_NORMAL_INTERVAL = int(os.getenv("TELEGRAM_NORMAL_INTERVAL", "300"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

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
