import logging
from time import time
from uuid import uuid4
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup
from Krito import pbot, MAX_PAGE
from helper.database import db
from helper.function import get_page_gif, get_page_caption, get_inline_keyboard

logging.basicConfig(level=logging.INFO, filename="start_callback_errors.log")
logger = logging.getLogger("StartCallbackHandler")

user_pages = {}

@pbot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id

    user_details = {
        "id": user_id,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "username": message.from_user.username,
        "mention": message.from_user.mention,
    }

    try:
        if not await db.is_user_exist(user_id):
            await db.add_user(client, message)

        # Token-based logic
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

        # Initial start page
        page_number = 1
        user_pages[user_id] = page_number
        caption = get_page_caption(page_number, **user_details)
        keyboard = InlineKeyboardMarkup(get_inline_keyboard(page_number))

        await message.reply_video(
            video=get_page_gif(),
            caption=caption,
            supports_streaming=True,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.exception("Error in /start command")

@pbot.on_callback_query(filters.regex(r"^(previous|next)$"))
async def handle_navigation(client, cq):
    user_id = cq.from_user.id
    current_page = user_pages.get(user_id, 1)

    try:
        if cq.data == "previous":
            new_page = max(1, current_page - 1)
        else:  # "next"
            new_page = min(MAX_PAGE, current_page + 1)

        user_pages[user_id] = new_page

        user_details = {
            "id": user_id,
            "first_name": cq.from_user.first_name,
            "last_name": cq.from_user.last_name,
            "username": cq.from_user.username,
            "mention": cq.from_user.mention,
        }

        caption = get_page_caption(new_page, **user_details)
        keyboard = InlineKeyboardMarkup(get_inline_keyboard(new_page))

        await cq.message.edit_caption(caption, reply_markup=keyboard)

    except Exception as e:
        logger.exception("Error handling page navigation")
