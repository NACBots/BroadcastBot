import os
import traceback
import logging

from pyrogram import Client
from pyrogram import StopPropagation, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
from handlers.broadcast import broadcast
from handlers.check_user import handle_user_status
from handlers.database import Database
from handlers.group_broadcast import group_broadcast

LOG_CHANNEL = config.LOG_CHANNEL
AUTH_USERS = config.AUTH_USERS
DB_URL = config.DB_URL
DB_NAME = config.DB_NAME

db = Database(DB_URL, DB_NAME)


Bot = Client(
    "BroadcastBot",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
)

@Bot.on_message(filters.private)
async def _(bot, cmd):
    await handle_user_status(bot, cmd)

@Bot.on_message(filters.command("start") & filters.private)
async def startprivate(client, message):
    # return
    chat_id = message.from_user.id
    if not await db.is_user_exist(chat_id):
        data = await client.get_me()
        BOT_USERNAME = data.username
        await db.add_user(chat_id)
        if LOG_CHANNEL:
            await client.send_message(
                LOG_CHANNEL,
                f"#NEWUSER: \n\nNew User [{message.from_user.first_name}](tg://user?id={message.from_user.id}) started @{BOT_USERNAME} !!",
            )
        else:
            logging.info(f"#NewUser :- Name : {message.from_user.first_name} ID : {message.from_user.id}")
    joinButton = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("CHANNEL", url="https://t.me/nacbots"),
                InlineKeyboardButton(
                    "SUPPORT GROUP", url="https://t.me/n_a_c_bot_developers"
                ),
            ]
        ]
    )
    welcomed = f"Hey <b>{message.from_user.first_name}</b>\nI'm a Telegram bot that can broadcast messages and media to bot subscribers <b>and</b> to multiple groups/channels.\n\n 🎚 use /settings\n 📣 /broadcast — send to all <b>users</b>\n 📢 /gbroadcast — send to all <b>groups</b>\n 🗂 /groups — list target groups"
    await message.reply_text(welcomed, reply_markup=joinButton)
    raise StopPropagation


@Bot.on_message(filters.command("settings"))
async def opensettings(bot, cmd):
    user_id = cmd.from_user.id
    await cmd.reply_text(
        f"`Here You Can Set Your Settings:`\n\nSuccessfully setted notifications to **{await db.get_notif(user_id)}**",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"NOTIFICATION  {'🔔' if ((await db.get_notif(user_id)) is True) else '🔕'}",
                        callback_data="notifon",
                    )
                ],
                [InlineKeyboardButton("❎", callback_data="closeMeh")],
            ]
        ),
    )


@Bot.on_message(filters.private & filters.command("broadcast"))
async def broadcast_handler_open(_, m):
    if m.from_user.id not in AUTH_USERS:
        print("Not Authorized")
        await m.delete()
        return
    if m.reply_to_message is None:
        await m.reply_text(
            "Reply to a message to broadcast it to all subscribers", quote=True
        )
        await m.delete()
    else:
        await broadcast(m, db)


@Bot.on_message(filters.private & filters.command("stats"))
async def sts(c, m):
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return
    await m.reply_text(
        text=f"**Total Users in Database 📂:** `{await db.total_users_count()}`\n\n"
             f"**Total Users with Notification Enabled 🔔 :** `{await db.total_notif_users_count()}`\n\n"
             f"**Total Groups/Channels Registered 🗂 :** `{await db.total_groups_count()}`",
        quote=True
    )


# ---------------------------------------------------------------------------
# Multi-group / multi-channel broadcasting
# ---------------------------------------------------------------------------


@Bot.on_message(filters.command("addgroup"))
async def addgroup_handler(_, m):
    """Register a group/channel as a broadcast target.

    Works both in private (`/addgroup -1001234567890`) and inside a group
    (just send `/addgroup` there).
    """
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return

    if m.chat.type in ("group", "supergroup", "channel"):
        chat = m.chat
    elif len(m.command) > 1:
        chat_id = m.command[1]
        try:
            chat = await _.get_chat(chat_id)
        except Exception:
            await m.reply_text(
                f"⚠️ Cannot resolve chat `{chat_id}`.\n"
                f"`{traceback.format_exc()}`",
                quote=True,
            )
            return
    else:
        await m.reply_text(
            "Usage:\n\n"
            "• Inside a group: just send `/addgroup`\n"
            "• In private: `/addgroup <chat_id>` (e.g. `/addgroup -1001234567890`)",
            quote=True,
        )
        return

    await db.add_group(
        chat_id=chat.id,
        title=getattr(chat, "title", "") or "",
        username=getattr(chat, "username", "") or "",
        chat_type=str(chat.type),
    )
    await m.reply_text(
        f"✅ Registered for broadcast:\n\n"
        f"**Title:** {getattr(chat, 'title', chat.id)}\n"
        f"**Chat ID:** `{chat.id}`\n"
        f"**Type:** `{chat.type}`\n\n"
        f"Total targets: `{await db.total_groups_count()}`",
        quote=True,
    )


@Bot.on_message(filters.command("delgroup"))
async def delgroup_handler(_, m):
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return

    if m.chat.type in ("group", "supergroup", "channel"):
        chat_id = m.chat.id
    elif len(m.command) > 1:
        try:
            chat_id = int(m.command[1])
        except ValueError:
            await m.reply_text("⚠️ chat_id must be a number.", quote=True)
            return
    else:
        await m.reply_text(
            "Usage:\n\n• Inside a group: `/delgroup`\n• In private: `/delgroup <chat_id>`",
            quote=True,
        )
        return

    await db.delete_group(chat_id)
    await m.reply_text(
        f"🗑 Removed `{chat_id}` from broadcast targets.\n"
        f"Remaining targets: `{await db.total_groups_count()}`",
        quote=True,
    )


@Bot.on_message(filters.command("groups"))
async def groups_handler(_, m):
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return

    cursor = await db.get_all_groups()
    groups = await cursor.to_list(length=None)
    if not groups:
        await m.reply_text(
            "No group/channel registered yet.\n\n"
            "Add the bot to a group (it auto-registers) or use `/addgroup`.",
            quote=True,
        )
        return

    lines = []
    for i, g in enumerate(groups, 1):
        title = g.get("title") or "(no title)"
        username = f" @{g['username']}" if g.get("username") else ""
        lines.append(f"{i}. {title}{username}\n    `{g['chat_id']}` · {g.get('chat_type')}")

    await m.reply_text(
        f"**🗂 Broadcast targets ({len(groups)}):**\n\n" + "\n".join(lines),
        quote=True,
    )


@Bot.on_message(filters.command("gbroadcast"))
async def gbroadcast_handler(_, m):
    """Broadcast the replied-to message to every registered group/channel."""
    if m.from_user.id not in AUTH_USERS:
        try:
            await m.delete()
        except Exception:
            pass
        return

    if m.reply_to_message is None:
        await m.reply_text(
            "Reply to a message with `/gbroadcast` to send it to **all registered "
            "groups/channels**.\n\n"
            f"Current targets: `{await db.total_groups_count()}`\n"
            "Manage them with `/addgroup`, `/delgroup`, `/groups`.",
            quote=True,
        )
        return

    await group_broadcast(m, db)


@Bot.on_message(filters.new_chat_members)
async def auto_register_group(_, m):
    """Auto-register any group/channel the bot itself is added to."""
    me = await _.get_me()
    for member in m.new_chat_members:
        if member.id == me.id:
            chat = m.chat
            await db.add_group(
                chat_id=chat.id,
                title=getattr(chat, "title", "") or "",
                username=getattr(chat, "username", "") or "",
                chat_type=str(chat.type),
            )
            try:
                await m.reply_text(
                    f"✅ Thanks for adding me! This chat is now a broadcast target "
                    f"(`{chat.id}`).\n\n"
                    f"Admins can use `/gbroadcast` (reply to a message) to push "
                    f"content here and to every other registered group."
                )
            except Exception:
                pass
            break


@Bot.on_message(filters.left_chat_member)
async def auto_unregister_group(_, m):
    """Deactivate a chat once the bot is removed from it."""
    me = await _.get_me()
    if m.left_chat_member and m.left_chat_member.id == me.id:
        await db.set_group_active(m.chat.id, False)


@Bot.on_message(filters.private & filters.command("ban_user"))
async def ban(c, m):
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return
    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to ban 🛑 any user from the bot 🤖.\n\nUsage:\n\n`/ban_user user_id ban_duration ban_reason`\n\nEg: `/ban_user 1234567 28 You misused me.`\n This will ban user with id `1234567` for `28` days for the reason `You misused me`.",
            quote=True,
        )
        return

    try:
        user_id = int(m.command[1])
        ban_duration = int(m.command[2])
        ban_reason = " ".join(m.command[3:])
        ban_log_text = f"Banning user {user_id} for {ban_duration} days for the reason {ban_reason}."

        try:
            await c.send_message(
                user_id,
                f"You are Banned 🚫 to use this bot for **{ban_duration}** day(s) for the reason __{ban_reason}__ \n\n**Message from the admin 🤠**",
            )
            ban_log_text += "\n\nUser notified successfully!"
        except BaseException:
            traceback.print_exc()
            ban_log_text += (
                f"\n\n ⚠️ User notification failed! ⚠️ \n\n`{traceback.format_exc()}`"
            )
        await db.ban_user(user_id, ban_duration, ban_reason)
        print(ban_log_text)
        await m.reply_text(ban_log_text, quote=True)
    except BaseException:
        traceback.print_exc()
        await m.reply_text(
            f"Error occoured ⚠️! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Bot.on_message(filters.private & filters.command("unban_user"))
async def unban(c, m):
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return
    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to unban 😃 any user.\n\nUsage:\n\n`/unban_user user_id`\n\nEg: `/unban_user 1234567`\n This will unban user with id `1234567`.",
            quote=True,
        )
        return

    try:
        user_id = int(m.command[1])
        unban_log_text = f"Unbanning user 🤪 {user_id}"

        try:
            await c.send_message(user_id, f"Your ban was lifted!")
            unban_log_text += "\n\n✅ User notified successfully! ✅"
        except BaseException:
            traceback.print_exc()
            unban_log_text += (
                f"\n\n⚠️ User notification failed! ⚠️\n\n`{traceback.format_exc()}`"
            )
        await db.remove_ban(user_id)
        print(unban_log_text)
        await m.reply_text(unban_log_text, quote=True)
    except BaseException:
        traceback.print_exc()
        await m.reply_text(
            f"⚠️ Error occoured ⚠️! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True,
        )


@Bot.on_message(filters.private & filters.command("banned_users"))
async def _banned_usrs(c, m):
    if m.from_user.id not in AUTH_USERS:
        await m.delete()
        return
    all_banned_users = await db.get_all_banned_users()
    banned_usr_count = 0
    text = ""
    async for banned_user in all_banned_users:
        user_id = banned_user["id"]
        ban_duration = banned_user["ban_status"]["ban_duration"]
        banned_on = banned_user["ban_status"]["banned_on"]
        ban_reason = banned_user["ban_status"]["ban_reason"]
        banned_usr_count += 1
        text += f"> **User_id**: `{user_id}`, **Ban Duration**: `{ban_duration}`, **Banned on**: `{banned_on}`, **Reason**: `{ban_reason}`\n\n"
    reply_text = f"Total banned user(s) 🤭: `{banned_usr_count}`\n\n{text}"
    if len(reply_text) > 4096:
        with open("banned-users.txt", "w") as f:
            f.write(reply_text)
        await m.reply_document("banned-users.txt", True)
        os.remove("banned-users.txt")
        return
    await m.reply_text(reply_text, True)


@Bot.on_callback_query()
async def callback_handlers(bot: Client, cb: CallbackQuery):
    user_id = cb.from_user.id
    if cb.data == "notifon":
        notif = await db.get_notif(cb.from_user.id)
        if notif is True:
            await db.set_notif(user_id, notif=False)
        else:
            await db.set_notif(user_id, notif=True)
        await cb.message.edit(
            f"`Here You Can Set Your Settings:`\n\nSuccessfully setted notifications to **{await db.get_notif(user_id)}**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"NOTIFICATION  {'🔔' if ((await db.get_notif(user_id)) is True) else '🔕'}",
                            callback_data="notifon",
                        )
                    ],
                    [InlineKeyboardButton("❎", callback_data="closeMeh")],
                ]
            ),
        )
        await cb.answer(
            f"Successfully setted notifications to {await db.get_notif(user_id)}"
        )
    else:
        await cb.message.delete(True)

print("Bot Started...")
Bot.run()
