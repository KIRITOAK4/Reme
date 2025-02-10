import os, random, asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaVideo, InputMediaAnimation
from helper.database import db
from Krito import pbot, ADMIN, MAX_PAGE
from pyrogram.enums import ParseMode
from helper.function import get_page_gif, get_page_caption, get_inline_keyboard
from time import time
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO, filename='start_callback_errors.log')
logger = logging.getLogger("StartCallbackHandler")
logger.setLevel(level=logging.INFO)

# Dictionary to store page numbers for users (updated within the callback function)
user_page_numbers = {}

@pbot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    try:
        userid = message.from_user.id
        if not await db.is_user_exist(userid):
            await db.add_user(client, message)
            
        if userid not in user_page_numbers:
            user_page_numbers[userid] = 1  # Initialize page number for the user
        page_number = user_page_numbers[userid]
        
        input_token = None
        if len(message.command) > 1:
            input_token = message.command[1]
        
        if input_token is not None:
            try:
                stored_token, stored_time = await db.get_token_and_time(userid)
                if stored_token != input_token:
                    gif_url = 'https://graph.org/file/f6e6beb62a16a46642fb4.mp4'
                    caption = '**Token is either used or invalid.**'
                    await message.reply_video(
                        video=gif_url,
                        caption=caption,
                        supports_streaming=True
                    )
                    return

                new_token = str(uuid4())
                new_time = time()
                await db.set_token(userid, new_token)
                await db.set_time(userid, new_time)
                await message.reply_text('Thanks for your support!')
            except Exception as e:
                error_text = f"Error: {e}"
                await message.reply_text(error_text, reply_to_message_id=message.id)
        else:
            user_details = {
                'id': message.from_user.id,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'username': message.from_user.username,
                'mention': message.from_user.mention
            }
            caption = get_page_caption(page_number, **user_details)
            inline_keyboard = get_inline_keyboard(page_number)
            reply_markup = InlineKeyboardMarkup(inline_keyboard)
            await message.reply_video(
                video=get_page_gif(page_number),
                caption=caption,
                supports_streaming=True,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )        
    except Exception as e:
        logger.error(f"An error occurred while executing start: {e}")

@pbot.on_callback_query(filters.regex(r"^(previous|next)$"))
async def callback_query(client, callback_query):
    try:
        user_id = callback_query.from_user.id  # user_id is already set here
        # We assume user_page_numbers[user_id] is initialized when the user starts the bot.

        user_details = {
            'id': user_id,
            'first_name': callback_query.from_user.first_name,
            'last_name': callback_query.from_user.last_name,
            'username': callback_query.from_user.username,
            'mention': callback_query.from_user.mention
        }

        data = callback_query.data
        if data == "previous":
            user_page_numbers[user_id] = max(1, user_page_numbers[user_id] - 1)
        elif data == "next":
            user_page_numbers[user_id] = min(MAX_PAGE, user_page_numbers[user_id] + 1)

        page_number = user_page_numbers[user_id]
        caption = get_page_caption(page_number, **user_details)
        inline_keyboard = get_inline_keyboard(page_number)
        video_path = get_page_gif(page_number)
        media_type = InputMediaVideo if video_path.endswith(".mp4") else InputMediaAnimation
        video = media_type(media=video_path, caption=caption)

        if callback_query.message.caption != caption or callback_query.message.reply_markup != InlineKeyboardMarkup(inline_keyboard):
            await callback_query.message.edit_caption(caption, reply_markup=InlineKeyboardMarkup(inline_keyboard))

        # Optionally update media
        # if video:
        #     await callback_query.message.edit_media(media=video)

    except Exception as e:
        logger.error(f"An error occurred while handling callback query: {e}")
