# Broadcast Bot v2
A simple Telegram bot that can broadcast messages and media to the bot subscribers using [MongoDB](https://mongodb.com).  

[![Readme Card](https://github-readme-stats.vercel.app/api/pin/?username=NACBots&repo=BroadcastBot&theme=flag-india)](https://github.com/nacbots/broadcastbot&bg_color=#24292F)  

## 🚀 What's New in v2?  
- **15x Faster Broadcasts** – Implemented **semaphore**, making message delivery significantly faster!  
- **Live Broadcast Status** – Real-time progress updates to track your broadcasts.  
- **PyroBlack Migration** – Switched from **Pyrogram** to **PyroBlack** for improved performance and efficiency.  
- **New Config Variables:**  
  - `MAX_CONCURRENT` – Maximum concurrent message sends (Default: 15, can be set up to 1000 for paid broadcasts).  
  - `UPDATE_INTERVAL` – Update interval in seconds to avoid flood waits (Default: 2).  

## Features  

- Supports [MongoDB](https://mongodb.com) database 💁 for user records 📽.  
- Users can choose whether to enable broadcast messages using `/settings` command.  
- Logs new users in a specified channel.  
- Get total user count from the database.  
- Ban and unban users.  

## Required Configs  

- `BOT_TOKEN` - Get from [@BotFather](https://t.me/BotFather)  
- `API_ID` - Get it from [telegram.org](https://my.telegram.org/auth)  
- `API_HASH` - Get it from [telegram.org](https://my.telegram.org/auth)  
- `AUTH_USERS` - Authorized user IDs for [Admin Commands](https://github.com/nacbots/broadcastbot#admin-commands) (separated by spaces).  
- `DB_URL` - MongoDB Database URI from [mongodb.com](https://mongodb.com)  

## Optional Configs  

- `LOG_CHANNEL` - Channel ID to log new user notifications.  
- `BROADCAST_AS_COPY` - Set to `True` for copy-forwarded messages, `False` for forwarded messages with a tag.  
- `DB_NAME` - Collection name in MongoDB.  
- `MAX_CONCURRENT` - Maximum concurrent message sends (Default: 15, can be set up to 2000).  
- `UPDATE_INTERVAL` - Update interval in seconds to avoid flood waits (Default: 2).  

## User Commands 🤔  

```
start - Start the bot 🥲  
settings - Customize settings  
```

## Admin Commands 🤫  

```
stats - Get total user count in the database  
broadcast - Reply to a message to broadcast  
ban_user - Ban a user with time & reason  
unban_user - Unban a user  
banned_users - Show banned users  
```

## Deploy 🚀  

### Easiest Heroku Deploy 🤭  

<p align="center">  
    <a href="https://heroku.com/deploy?template=https://github.com/nacbots/BroadcastBot">  
    <img src="https://github.com/nacbots/broadcastbot/blob/main/herokudeploy-01.svg" alt="herokudeploy-01" border="0" height="90" width="285"></a>  
</p>  

### Host Locally 🤕  

```shell
git clone https://github.com/nacbots/BroadcastBot  
cd BroadcastBot  
pip3 install -r requirements.txt  
# EDIT config.py values appropriately  
python3 main.py  
```

## Support Group  

<a href="https://t.me/NACBots"><img src="https://img.shields.io/badge/Telegram-Updates%20Channel-blue.svg?logo=telegram"></a>  
<a href="https://t.me/n_a_c_bot_developers"><img src="https://img.shields.io/badge/Telegram-Support%20Group-blue.svg?logo=telegram"></a>  

## Found a Bug? 🐛  

```Feel free to create a pull request or open an issue and describe your problem freely.```  

## Credits  

- [@NikhilEashy](https://github.com/nikhileashy)  
- [@MrBotDeveloper](https://github.com/MrBotDeveloper)  

<a href="https://pyrogram.org"><img src="https://i.ibb.co/SVLD5k8/Document-1222546317.png" alt="pyrogram" border="0"></a>  

