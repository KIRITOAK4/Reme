import os
import asyncio
import uuid
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup
from pyrogram.types import InlineKeyboardButton
from helper.database import db
from Krito import BOT_NAME, ADMIN, TOKEN_TIMEOUT, SP_USERS, TUTORIAL_URL, SHORT_URL, MAX_SPACE, pbot
from shortener import shorten_url

IST = timezone("Asia/Kolkata")  # Set to Indian Standard Time

async def validate_user(message, button=None):
    try:
        if TOKEN_TIMEOUT in ["None", ""]:
            return None, None

        userid = message.from_user.id
        if userid in ADMIN or userid in SP_USERS:
            return None, None

        token, expire = await db.get_token_and_time(userid)
        reset_time = get_next_reset_time(TOKEN_TIMEOUT)
        now = datetime.now(IST)
        
        if expire is None:
            is_expired = True
        else:
            token_time = datetime.fromtimestamp(float(expire), IST)
            is_expired = token_time < reset_time

        if is_expired:
            new_token = token if (expire is None and token) else str(uuid.uuid4())
            if expire is not None:
                await db.remove_time_field(userid)
            await db.set_token(userid, new_token)

            if button is None:
                button = generate_buttons(new_token)

            error_msg = '⚠️ Your token has expired. Please refresh your token to continue.'
            return error_msg, button

        return None, None

    except Exception as e:
        return f"An unexpected error occurred: {e}", button

def get_last_reset_time(token_timeout):
    """Return the last daily reset time based on TOKEN_TIMEOUT (HH:MM)."""
    now = datetime.now(IST)
    hour, minute = map(int, token_timeout.split(":"))
    reset_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now < reset_time:
        reset_time -= timedelta(days=1)
    return reset_time
    
def generate_buttons(new_token):
    buttons = []
    if TUTORIAL_URL:
        buttons.append([InlineKeyboardButton(text='📘 Tutorial', url=TUTORIAL_URL)])
    if SHORT_URL:
        buttons.append([InlineKeyboardButton(text='🔗 URL', url=SHORT_URL)])
    buttons.append([
        InlineKeyboardButton(text='🔄 Refresh Token', url=shorten_url(f'https://telegram.me/{BOT_NAME}?start={new_token}')),
    ])
    return buttons  

async def check_user_limit(user_id):
    filled_time = await db.get_filled_time(user_id)
    if filled_time:
        filled_dt = datetime.fromisoformat(filled_time).astimezone(IST)
        # Optional 24-hour lockout (commented out)
        # if datetime.now(IST) - filled_dt < timedelta(days=1):
        #     return False
        if filled_dt.date() == datetime.now(IST).date():
            return False
        await db.reset_filled_time(user_id)
        await db.set_space_used(user_id, 0)
    return True

@pbot.on_message(filters.command("ping") & filters.private)
async def ping_command(client, message: Message):
    user_id = message.from_user.id
    error_msg, button = await validate_user(message)
    if error_msg:
        await message.reply_text(
            error_msg,
            reply_markup=InlineKeyboardMarkup(button) if button else None
        )
        return

    await message.reply_text("✅ Pong! You're verified.")
    
