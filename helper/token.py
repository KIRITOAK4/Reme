import os
import asyncio
import uuid
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram.types import InlineKeyboardButton
from helper.database import db
from Krito import BOT_NAME, ADMIN, TOKEN_TIMEOUT, SP_USERS, TUTORIAL_URL, SHORT_URL, MAX_SPACE
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
        is_expired = (expire is None or now >= reset_time)

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

def get_next_reset_time(token_timeout):
    """Parses time format 'HH:MM' and returns the next reset datetime."""
    now = datetime.now(IST)    
    try:
        hour, minute = map(int, token_timeout.split(":"))
        reset_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now >= reset_time:
            reset_time += timedelta(days=1)
        return reset_time
    except ValueError:
        raise ValueError("Invalid TOKEN_TIMEOUT format. Use 'HH:MM' (e.g., '07:08').")

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
    """
    Check if the user is blocked due to space limit.
    Reset block if a new calendar day has started.
    """
    filled_time = await db.get_filled_time(user_id)
    if filled_time:
        filled_dt = datetime.fromisoformat(filled_time).astimezone(IST)
        # Switched from 24-hour lockout to calendar day-based reset
        # if datetime.now(IST) - filled_dt < timedelta(days=1):
        #     return False  # still blocked (24-hour lockout - now removed)
        if filled_dt.date() == datetime.now(IST).date():
            return False
        await db.reset_filled_time(user_id)
        await db.set_space_used(user_id, 0)
    return True
