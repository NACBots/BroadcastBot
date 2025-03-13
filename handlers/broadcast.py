# (c) N A C BOTS

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
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
    MessageNotModified,
)

import config

broadcast_ids = {}

BROADCAST_AS_COPY = config.BROADCAST_AS_COPY
MAX_CONCURRENT = config.MAX_CONCURRENT
UPDATE_INTERVAL = config.UPDATE_INTERVAL

async def send_msg(user_id, message, semaphore):
    async with semaphore:
        try:
            if BROADCAST_AS_COPY is False:
                await message.forward(chat_id=user_id)
            elif BROADCAST_AS_COPY is True:
                await message.copy(chat_id=user_id)
            return 200, None
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await send_msg(user_id, message, semaphore)
        except InputUserDeactivated:
            return 400, f"{user_id} : deactivated\n"
        except UserIsBlocked:
            return 400, f"{user_id} : blocked the bot\n"
        except PeerIdInvalid:
            return 400, f"{user_id} : user id invalid\n"
        except Exception as e:
            print(e)
            return 500, f"{user_id} : {traceback.format_exc()}\n"

async def update_progress_message(progress_msg, total, done, success, failed, start_time):
    elapsed = datetime.timedelta(seconds=int(time.time() - start_time))
    text = (
        f"📢 Broadcast in Progress...\n\n"
        f"Total Users: {total}\n"
        f"Completed: {done} ({(done/total)*100:.1f}%)\n"
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

async def broadcast(m, db):
    broadcast_msg = m.reply_to_message
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    
    while True:
        broadcast_id = "".join([random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break
    
    out = await m.reply_text(
        text=f"Broadcast Started! You will be notified with log file when all the users are notified."
    )
    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_users, current=done, failed=failed, success=success
    )

    progress_msg = await m.reply_text(
        f"📢 Broadcast in Progress...\n\n"
        f"Total Users: {total_users}\n"
        f"Completed: 0 (0.0%)\n"
        f"Success: 0\n"
        f"Failed: 0\n"
        f"Elapsed Time: 0:00:00"
    )

    async def process_user(user):
        nonlocal done, failed, success
        sts, msg = await send_msg(user_id=int(user["id"]), message=broadcast_msg, semaphore=semaphore)
        return sts, msg, user["id"]

    all_users_cursor = await db.get_all_notif_user()
    all_users = await all_users_cursor.to_list(length=None)
    
    async with aiofiles.open("broadcast.txt", "w") as broadcast_log_file:
        tasks = [process_user(user) for user in all_users]
        last_update = time.time()
        
        for completed_task in asyncio.as_completed(tasks):
            sts, msg, user_id = await completed_task
            
            if msg is not None:
                await broadcast_log_file.write(msg)
            
            if sts == 200:
                success += 1
            else:
                failed += 1
            
            if sts == 400:
                await db.delete_user(user_id)
            
            done += 1
            
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(current=done, failed=failed, success=success)
                )
            current_time = time.time()
            if current_time - last_update >= UPDATE_INTERVAL:
                await update_progress_message(progress_msg, total_users, done, success, failed, start_time)
                last_update = current_time

    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    await update_progress_message(progress_msg, total_users, done, success, failed, start_time)
    
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    
    if failed == 0:
        await progress_msg.edit_text(
            text=f"✅ Broadcast Completed in `{completed_in}`\n\n"
                 f"Total Users: {total_users}\n"
                 f"Total Done: {done}, {success} Success, {failed} Failed"
        )
    else:
        await progress_msg.delete()
        await m.reply_document(
            document="broadcast.txt",
            caption=f"✅ Broadcast Completed in `{completed_in}`\n\n"
                    f"Total Users: {total_users}\n"
                    f"Total Done: {done}, {success} Success, {failed} Failed",
            quote=True,
        )
    
    os.remove("broadcast.txt")
