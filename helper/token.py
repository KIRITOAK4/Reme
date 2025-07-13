import os
import asyncio
import uuid
import aiohttp
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db
from Krito import BOT_NAME, ADMIN, TOKEN_TIMEOUT, SP_USERS, TUTORIAL_URL, SHORT_URL, MAX_SPACE, USE_VERCEL_QUIZ, pbot
from shortener import shorten_url

IST = timezone("Asia/Kolkata")  # Set to Indian Standard Time

def get_last_reset_time(token_timeout):
    now = datetime.now(IST)
    hour, minute = map(int, token_timeout.split(":"))
    reset_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if now < reset_time:
        reset_time -= timedelta(days=1)
    return reset_time

async def get_vercel_quiz_url(final_url: str) -> str:
    if not USE_VERCEL_QUIZ:
        return final_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://validate-user-tan.vercel.app/api/store-token",
                json={"url": final_url}
            ) as resp:
                data = await resp.json()
                token = data.get("token")
                if token:
                    return f"https://validate-user-tan.vercel.app/?token={token}"
    except Exception as e:
        print(f"[get_vercel_quiz_url] Error: {e}")

    return final_url

async def generate_buttons(new_token: str):
    final_url = shorten_url(f'https://telegram.me/{BOT_NAME}?start={new_token}')
    vercel_url = await get_vercel_quiz_url(final_url)

    buttons = []
    if TUTORIAL_URL:
        buttons.append([InlineKeyboardButton("📘 Tutorial", url=TUTORIAL_URL)])
    if SHORT_URL:
        buttons.append([InlineKeyboardButton("🔗 URL", url=SHORT_URL)])

    buttons.append([InlineKeyboardButton("🔄 Refresh Token", url=vercel_url)])
    return buttons

async def validate_user(message, button=None):
    try:
        if TOKEN_TIMEOUT in ["None", ""]:
            return None, None

        userid = message.from_user.id
        if userid in ADMIN or userid in SP_USERS:
            return None, None

        token, expire = await db.get_token_and_time(userid)
        reset_time = get_last_reset_time(TOKEN_TIMEOUT)
        now = datetime.now(IST)

        if expire is None:
            is_expired = True
        else:
            token_time = datetime.fromtimestamp(float(expire), IST)
            is_expired = token_time < reset_time

        if token is None or is_expired:
            new_token = token if (expire is None and token) else str(uuid.uuid4())
            if expire is not None:
                await db.remove_time_field(userid)
            await db.set_token(userid, new_token)

            if button is None:
                button = await generate_buttons(new_token)

            error_msg = '⚠️ Your token has expired. Please refresh your token to continue.'
            return error_msg, button

        return None, None

    except Exception as e:
        return f"An unexpected error occurred: {e}", button

async def check_user_limit(user_id):
    filled_time = await db.get_filled_time(user_id)
    if filled_time:
        filled_dt = datetime.fromisoformat(filled_time).astimezone(IST)
        now_dt = datetime.now(IST)
        # Optional 24-hour lockout (commented out)
        # if datetime.now(IST) - filled_dt < timedelta(days=1):
        #     return False
        if filled_dt.date() == now_dt.date():
            return False
        await db.reset_filled_time(user_id)
        await db.set_space_used(user_id, 0)
    return True

@pbot.on_message(filters.command("sing") & filters.private)
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
