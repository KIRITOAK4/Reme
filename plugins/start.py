import logging
import random
import asyncio
from time import time
from uuid import uuid4
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from helper.database import db
from Krito import pbot, MAX_PAGE
from helper.function import get_page_gif, get_page_caption, get_inline_keyboard

# Setup logging
logging.basicConfig(level=logging.INFO, filename="start_errors.log")
logger = logging.getLogger("StartHandler")

@pbot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    try:
        user_id = message.from_user.id
        user_details = {
            "id": user_id,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username,
            "mention": message.from_user.mention,
        }

        # Check if user exists in the database, else add
        if not await db.is_user_exist(user_id):
            await db.add_user(client, message)

        # Token processing (if provided)
        if len(message.command) > 1:
            input_token = message.command[1]
            stored_token, stored_time = await db.get_token_and_time(user_id)

            if stored_token != input_token:
                await message.reply_video(
                    video="https://graph.org/file/f6e6beb62a16a46642fb4.mp4",
                    caption="**Token is either used or invalid.**",
                    supports_streaming=True,
                )
                return
                
            await db.set_token(user_id, str(uuid4()))
            await db.set_time(user_id, time())
            await message.reply_text("Thanks for your support!")
            return

        # Default start message (Page 1)
        page_number = 1
        caption = get_page_caption(page_number, **user_details)
        inline_keyboard = get_inline_keyboard(page_number)

        await message.reply_video(
            video=get_page_gif(),
            caption=caption,
            supports_streaming=True,
            reply_markup=InlineKeyboardMarkup(inline_keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error in start command: {e}")

@pbot.on_callback_query(filters.regex(r"^(previous|next):\d+$"))
async def callback_query(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data.split(":")  # Example: "next:2" or "previous:3"
        
        action = data[0]
        current_page = int(data[1])

        if action == "previous":
            new_page = max(1, current_page - 1)
        elif action == "next":
            new_page = min(MAX_PAGE, current_page + 1)
        else:
            return  # Invalid action

        # Get user details for caption
        user_details = {
            "id": user_id,
            "first_name": callback_query.from_user.first_name,
            "last_name": callback_query.from_user.last_name,
            "username": callback_query.from_user.username,
            "mention": callback_query.from_user.mention,
        }

        # Update caption and buttons (GIF remains unchanged)
        caption = get_page_caption(new_page, **user_details)
        inline_keyboard = get_inline_keyboard(new_page)

        await callback_query.message.edit_caption(
            caption=caption, 
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )

    except Exception as e:
        logger.error(f"Error in callback_query: {e}")
        
