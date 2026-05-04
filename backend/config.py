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
BASE_PATH = Path(__file__).parent.parent
MODEL_PATH = BASE_PATH / os.getenv("MODEL_PATH", "models/ids_model.pkl")
FEATURE_COLUMNS_PATH = BASE_PATH / os.getenv("FEATURE_COLUMNS_PATH", "models/feature_columns.pkl")

def _get_default_interface() -> str:
    try:
        from scapy.all import conf, get_if_list
        # Scapy's conf.iface is the best bet
        if conf.iface:
            return str(conf.iface)

        # Try to find something reasonable from the list
        ifaces = get_if_list()
        if sys.platform == "win32":
            # On Windows, look for NPF interfaces (Npcap/WinPcap)
            for iface in ifaces:
                if "NPF" in iface:
                    return iface
        elif sys.platform == "darwin":
            if "en0" in ifaces: return "en0"
    except Exception:
        pass

    try:
        import psutil
        interfaces = list(psutil.net_if_addrs().keys())

        if sys.platform == "darwin":
            for iface in ["en0", "en1", "en2", "en3"]:
                if iface in interfaces:
                    return iface
            return "en0"

        if sys.platform == "win32":
            # On Windows, we want the NPF/Npcap interface names
            for iface in interfaces:
                if "ethernet" in iface.lower() or "wi-fi" in iface.lower() or "npf" in iface.lower():
                    return iface
            return interfaces[0] if interfaces else "\\\\Device\\\\NPF_Unknown"

        for iface in interfaces:
            if iface.lower() in ["wifi", "wi-fi", "ethernet", "lan", "wan", "wlan0", "eth0"]:
                return iface

        return interfaces[0] if interfaces else "eth0"
    except Exception:
        return "eth0"

NETWORK_INTERFACE = os.getenv("NETWORK_INTERFACE", _get_default_interface())
FLOW_TIMEOUT = int(os.getenv("FLOW_TIMEOUT", "60"))
TELEGRAM_COOLDOWN = int(os.getenv("TELEGRAM_COOLDOWN", "10"))
TELEGRAM_NORMAL_INTERVAL = int(os.getenv("TELEGRAM_NORMAL_INTERVAL", "300"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    import secrets
    SECRET_KEY = secrets.token_hex(32)
    logger.warning("Using auto-generated SECRET_KEY. Set SECRET_KEY in .env for production!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7)))

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")

TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Kolkata")
try:
    TIMEZONE = ZoneInfo(TIMEZONE_NAME)
except Exception:
    logger.warning(f"Invalid timezone '{TIMEZONE_NAME}', falling back to UTC")
    TIMEZONE = ZoneInfo("UTC")
