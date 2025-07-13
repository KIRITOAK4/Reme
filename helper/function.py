import os
import random
import logging
from Krito import Text, Text1, Text2, Text3, MAX_PAGE
from pyrogram.types import InlineKeyboardButton

# Setup logging
logging.basicConfig(level=logging.INFO, filename="function_error.log")
logger = logging.getLogger("GifHandler")

# ✅ Your original version preserved
def get_page_gif():
    try:
        gif_files = os.listdir("./gif")
        if not gif_files:
            raise FileNotFoundError("No GIF files found in './gif' directory.")
        return f"./gif/{random.choice(gif_files)}"
    except Exception as e:
        logger.error(f"Error in get_page_gif: {e}")
        return None

# ✅ Optimized caption function
def get_page_caption(page_number, first_name, last_name, mention, username, id):
    try:
        templates = {1: Text, 2: Text1, 3: Text2, 4: Text3}
        template = templates.get(page_number, Text)
        mention_text = f"[{first_name}](tg://user?id={id})"
        username_text = f"@{username}" if username else ""
        return template.format(
            first_name=first_name,
            last_name=last_name or "",
            username=username_text,
            mention=mention_text,
            id=id
        )
    except Exception as e:
        logger.error(f"Error in get_page_caption: {e}")
        return "⚠️ Unable to generate caption."

# ✅ Optimized inline keyboard
def get_inline_keyboard(page_number):
    try:
        row = []
        if page_number > 1:
            row.append(InlineKeyboardButton("👈", callback_data="previous"))
        if page_number < MAX_PAGE:
            row.append(InlineKeyboardButton("👉", callback_data="next"))
        return [row] if row else []
    except Exception as e:
        logger.error(f"Error in get_inline_keyboard: {e}")
        return []
