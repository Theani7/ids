import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MODEL_PATH = os.getenv("MODEL_PATH", "models/ids_model.pkl")
FEATURE_COLUMNS_PATH = os.getenv("FEATURE_COLUMNS_PATH", "models/feature_columns.pkl")
NETWORK_INTERFACE = os.getenv("NETWORK_INTERFACE", "eth0")
FLOW_TIMEOUT = 60  # seconds
TELEGRAM_COOLDOWN = 10  # seconds between malicious alerts
TELEGRAM_NORMAL_INTERVAL = 300  # seconds between normal summaries

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-intruml-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
