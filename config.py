import os


def _load_dotenv(path=None):
    """Minimal .env loader (no external dependency).

    Existing environment variables always win over the .env file.
    """
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


def _env_int(name, default=""):
    raw = os.environ.get(name, "")
    if raw == "" or raw is None:
        if default == "":
            raise RuntimeError(
                f"Environment variable {name} is required. "
                f"Set it in .env or export it before running."
            )
        return int(default)
    return int(raw)


def _env_bool(name, default=True):
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on", "y", "t")


BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = _env_int("API_ID")
API_HASH = os.environ.get("API_HASH", "")
LOG_CHANNEL = _env_int("LOG_CHANNEL")
AUTH_USERS = set(int(x) for x in os.environ.get("AUTH_USERS", "").split() if x.strip())
DB_URL = os.environ.get("DB_URL", "")
DB_NAME = os.environ.get("DB_NAME", "BroadcastBot")

# broadcast settings

BROADCAST_AS_COPY = _env_bool("BROADCAST_AS_COPY", True)
MAX_CONCURRENT = _env_int("MAX_CONCURRENT", "10")  # Maximum concurrent message sends. You can set this value up to 1000 if you are using a paid broadcast.
UPDATE_INTERVAL = _env_int("UPDATE_INTERVAL", "2")  # Update interval in seconds to avoid flood waits
