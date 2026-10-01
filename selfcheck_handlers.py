"""Static handler-registration check.

Stubs out pyrogram.Client so `main.py` can be imported without touching
Telegram, then prints every handler that got registered.

    .venv/bin/python selfcheck_handlers.py
"""

import os
import sys

os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("API_ID", "1")
os.environ.setdefault("API_HASH", "test")
os.environ.setdefault("LOG_CHANNEL", "-1000000000001")
os.environ.setdefault("AUTH_USERS", "111 222")
os.environ.setdefault("DB_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("DB_NAME", "BroadcastBotSelfCheck")

import pyrogram  # noqa: E402

REGISTERED = []


class FakeClient:
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs

    def _decorator(self, kind, filters_obj, group=None):
        def deco(func):
            REGISTERED.append((kind, repr(filters_obj), func.__name__))
            return func
        return deco

    def on_message(self, filters_obj=None, group=None):
        return self._decorator("message", filters_obj, group)

    def on_callback_query(self, filters_obj=None, group=None):
        return self._decorator("callback_query", filters_obj, group)

    def __getattr__(self, item):
        if item.startswith("on_"):
            return lambda filters_obj=None, group=None: self._decorator(
                item[3:], filters_obj, group
            )
        raise AttributeError(item)

    def run(self):
        print(f"\nClient({self.name!r}) would now start polling Telegram.")
        print(f"Registered handlers: {len(REGISTERED)}\n")


pyrogram.Client = FakeClient

import main  # noqa: E402,F401

names = [n for _, _, n in REGISTERED]
print(f"{'TYPE':<16} {'HANDLER':<26} FILTERS")
print("-" * 90)
for kind, flt, name in REGISTERED:
    print(f"{kind:<16} {name:<26} {flt}")

expected = {
    "startprivate",
    "opensettings",
    "broadcast_handler_open",
    "sts",
    "addgroup_handler",
    "delgroup_handler",
    "groups_handler",
    "gbroadcast_handler",
    "auto_register_group",
    "auto_unregister_group",
}
missing = expected - set(names)

print("\n" + "=" * 90)
if missing:
    print(f"❌ MISSING handlers: {sorted(missing)}")
    sys.exit(1)
print(f"✅ All {len(expected)} expected handlers registered "
      f"({len(REGISTERED)} total).")
print("=" * 90)
