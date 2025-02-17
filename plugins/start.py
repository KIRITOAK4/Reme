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
logging.basicConfig(level=logging.DEBUG, filename="start_callback_errors.log", filemode="w",
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("StartCallbackHandler")

# Dictionary to track user pages (resets on bot restart)
user_pages = {}

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

        logger.debug(f"User {user_id} triggered /start. Details: {user_details}")

        if not await db.is_user_exist(user_id):
            await db.add_user(client, message)
            logger.debug(f"New user added: {user_id}")

        if len(message.command) > 1:
            input_token = message.command[1]
            stored_token, stored_time = await db.get_token_and_time(user_id)

            if stored_token != input_token:
                logger.warning(f"Invalid token attempt by user {user_id}. Input: {input_token}, Stored: {stored_token}")
                await message.reply_video(
                    video="https://graph.org/file/f6e6beb62a16a46642fb4.mp4",
                    caption="**Token is either used or invalid.**",
                    supports_streaming=True,
                )
                return
                
            await db.set_token(user_id, str(uuid4()))
            await db.set_time(user_id, time())
            logger.debug(f"User {user_id} updated token and time.")

            await message.reply_text("Thanks for your support!")
            return

        # Start from page 1
        user_pages[user_id] = 1
        page_number = 1

        logger.debug(f"User {user_id} set to page {page_number}")

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
        logger.error(f"Error in start command for user {user_id}: {e}", exc_info=True)

@pbot.on_callback_query(filters.regex(r"^(previous|next)$"))
async def callback_query(client, callback_query):
    try:
        user_id = callback_query.from_user.id
        current_page = user_pages.get(user_id, 1)  # Default to page 1 if not found

        logger.debug(f"User {user_id} is on page {current_page}. Action: {callback_query.data}")

        if callback_query.data == "previous":
            new_page = max(1, current_page - 1)
        elif callback_query.data == "next":
            new_page = min(MAX_PAGE, current_page + 1)
        else:
            logger.warning(f"Invalid callback data from user {user_id}: {callback_query.data}")
            return  # Invalid action

        # Update user’s page number
        user_pages[user_id] = new_page

        logger.debug(f"User {user_id} navigated to page {new_page}")

        user_details = {
            "id": user_id,
            "first_name": callback_query.from_user.first_name,
            "last_name": callback_query.from_user.last_name,
            "username": callback_query.from_user.username,
            "mention": callback_query.from_user.mention,
        }

        caption = get_page_caption(new_page, **user_details)
        inline_keyboard = get_inline_keyboard(new_page)

        await callback_query.message.edit_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )

    except Exception as e:
        logger.error(f"Error in callback_query for user {user_id}: {e}", exc_info=True)
        
