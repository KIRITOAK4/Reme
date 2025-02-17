import asyncio
import logging
from time import time
from uuid import uuid4
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, CallbackQuery
from pyrogram.enums import ParseMode
from helper.database import db
from Krito import pbot, MAX_PAGE
from helper.function import get_page_gif, get_page_caption, get_inline_keyboard

# Setup logging
logging.basicConfig(level=logging.INFO, filename="start_callback_errors.log")
logger = logging.getLogger("StartCallbackHandler")

# Dictionary to track user pages
user_pages = {}

@pbot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    try:
        print("/start command received")  # Debug
        user_id = message.from_user.id
        print(f"User ID: {user_id}")  # Debug

        user_details = {
            "id": user_id,
            "first_name": message.from_user.first_name,
            "last_name": message.from_user.last_name,
            "username": message.from_user.username,
            "mention": message.from_user.mention,
        }
        print(f"User Details: {user_details}")  # Debug

        if not await db.is_user_exist(user_id):
            print("User does not exist, adding to database.")  # Debug
            await db.add_user(client, message)
        else:
            print("User already exists in database.")  # Debug

        if len(message.command) > 1:
            input_token = message.command[1]
            stored_token, stored_time = await db.get_token_and_time(user_id)
            print(f"Received Token: {input_token}, Stored Token: {stored_token}")  # Debug

            if stored_token != input_token:
                print("Invalid token, sending error message.")  # Debug
                await message.reply_video(
                    video="https://graph.org/file/f6e6beb62a16a46642fb4.mp4",
                    caption="**Token is either used or invalid.**",
                    supports_streaming=True,
                )
                return
            
            print("Valid token, updating token and time.")  # Debug
            await db.set_token(user_id, str(uuid4()))
            await db.set_time(user_id, time())
            await message.reply_text("Thanks for your support!")
            return

        # Start from page 1
        user_pages[user_id] = 1
        page_number = 1
        print(f"Starting user {user_id} at page {page_number}")  # Debug

        caption = get_page_caption(page_number, **user_details)
        print(f"caption problem: {caption}")
        inline_keyboard = get_inline_keyboard(page_number)
        print(f"inline problem: {inline_keyboard}")

        await message.reply_video(
            video=get_page_gif(),
            caption=caption,
            supports_streaming=True,
            reply_markup=InlineKeyboardMarkup(inline_keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        print(f"Error in start command: {e}")  # Debug

@pbot.on_callback_query(filters.regex(r"^(previous|next)$"))
async def callback_query(client, callback_query):
    try:
        print("Callback query received")  # Debug
        user_id = callback_query.from_user.id
        print(f"User ID: {user_id}")  # Debug

        current_page = user_pages.get(user_id, 1)
        print(f"Current Page: {current_page}")  # Debug

        if callback_query.data == "previous":
            page_number = max(1, current_page - 1)
            print(f"Navigating to previous page: {new_page}")  # Debug
        elif callback_query.data == "next":
            page_number = min(MAX_PAGE, current_page + 1)
            print(f"Navigating to next page: {new_page}")  # Debug
        else:
            print("Invalid callback data received")  # Debug
            return

        user_pages[user_id] = page_number
        print(f"Updated user {user_id} to page {new_page}")  # Debug

        user_details = {
            "id": user_id,
            "first_name": callback_query.from_user.first_name,
            "last_name": callback_query.from_user.last_name,
            "username": callback_query.from_user.username,
            "mention": callback_query.from_user.mention,
        }
        print(f"User Details: {user_details}")  # Debug

        caption = get_page_caption(page_number, **user_details)
        print(f"caption problem: {caption}")
        inline_keyboard = get_inline_keyboard(page_number)
        print(f"inline problem: {inline_keyboard}")

        await callback_query.message.edit_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )
    except Exception as e:
        logger.error(f"Error in callback_query: {e}")
        print(f"Error in callback_query: {e}")  # Debug
