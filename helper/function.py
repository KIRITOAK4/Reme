import os
import random
import logging
from Krito import Text, Text1, Text2, Text3, MAX_PAGE
from pyrogram.types import InlineKeyboardButton

# Setup logging
logging.basicConfig(level=logging.INFO, filename="lameda_error.log")
logger = logging.getLogger("GifHandler")

# Function to get a random GIF from the 'gif' directory
def get_page_gif(page_number):
    try:
        gif_files = os.listdir("./gif")
        if not gif_files:
            raise FileNotFoundError("No GIF files found in './gif' directory.")
        return f"./gif/{random.choice(gif_files)}"
    except Exception as e:
        logger.error(f"Error in get_page_gif: {e}")
        return None

# Function to format caption text
def get_page_caption(page_number, first_name, last_name, mention, username, id):
    try:
        text_templates = {1: Text, 2: Text1, 3: Text2, 4: Text3}
        page_text = text_templates.get(page_number, Text)
        mention = f"[{first_name}](tg://user?id={id})"
        username_text = f"@{username}" if username else ""
        return page_text.format(
            first_name=first_name, last_name=last_name, username=username_text, mention=mention, id=id
        )
    except Exception as e:
        logger.error(f"Error in get_page_caption: {e}")
        return None

# Function to generate inline keyboard
def get_inline_keyboard(page_number):
    try:
        buttons = []
        if page_number > 1:
            buttons.append(InlineKeyboardButton("👈", callback_data="previous"))
        if page_number < MAX_PAGE:
            buttons.append(InlineKeyboardButton("👉", callback_data="next"))
        return [buttons] if buttons else []
    except Exception as e:
        logger.error(f"Error in get_inline_keyboard: {e}")
        return None
