import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", ""))
AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "").split())
DB_URL = os.environ.get("DB_URL", "")
DB_NAME = os.environ.get("DB_NAME", "BroadcastBot")

# broadcast settings

BROADCAST_AS_COPY = bool(os.environ.get("BROADCAST_AS_COPY", True))
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT", "15"))  # Maximum concurrent message sends. You can set this value up to 1000 if you are using a paid broadcast.
UPDATE_INTERVAL = int(os.environ.get("UPDATE_INTERVAL", "2"))  # Update interval in seconds to avoid flood waits