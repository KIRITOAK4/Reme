import os
import re
import asyncio
from datetime import datetime
from pytz import timezone
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from helper.utils import humanbytes
from helper.database import db
from helper.token import validate_user, check_user_limit
from .chatid import get_chat_status
from helper.core.rename_function import handle_sample, handle_auto_rename, handle_rename
from Krito import ubot, pbot

async def extract_season_episode(filename):
    season, episode = None, None
    pattern1 = re.compile(r'[\[\(\{\<]?\s*S(\d+)(?:E|EP)(\d+)\s*[\]\)\}\>]?', re.IGNORECASE)
    pattern2 = re.compile(r'[\[\(\{\<]?\s*S(\d+)\s*(?:E|EP|-\s*EP)(\d+)\s*[\]\)\}\>]?', re.IGNORECASE)
    pattern3 = re.compile(r'[\[\(\{\<]?\s*(?:E|EP)\s*(\d+)\s*[\]\)\}\>]?', re.IGNORECASE)
    pattern3_2 = re.compile(r'\s*-\s*(\d+)\s*')
    pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
    patternX = re.compile(r'(\d+)')

    match = pattern1.search(filename) or pattern2.search(filename) or pattern4.search(filename) or pattern3.search(filename) or pattern3_2.search(filename)

    if match:
        groups = match.groups()
        if len(groups) == 2:
            season, episode = groups
        elif len(groups) == 1:
            episode = groups[0]
    else:
        episode_match = patternX.search(filename)
        if episode_match:
            episode = episode_match.group(1)

    cleaned_filename = filename
    if match:
        cleaned_filename = re.sub(re.escape(match.group(0)), "", filename).strip()
    elif episode:
        cleaned_filename = re.sub(re.escape(episode), "", cleaned_filename).strip()

    cleaned_filename = re.sub(r"[\s._-]+$", "", cleaned_filename).strip()
    base_name, _ = os.path.splitext(cleaned_filename)
    return season, episode, base_name

@pbot.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    """Handles the start of the renaming process by showing options."""
    user_id = message.from_user.id

    is_blocked = not await check_user_limit(user_id)
    if is_blocked:
        error_msg, button = await validate_user(message)
        if error_msg:
            await message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(button) if button else None)
            return

    file = getattr(message, message.media.value)
    filename = file.file_name
    filesize = humanbytes(file.file_size)

    try:
        text = f"""**__What do you want me to do with this file?__**\n\n**File Name** :- `{filename}`\n\n**File Size** :- `{filesize}`"""
        buttons = [
            [InlineKeyboardButton("📝 𝚂𝚃𝙰𝚁𝚃 𝚁𝙴𝙽𝙰𝙼𝙴 📝", callback_data="rename"),
             InlineKeyboardButton("🔄 𝙰𝚄𝚃𝙾 𝚁𝙴𝙽𝙰𝙼𝙴 🔄", callback_data="auto_rename")],
            [InlineKeyboardButton("📋 𝚂𝙰𝙼𝙿𝙻𝙴 📋", callback_data="sample")]
        ]

        await message.reply_text(text=text, reply_to_message_id=message.id, reply_markup=InlineKeyboardMarkup(buttons))
        await asyncio.sleep(1)  # Prevents flood wait issues

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_text(text=text, reply_to_message_id=message.id, reply_markup=InlineKeyboardMarkup(buttons))

@pbot.on_callback_query(filters.regex(r"^(rename|sample|auto_rename)"))
async def callback_handler(client, callback_query):
    """Routes callback data to the appropriate handler."""
    try:
        data = callback_query.data
        msg = callback_query.message
        replied = msg.reply_to_message

        if not replied:
            await callback_query.answer("Original file not found.", show_alert=True)
            return

        file = getattr(replied, replied.media.value, None)
        if not file or not file.file_name:
            await callback_query.answer("Invalid file or filename missing.", show_alert=True)
            return

        await msg.delete()

        if data == "sample":
            await handle_sample(client, callback_query, file, replied)
        elif data == "auto_rename":
            await handle_auto_rename(client, callback_query, file, replied)
        elif data == "rename":
            await handle_rename(client, callback_query, file, replied)

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        await callback_query.message.reply_text(f"❌ Callback error: {e}")
