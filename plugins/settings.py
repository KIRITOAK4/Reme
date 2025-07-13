from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Krito import pbot
from helper.utils import humanbytes
from helper.function import get_page_gif
from .chatid import base_dir, get_chat_status
from helper.database import db

# Constants
TEMPLATES = [
    "[S {season} Ep {episode}] {cz_name}",
    "[s {season} ep {episode}] {cz_name}",
    "[S{season} EP{episode}] {cz_name}",
    "[s{season} ep{episode}] {cz_name}",
    "[Ep {episode}] {cz_name}",
    "[S{season}_EP{episode}] {cz_name}"
]
UPLOAD_MODES = ["document", "video", "audio"]
EXTENSIONS = ["mkv", "mp4", "mp3", "apk", "txt", "pdf"]
SAMPLE_VALUES = [0, 30, 60, 90, 120]
random_gif = get_page_gif()

METADATA_KEYS = {
    "title": "Send me the new value for title:",
    "artist": "Send me the new value for artist:",
    "audio": "Send me the new value for audio:",
    "video": "Send me the new value for video:",
    "author": "Send me the new value for author:",
    "subtitle": "Send me the new value for subtitle:"
}

def generate_buttons(button_data):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=callback)] for text, callback in button_data]
    )

# SETTINGS MENU
@pbot.on_message(filters.private & filters.command("settings"))
async def settings_menu(client, message):
    await render_settings_menu(client, message)

@pbot.on_callback_query(filters.regex(r"settings_menu"))
async def settings_menu_callback(client, callback_query):
    await render_settings_menu(client, callback_query.message)

async def render_settings_menu(client, message):
    user_id = message.from_user.id
    template = await db.get_template(user_id)
    upload_type = await db.get_uploadtype(user_id)
    exten = await db.get_exten(user_id)
    chat_id, verified = await get_chat_status(user_id)
    thumbnail = await db.get_thumbnail(user_id)
    metadata = await db.get_metadata(user_id)
    metadata_status = "False" if all(v == "t.me/devil_testing_bot" for v in metadata.values()) else "True"
    set_cap = await db.get_caption(user_id)
    used_space = await db.get_space_used(user_id)
    spaceup = humanbytes(used_space)

    caption = f"""
➖➖➖➖➖➖➖➖➖➖➖➖
┃   **--👩‍💻User ID--**: {user_id}
┃
┃**--🧾Caption--**: {set_cap}
┃**--🎬Upload Type--**: {upload_type}
┃**--🎛Extension--**: {exten}
┃**--📮Chat ID--**: {chat_id} {"✅" if verified else "❌"}
┃**--🏡Thumbnail--**: {"✅ Set" if thumbnail else "❌ Not Set"}
┃**--🛠Metadata--**: {"✅ Enabled" if metadata_status == "True" else "❌ Disabled"}
┃**--🌓Space Used--**: {spaceup}
➖➖➖➖➖➖➖➖➖➖➖➖
"""
    buttons = generate_buttons([
        ("Set Caption", "settings_set_caption"),
        ("Set Thumbnail", "settings_set_thumbnail"),
        ("Set Template", "settings_set_template"),
        ("Set Upload Mode", "settings_upload_option"),
        ("Set Extension", "settings_set_extension"),
        (f"Metadata {'✅' if metadata_status == 'True' else '❌'}", "settings_toggle_metadata"),
        ("Set Sample Button", "settings_sample_button"),
        ("Delete Settings", "settings_delete")
    ])

    if thumbnail:
        await message.reply_photo(photo=thumbnail, caption=caption, reply_markup=buttons)
    else:
        await message.reply_animation(animation=random_gif, caption=caption, reply_markup=buttons)

# ---------------- BUTTON SELECTORS ----------------

@pbot.on_callback_query(filters.regex("settings_set_template"))
async def open_template_selector(client, cq):
    await show_template_selector(client, cq, 0)

@pbot.on_callback_query(filters.regex("template_select_(\\d+)"))
async def show_template_selector(client, cq, index=None):
    i = int(cq.matches[0].group(1)) if index is None else index
    prev_i, next_i = (i - 1) % len(TEMPLATES), (i + 1) % len(TEMPLATES)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Prev", callback_data=f"template_select_{prev_i}"),
         InlineKeyboardButton("➡️ Next", callback_data=f"template_select_{next_i}")],
        [InlineKeyboardButton("✅ Set This", callback_data=f"template_set_{i}")],
        [InlineKeyboardButton("Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Current Template:\n\n`{TEMPLATES[i]}`", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("template_set_(\\d+)"))
async def set_template(client, cq):
    i = int(cq.matches[0].group(1))
    await db.set_template(cq.from_user.id, TEMPLATES[i])
    await cq.message.edit_text("✅ Template updated!")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex("settings_upload_option"))
async def open_upload_selector(client, cq):
    await show_upload_selector(client, cq, 0)

@pbot.on_callback_query(filters.regex("upload_select_(\\d+)"))
async def show_upload_selector(client, cq, index=None):
    i = int(cq.matches[0].group(1)) if index is None else index
    prev_i, next_i = (i - 1) % len(UPLOAD_MODES), (i + 1) % len(UPLOAD_MODES)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Prev", callback_data=f"upload_select_{prev_i}"),
         InlineKeyboardButton("➡️ Next", callback_data=f"upload_select_{next_i}")],
        [InlineKeyboardButton("✅ Set This", callback_data=f"upload_set_{i}")],
        [InlineKeyboardButton("Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Current Upload Mode: `{UPLOAD_MODES[i]}`", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("upload_set_(\\d+)"))
async def set_upload_mode(client, cq):
    i = int(cq.matches[0].group(1))
    await db.set_uploadtype(cq.from_user.id, UPLOAD_MODES[i])
    await cq.message.edit_text("✅ Upload mode updated!")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex("settings_set_extension"))
async def open_extension_selector(client, cq):
    await show_extension_selector(client, cq, 0)

@pbot.on_callback_query(filters.regex("exten_select_(\\d+)"))
async def show_extension_selector(client, cq, index=None):
    i = int(cq.matches[0].group(1)) if index is None else index
    prev_i, next_i = (i - 1) % len(EXTENSIONS), (i + 1) % len(EXTENSIONS)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Prev", callback_data=f"exten_select_{prev_i}"),
         InlineKeyboardButton("➡️ Next", callback_data=f"exten_select_{next_i}")],
        [InlineKeyboardButton("✅ Set This", callback_data=f"exten_set_{i}")],
        [InlineKeyboardButton("Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Current Extension: `{EXTENSIONS[i]}`", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("exten_set_(\\d+)"))
async def set_extension(client, cq):
    i = int(cq.matches[0].group(1))
    await db.set_exten(cq.from_user.id, EXTENSIONS[i])
    await cq.message.edit_text("✅ Extension updated!")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex("settings_sample_button"))
async def open_sample_selector(client, cq):
    await show_sample_selector(client, cq, 0)

@pbot.on_callback_query(filters.regex("sample_select_(\\d+)"))
async def show_sample_selector(client, cq, index=None):
    i = int(cq.matches[0].group(1)) if index is None else index
    prev_i, next_i = (i - 1) % len(SAMPLE_VALUES), (i + 1) % len(SAMPLE_VALUES)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Prev", callback_data=f"sample_select_{prev_i}"),
         InlineKeyboardButton("➡️ Next", callback_data=f"sample_select_{next_i}")],
        [InlineKeyboardButton("✅ Set This", callback_data=f"sample_set_{i}")],
        [InlineKeyboardButton("Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Current Sample Value: `{SAMPLE_VALUES[i]}`", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("sample_set_(\\d+)"))
async def set_sample_value(client, cq):
    i = int(cq.matches[0].group(1))
    await db.set_sample_value(cq.from_user.id, SAMPLE_VALUES[i])
    await cq.message.edit_text("✅ Sample value updated!")
    await settings_menu_callback(client, cq)

# ---------------- CAPTION & THUMBNAIL ----------------

@pbot.on_callback_query(filters.regex("settings_set_caption"))
async def ask_caption(client, cq):
    await cq.message.edit_text(
        "Send me the new caption to save.\n\nAvailable vars:\n{filename}\n{duration}\n{filesize}",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )

@pbot.on_callback_query(filters.regex("settings_set_thumbnail"))
async def ask_thumbnail(client, cq):
    await cq.message.edit_text(
        "Send me the new thumbnail (as an image).",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )

@pbot.on_message(filters.private & filters.reply)
async def handle_caption_or_thumbnail_reply(client, message):
    user_id = message.from_user.id
    reply_to = message.reply_to_message
    if not reply_to or not reply_to.text:
        return

    if "Send me the new caption" in reply_to.text:
        try:
            await db.set_caption(user_id, message.text)
            await reply_to.edit_text("✅ Caption updated successfully!")
            await message.delete()
        except Exception as e:
            await message.reply(f"❌ Failed to update caption:\n`{e}`")

    elif "Send me the new thumbnail" in reply_to.text:
        if message.photo:
            try:
                await db.set_thumbnail(user_id, message.photo.file_id)
                await reply_to.edit_text("✅ Thumbnail updated successfully!")
                await message.delete()
            except Exception as e:
                await message.reply(f"❌ Failed to update thumbnail:\n`{e}`")
        else:
            await message.reply("❌ Please send a valid image.")

# ---------------- METADATA ----------------

@pbot.on_callback_query(filters.regex("settings_toggle_metadata"))
async def metadata_toggle(client, cq):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Title", "set_metadata_title"),
            InlineKeyboardButton("❌ Delete Title", "delete_metadata_title")
        ],
        [
            InlineKeyboardButton("Artist", "set_metadata_artist"),
            InlineKeyboardButton("❌ Delete Artist", "delete_metadata_artist")
        ],
        [
            InlineKeyboardButton("Audio", "set_metadata_audio"),
            InlineKeyboardButton("❌ Delete Audio", "delete_metadata_audio")
        ],
        [
            InlineKeyboardButton("Author", "set_metadata_author"),
            InlineKeyboardButton("❌ Delete Author", "delete_metadata_author")
        ],
        [
            InlineKeyboardButton("Video", "set_metadata_video"),
            InlineKeyboardButton("❌ Delete Video", "delete_metadata_video")
        ],
        [
            InlineKeyboardButton("Subtitle", "set_metadata_subtitle"),
            InlineKeyboardButton("❌ Delete Subtitle", "delete_metadata_subtitle")
        ],
        [
            InlineKeyboardButton("✅ Reset All Metadata", "delete_metadata_all")
        ],
        [
            InlineKeyboardButton("🔙 Back", "settings_menu")
        ]
    ])
    await cq.message.edit_text("Select a metadata field to update or delete:", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("set_metadata_(title|artist|audio|video|author|subtitle)"))
async def ask_metadata_field(client, cq):
    field = cq.data.split("_")[-1]
    await cq.message.edit_text(METADATA_KEYS[field], reply_markup=generate_buttons([("Back", "settings_toggle_metadata")]))

# ---------------- DELETE SETTINGS ----------------

@pbot.on_callback_query(filters.regex("settings_delete"))
async def delete_menu(client, cq):
    buttons = generate_buttons([
        ("Delete Caption", "delete_caption"),
        ("Delete Thumbnail", "delete_thumbnail"),
        ("Delete Metadata", "delete_metadata"),
        ("Delete Chatid", "delete_chatid"),
        ("Back", "settings_menu")
    ])
    await cq.message.edit_text("Select the setting to delete:", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("delete_caption"))
async def delete_caption(client, cq):
    await db.set_caption(cq.from_user.id, None)
    await cq.message.edit_text("❌ Caption reset.")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex("delete_thumbnail"))
async def delete_thumbnail(client, cq):
    await db.set_thumbnail(cq.from_user.id, None)
    await cq.message.edit_text("❌ Thumbnail reset.")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex("delete_metadata"))
async def delete_metadata(client, cq):
    default = {key: "t.me/devil_testing_bot" for key in METADATA_KEYS}
    await db.set_metadata(cq.from_user.id, default)
    await cq.message.edit_text("❌ Metadata reset.")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex("delete_chatid"))
async def delete_chatid(client, cq):
    user_id = cq.from_user.id
    base_dir.pop(user_id, None)
    await cq.message.edit_text("✅ Chat ID deleted.")
    await settings_menu_callback(client, cq)

@pbot.on_callback_query(filters.regex(r"delete_metadata_(title|artist|audio|video|author|subtitle)"))
async def delete_individual_metadata(client, cq):
    user_id = cq.from_user.id
    field = cq.matches[0].group(1)
    metadata = await db.get_metadata(user_id)
    metadata[field] = "t.me/devil_testing_bot"
    await db.set_metadata(user_id, metadata)
    await cq.message.edit_text(f"❌ `{field}` metadata field has been reset.")
    await metadata_toggle(client, cq)
    
@pbot.on_callback_query(filters.regex("delete_metadata_all"))
async def delete_metadata_all(client, cq):
    user_id = cq.from_user.id
    default = {key: "t.me/devil_testing_bot" for key in METADATA_KEYS}
    await db.set_metadata(user_id, default)
    await cq.message.edit_text("✅ All metadata fields have been reset to default.")
    await metadata_toggle(client, cq)
