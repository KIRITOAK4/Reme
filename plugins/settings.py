from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaAnimation
from Krito import pbot
from helper.utils import humanbytes
from helper.function import get_page_gif
from .chatid import base_dir, get_chat_status
from helper.database import db
from pyrogram.errors import MessageEditTimeExpired, MessageNotModified

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

def generate_buttons(button_data, row_width=2):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=callback) for text, callback in button_data[i:i+row_width]]
        for i in range(0, len(button_data), row_width)
    ])

async def render_settings_menu(client, message, fast=False, cq=None):
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
┃**--📞 Caption--**: {set_cap}
┃**--🎮 Upload Type--**: {upload_type}
┃**--🎧 Extension--**: {exten}
┃**--📮 Chat ID--**: {chat_id} {"✅" if verified else "❌"}
┃**--🏡 Thumbnail--**: {"✅ Set" if thumbnail else "❌ Not Set"}
┃**--🚠 Metadata--**: {"✅ Enabled" if metadata_status == "True" else "❌ Disabled"}
┃**--🌃 Space Used--**: {spaceup}
➖➖➖➖➖➖➖➖➖➖➖➖
"""
    buttons = generate_buttons([
        ("Caption", "settings_set_caption"),
        ("Thumbnail", "settings_set_thumbnail"),
        ("Template", "settings_template_toggle"),
        ("Upload Mode", "settings_upload_toggle"),
        ("Extension", "settings_extension_toggle"),
        ("Sample Button", "settings_sample_toggle"),
        (f"Metadata {'✅' if metadata_status == 'True' else '❌'}", "settings_toggle_metadata")
    ])
    buttons.inline_keyboard.append([InlineKeyboardButton("Delete Settings", callback_data="settings_delete")])

    if fast:
        try:
            await message.edit_caption(caption=caption, reply_markup=buttons)
        except MessageEditTimeExpired:
            if cq:
                await cq.answer("⚠️ Message too old to edit. Please use /settings again.", show_alert=True)
    else:
        if thumbnail:
            await message.reply_photo(photo=thumbnail, caption=caption, reply_markup=buttons)
        else:
            await message.reply_animation(animation=random_gif, caption=caption, reply_markup=buttons)

@pbot.on_message(filters.private & filters.command("settings"))
async def settings_menu(client, message):
    await render_settings_menu(client, message)

@pbot.on_callback_query(filters.regex(r"settings_menu"))
async def settings_menu_callback(client, cq):
    await render_settings_menu(client, cq.message, fast=True, cq=cq)

# ---------- Template Toggle ----------
@pbot.on_callback_query(filters.regex("settings_template_toggle"))
async def toggle_template(client, cq):
    current = await db.get_template(cq.from_user.id)
    index = TEMPLATES.index(current) if current in TEMPLATES else 0
    new_index = (index + 1) % len(TEMPLATES)
    await db.set_template(cq.from_user.id, TEMPLATES[new_index])
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📄 {new_index + 1}", callback_data="settings_template_toggle")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Current Template:\n\n`{TEMPLATES[new_index]}`", reply_markup=buttons)

# ---------- Upload Toggle ----------
@pbot.on_callback_query(filters.regex("settings_upload_toggle"))
async def toggle_upload(client, cq):
    current = await db.get_uploadtype(cq.from_user.id)
    index = UPLOAD_MODES.index(current) if current in UPLOAD_MODES else 0
    new_index = (index + 1) % len(UPLOAD_MODES)
    await db.set_uploadtype(cq.from_user.id, UPLOAD_MODES[new_index])
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎮 {UPLOAD_MODES[new_index]}", callback_data="settings_upload_toggle")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Upload Mode:\n\n`{UPLOAD_MODES[new_index]}`", reply_markup=buttons)

# ---------- Extension Toggle ----------
@pbot.on_callback_query(filters.regex("settings_extension_toggle"))
async def toggle_extension(client, cq):
    current = await db.get_exten(cq.from_user.id)
    index = EXTENSIONS.index(current) if current in EXTENSIONS else 0
    new_index = (index + 1) % len(EXTENSIONS)
    await db.set_exten(cq.from_user.id, EXTENSIONS[new_index])
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎧 {EXTENSIONS[new_index]}", callback_data="settings_extension_toggle")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Extension:\n\n`{EXTENSIONS[new_index]}`", reply_markup=buttons)

# ---------- Sample Toggle ----------
@pbot.on_callback_query(filters.regex("settings_sample_toggle"))
async def toggle_sample(client, cq):
    current = await db.get_sample_value(cq.from_user.id)
    index = SAMPLE_VALUES.index(current) if current in SAMPLE_VALUES else 0
    new_index = (index + 1) % len(SAMPLE_VALUES)
    await db.set_sample_value(cq.from_user.id, SAMPLE_VALUES[new_index])
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎯 {SAMPLE_VALUES[new_index]} sec", callback_data="settings_sample_toggle")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(f"Sample Duration:\n\n`{SAMPLE_VALUES[new_index]} seconds`", reply_markup=buttons)

# ---------------- caption ---------------

@pbot.on_callback_query(filters.regex("settings_set_caption"))
async def ask_caption(client, cq):
    await cq.message.edit_text(
        "📝 **Send the new caption.**\n\nYou can use:\n`{filename}` — file name\n`{duration}` — duration\n`{filesize}` — size",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
        ])
    )

@pbot.on_message(filters.private & filters.reply)
async def save_caption(client, message):
    user_id = message.from_user.id
    if not message.reply_to_message or not message.reply_to_message.text:
        return

    reply_text = message.reply_to_message.text

    if "Send the new caption" in reply_text:
        await db.set_caption(user_id, message.text)
        await message.reply("✅ **Caption updated successfully.**")
        await message.delete()

# ---------------- Thumbnial ---------------

@pbot.on_callback_query(filters.regex("settings_set_thumbnail"))
async def ask_thumbnail(client, cq):
    await cq.message.edit_text(
        "🖼️ **Send a new thumbnail** (photo only)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
        ])
    )

@pbot.on_message(filters.private & filters.reply)
async def save_thumbnail(client, message):
    user_id = message.from_user.id
    if not message.reply_to_message or not message.reply_to_message.text:
        return

    reply_text = message.reply_to_message.text

    if "Send a new thumbnail" in reply_text:
        if message.photo:
            await db.set_thumbnail(user_id, message.photo.file_id)
            await message.reply("✅ **Thumbnail updated.**")
            await message.delete()
        else:
            await message.reply("❌ Please send a valid photo.")
            
# ---------------- Metadata ---------------

@pbot.on_callback_query(filters.regex("settings_toggle_metadata"))
async def metadata_menu(client, cq):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎧 Title", callback_data="set_metadata_title"),
         InlineKeyboardButton("🗑 Title", callback_data="delete_metadata_title")],
        [InlineKeyboardButton("🎤 Artist", callback_data="set_metadata_artist"),
         InlineKeyboardButton("🗑 Artist", callback_data="delete_metadata_artist")],
        [InlineKeyboardButton("🎵 Audio", callback_data="set_metadata_audio"),
         InlineKeyboardButton("🗑 Audio", callback_data="delete_metadata_audio")],
        [InlineKeyboardButton("🎬 Video", callback_data="set_metadata_video"),
         InlineKeyboardButton("🗑 Video", callback_data="delete_metadata_video")],
        [InlineKeyboardButton("✍️ Author", callback_data="set_metadata_author"),
         InlineKeyboardButton("🗑 Author", callback_data="delete_metadata_author")],
        [InlineKeyboardButton("📜 Subtitle", callback_data="set_metadata_subtitle"),
         InlineKeyboardButton("🗑 Subtitle", callback_data="delete_metadata_subtitle")],
        [InlineKeyboardButton("♻️ Reset All", callback_data="reset_all_metadata")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text("🛠 **Metadata Settings**\nChoose field to update or reset.", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("set_metadata_(title|artist|audio|video|author|subtitle)"))
async def ask_metadata(client, cq):
    field = cq.matches[0].group(1)
    await cq.message.edit_text(
        f"✏️ Send new value for **{field}**:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="settings_toggle_metadata")]
        ])
    )

# ---------------- Delete ---------------

@pbot.on_callback_query(filters.regex("settings_delete"))
async def delete_menu(client, cq):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Caption", callback_data="delete_caption"),
         InlineKeyboardButton("🗑 Thumbnail", callback_data="delete_thumbnail")],
        [InlineKeyboardButton("🗑 Metadata", callback_data="reset_all_metadata")],
        [InlineKeyboardButton("🗑 Chat ID", callback_data="delete_chatid")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text("🧹 **Select item to delete**:", reply_markup=buttons)

@pbot.on_callback_query(filters.regex("delete_caption"))
async def delete_caption(client, cq):
    await db.set_caption(cq.from_user.id, None)
    await cq.answer("🗑 Caption removed", show_alert=False)
    await render_settings_menu(client, cq.message, fast=True, cq=cq)

@pbot.on_callback_query(filters.regex("delete_thumbnail"))
async def delete_thumbnail(client, cq):
    await db.set_thumbnail(cq.from_user.id, None)
    await cq.answer("🗑 Thumbnail removed", show_alert=False)
    await render_settings_menu(client, cq.message, fast=True, cq=cq)

@pbot.on_callback_query(filters.regex("delete_chatid"))
async def delete_chatid(client, cq):
    base_dir.pop(cq.from_user.id, None)
    await cq.answer("🗑 Chat ID removed", show_alert=False)
    await render_settings_menu(client, cq.message, fast=True, cq=cq)

@pbot.on_callback_query(filters.regex("delete_metadata_(title|artist|audio|video|author|subtitle)"))
async def delete_metadata_field(client, cq):
    field = cq.matches[0].group(1)
    metadata = await db.get_metadata(cq.from_user.id)
    metadata[field] = "t.me/devil_testing_bot"
    await db.set_metadata(cq.from_user.id, metadata)
    await cq.answer(f"🗑️ {field.capitalize()} reset!", show_alert=False)
    await metadata_menu(client, cq)

@pbot.on_callback_query(filters.regex("reset_all_metadata"))
async def reset_all_metadata(client, cq):
    default = {key: "t.me/devil_testing_bot" for key in METADATA_KEYS}
    await db.set_metadata(cq.from_user.id, default)
    await cq.answer("✅ All metadata reset.", show_alert=False)
    await metadata_menu(client, cq)
