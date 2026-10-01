# (c) N A C BOTS
#
# Multi-group / multi-channel broadcasting add-on.
#
# The original bot only knows about *users* (bot subscribers).
# This module adds the ability to broadcast one message to every
# group / channel the bot has been added to.

import asyncio
import datetime
import os
import random
import string
import time
import traceback

import aiofiles
from pyrogram.errors import (
    FloodWait,
    MessageNotModified,
    ChatWriteForbidden,
    ChatAdminRequired,
    ChannelPrivate,
    PeerIdInvalid,
    ChatIdInvalid,
)

import config

group_broadcast_ids = {}

BROADCAST_AS_COPY = config.BROADCAST_AS_COPY
MAX_CONCURRENT = config.MAX_CONCURRENT
UPDATE_INTERVAL = config.UPDATE_INTERVAL


async def send_to_chat(chat_id, message, semaphore):
    """Send/forward `message` to a single group or channel."""
    async with semaphore:
        try:
            if BROADCAST_AS_COPY is False:
                await message.forward(chat_id=chat_id)
            else:
                await message.copy(chat_id=chat_id)
            return 200, None
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await send_to_chat(chat_id, message, semaphore)
        except ChatWriteForbidden:
            return 403, f"{chat_id} : bot cannot post here (muted / no write permission)\n"
        except ChatAdminRequired:
            return 403, f"{chat_id} : admin rights required\n"
        except ChannelPrivate:
            return 400, f"{chat_id} : chat is private or bot was kicked\n"
        except (PeerIdInvalid, ChatIdInvalid):
            return 400, f"{chat_id} : chat id invalid\n"
        except Exception:
            return 500, f"{chat_id} : {traceback.format_exc()}\n"


async def update_group_progress(progress_msg, total, done, success, failed, start_time):
    elapsed = datetime.timedelta(seconds=int(time.time() - start_time))
    pct = (done / total * 100) if total else 100.0
    text = (
        f"📢 Group Broadcast in Progress...\n\n"
        f"Total Chats: {total}\n"
        f"Completed: {done} ({pct:.1f}%)\n"
        f"Success: {success}\n"
        f"Failed: {failed}\n"
        f"Elapsed Time: {elapsed}"
    )
    try:
        await progress_msg.edit_text(text)
    except MessageNotModified:
        pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception:
        pass


async def group_broadcast(m, db):
    """Broadcast the replied-to message to every registered group/channel."""
    broadcast_msg = m.reply_to_message
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    while True:
        broadcast_id = "".join([random.choice(string.ascii_letters) for i in range(3)])
        if not group_broadcast_ids.get(broadcast_id):
            break

    out = await m.reply_text(
        text="Group Broadcast Started! You will get a log file when it finishes."
    )
    start_time = time.time()

    all_groups_cursor = await db.get_all_groups()
    all_groups = await all_groups_cursor.to_list(length=None)
    total_chats = len(all_groups)

    if total_chats == 0:
        await out.delete()
        await m.reply_text(
            "⚠️ No groups/channels registered yet.\n\n"
            "Add me to a group (I register myself automatically) "
            "or use `/addgroup <chat_id>`.",
            quote=True,
        )
        return

    done = failed = success = 0
    group_broadcast_ids[broadcast_id] = dict(
        total=total_chats, current=done, failed=failed, success=success
    )

    progress_msg = await m.reply_text(
        f"📢 Group Broadcast in Progress...\n\n"
        f"Total Chats: {total_chats}\n"
        f"Completed: 0 (0.0%)\n"
        f"Success: 0\n"
        f"Failed: 0\n"
        f"Elapsed Time: 0:00:00"
    )

    async def process_chat(group):
        sts, msg = await send_to_chat(
            chat_id=int(group["chat_id"]), message=broadcast_msg, semaphore=semaphore
        )
        return sts, msg, group["chat_id"]

    async with aiofiles.open("group_broadcast.txt", "w") as broadcast_log_file:
        tasks = [process_chat(group) for group in all_groups]
        last_update = time.time()

        for completed_task in asyncio.as_completed(tasks):
            sts, msg, chat_id = await completed_task

            if msg is not None:
                await broadcast_log_file.write(msg)

            if sts == 200:
                success += 1
            else:
                failed += 1

            # 400 -> chat is gone, stop targeting it
            if sts == 400:
                await db.set_group_active(chat_id, False)

            done += 1

            if group_broadcast_ids.get(broadcast_id) is None:
                break
            else:
                group_broadcast_ids[broadcast_id].update(
                    dict(current=done, failed=failed, success=success)
                )

            current_time = time.time()
            if current_time - last_update >= UPDATE_INTERVAL:
                await update_group_progress(
                    progress_msg, total_chats, done, success, failed, start_time
                )
                last_update = current_time

    if group_broadcast_ids.get(broadcast_id):
        group_broadcast_ids.pop(broadcast_id)

    await update_group_progress(
        progress_msg, total_chats, done, success, failed, start_time
    )

    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(2)
    await out.delete()

    if failed == 0:
        await progress_msg.edit_text(
            text=f"✅ Group Broadcast Completed in `{completed_in}`\n\n"
                 f"Total Chats: {total_chats}\n"
                 f"Total Done: {done}, {success} Success, {failed} Failed"
        )
    else:
        await progress_msg.delete()
        await m.reply_document(
            document="group_broadcast.txt",
            caption=f"✅ Group Broadcast Completed in `{completed_in}`\n\n"
                    f"Total Chats: {total_chats}\n"
                    f"Total Done: {done}, {success} Success, {failed} Failed",
            quote=True,
        )

    if os.path.exists("group_broadcast.txt"):
        os.remove("group_broadcast.txt")
