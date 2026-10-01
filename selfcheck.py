"""Standalone self-check for the multi-group broadcast add-on.

Runs against the local MongoDB (start it with ../start-mongo.sh first):

    .venv/bin/python selfcheck.py
"""

import asyncio
import os
import sys

os.environ.setdefault("BOT_TOKEN", "123456:TEST")
os.environ.setdefault("API_ID", "1")
os.environ.setdefault("API_HASH", "test")
os.environ.setdefault("LOG_CHANNEL", "-1000000000001")
os.environ.setdefault("AUTH_USERS", "111 222")
os.environ.setdefault("DB_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("DB_NAME", "BroadcastBotSelfCheck")

from pyrogram.errors import ChatWriteForbidden  # noqa: E402

from handlers.database import Database  # noqa: E402
from handlers.group_broadcast import send_to_chat  # noqa: E402

PASS, FAIL = 0, 0


def check(label, ok, extra=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label} {extra}")


class FakeMessage:
    """Minimal stand-in for a Telegram Message."""

    def __init__(self):
        self.sent = []

    async def copy(self, chat_id):
        if int(chat_id) == 999:
            raise ChatWriteForbidden()
        self.sent.append(int(chat_id))

    async def forward(self, chat_id):
        return await self.copy(chat_id)


async def main():
    db = Database(os.environ["DB_URL"], os.environ["DB_NAME"])
    await db.groups.delete_many({})  # clean slate

    print("\n[1] group registry (DB layer)")
    await db.add_group(-1001, title="Group A", username="groupa", chat_type="supergroup")
    await db.add_group(-1002, title="Group B", chat_type="supergroup")
    await db.add_group(-1003, title="Channel C", chat_type="channel")
    check("add_group x3", await db.total_groups_count() == 3)

    await db.add_group(-1001, title="Group A renamed", chat_type="supergroup")
    check("add_group upserts (no duplicate)", await db.total_groups_count() == 3)
    cursor = await db.get_all_groups()
    groups = await cursor.to_list(length=None)
    renamed = [g for g in groups if g["chat_id"] == -1001]
    check("upsert updates title", renamed and renamed[0]["title"] == "Group A renamed")

    check("is_group_exist(-1002) is True", await db.is_group_exist(-1002))
    check("is_group_exist(-7777) is False", not await db.is_group_exist(-7777))

    await db.set_group_active(-1003, False)
    check("set_group_active(False) hides it", await db.total_groups_count() == 2)

    await db.delete_group(-1002)
    check("delete_group removes it", await db.total_groups_count() == 1)

    await db.groups.delete_many({})

    print("\n[2] send_to_chat (broadcast worker)")
    await db.add_group(-2001, title="OK 1")
    await db.add_group(-2002, title="OK 2")
    await db.add_group(999, title="Forbidden")

    msg = FakeMessage()
    sem = asyncio.Semaphore(5)
    results = await asyncio.gather(
        *[send_to_chat(g["chat_id"], msg, sem) for g in
          (await (await db.get_all_groups()).to_list(length=None))]
    )
    codes = sorted(r[0] for r in results)
    check("3 chats attempted", len(results) == 3)
    check("2 successes + 1 failure", codes == [200, 200, 403], codes)
    check("only writable chats received", sorted(msg.sent) == [-2002, -2001] or
          sorted(msg.sent) == [-2001, -2002], msg.sent)
    failure = [r for r in results if r[0] == 403]
    check("failure names the chat id", failure and "999" in failure[0][1])

    await db.groups.delete_many({})

    print(f"\n{'='*46}\nPASSED: {PASS}   FAILED: {FAIL}\n{'='*46}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
