import os
import random
import logging
from gif import *
from Krito import Text, Text1, Text2, Text3, MAX_PAGE
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, filename='lameda_error.log')
logger = logging.getLogger("GifHandler")
logger.setLevel(level=logging.INFO)

# Function to get a random GIF from the 'gif' folder
def get_page_gif(page_number):
    try:
        gif = os.listdir('./gif')
        selected_gif = random.choice(gif)
        gif_path = f'./gif/{selected_gif}'
        return gif_path
    except Exception as e:
        logger.error(f"An error occurred in get_page_gif: {e}")
        return None

def get_page_caption(page_number, first_name, last_name, mention, username, id):
    try:
        page_text = {0: Text, 1: Text1, 2: Text2, 3: Text3}.get(page_number, Text)
        mention = f"[{first_name}](tg://user?id={id})"
        username_text = f"@{username}" if username else ""
        formatted_text = page_text.format(first_name=first_name, last_name=last_name, username=username_text, mention=mention, id=id)
        return formatted_text
    except Exception as e:
        logger.error(f"An error occurred in get_page_caption: {e}")
        return None

# Function to generate the inline keyboard based on the page number
def get_inline_keyboard(page_number):
    try:
        inline_keyboard = []
        row = []

        # Add "previous" button if not on the first page
        if page_number > 0:
            row.append(InlineKeyboardButton("👈", callback_data="previous"))

        # Add "next" button if not on the last page
        if page_number < MAX_PAGE:
            row.append(InlineKeyboardButton("👉", callback_data="next"))
        
        # Add the row to the inline keyboard
        inline_keyboard.append(row)
        return inline_keyboard
    except Exception as e:
        logger.error(f"An error occurred in get_inline_keyboard: {e}")
        return None
        
