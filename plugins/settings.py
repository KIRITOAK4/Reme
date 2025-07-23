from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaAnimation
from pyrogram.errors import MessageEditTimeExpired, MessageNotModified
from Krito import pbot
from helper.utils import humanbytes
from helper.function import get_page_gif
from helper.database import db
from .chatid import base_dir, get_chat_status

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
    user_id = cq.from_user.id if cq else message.from_user.id
    template = await db.get_template(user_id)
    upload_type = await db.get_uploadtype(user_id)
    exten = await db.get_exten(user_id)
    sample = await db.get_sample_value(user_id)
    chat_id, verified = await get_chat_status(user_id)
    thumbnail = await db.get_thumbnail(user_id)
    metadata = await db.get_metadata(user_id)
    metadata_enabled = any(v != "t.me/devil_testing_bot" for v in metadata.values())
    set_cap = await db.get_caption(user_id)
    used_space = await db.get_space_used(user_id)

    caption = f"""
➖➖➖➖➖➖➖➖➖➖➖➖
┃   **--👩‍💻User ID--**: {user_id}
┃
┃**--📞 Caption--**: {set_cap}
┃**--🎮 Upload Type--**: {upload_type}
┃**--🎧 Extension--**: {exten}
┃**--⏱ Sample--**: {sample} sec
┃**--📮 Chat ID--**: {chat_id} {"✅" if verified else "❌"}
┃**--🏡 Thumbnail--**: {"✅ Set" if thumbnail else "❌ Not Set"}
┃**--🚠 Metadata--**: {"✅ Enabled" if metadata_enabled else "❌ Disabled"}
┃**--🌃 Space Used--**: {humanbytes(used_space)}
➖➖➖➖➖➖➖➖➖➖➖➖
"""

    buttons = generate_buttons([
        ("Caption", "settings_set_caption"),
        ("Thumbnail", "settings_set_thumbnail"),
        ("Template", "settings_template_toggle"),
        ("Upload Mode", "settings_upload_toggle"),
        ("Extension", "settings_extension_toggle"),
        ("Sample", "settings_sample_toggle"),
        (f"Metadata {'✅' if metadata_enabled else '❌'}", "settings_toggle_metadata")
    ])
    buttons.inline_keyboard.append([InlineKeyboardButton("🗑 Delete Settings", callback_data="settings_delete")])

    try:
        if fast:
            await message.edit_caption(caption=caption, reply_markup=buttons)
        else:
            if thumbnail:
                await message.reply_photo(thumbnail, caption=caption, reply_markup=buttons)
            else:
                await message.reply_animation(random_gif, caption=caption, reply_markup=buttons)
    except MessageEditTimeExpired:
        if cq:
            await cq.answer("⚠️ Message too old to edit. Please use /settings again.", show_alert=True)

# Entry Commands
@pbot.on_message(filters.private & filters.command("settings"))
async def settings_menu(client, message):
    await render_settings_menu(client, message)

@pbot.on_callback_query(filters.regex("settings_menu"))
async def settings_menu_callback(client, cq):
    await render_settings_menu(client, cq.message, fast=True, cq=cq)

# Generic Cycle Toggle
async def cycle_toggle(cq, values, getter, setter, label, show_index=False, suffix=""):
    user_id = cq.from_user.id
    current = await getter(user_id)
    index = values.index(current) if current in values else 0
    new_index = (index + 1) % len(values)
    new_value = values[new_index]
    await setter(user_id, new_value)

    if show_index:
        button_text = f"{new_index + 1}/{len(values)}"
        caption_text = f"📄 **Template {new_index + 1}/{len(values)}**\n\n`{new_value}`"
    else:
        button_text = f"{new_value}{suffix}"
        caption_text = f"{label}:\n\n`{new_value}`"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(button_text, callback_data=cq.data)],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
    ])
    await cq.message.edit_text(caption_text, reply_markup=buttons)

# Template
@pbot.on_callback_query(filters.regex("settings_template_toggle"))
async def toggle_template(client, cq):
    await cycle_toggle(cq, TEMPLATES, db.get_template, db.set_template, "📄 Template", show_index=True)

# Upload Type
@pbot.on_callback_query(filters.regex("settings_upload_toggle"))
async def toggle_upload(client, cq):
    await cycle_toggle(cq, UPLOAD_MODES, db.get_uploadtype, db.set_uploadtype, "🎮 Upload Type")

# Extension
@pbot.on_callback_query(filters.regex("settings_extension_toggle"))
async def toggle_extension(client, cq):
    await cycle_toggle(cq, EXTENSIONS, db.get_exten, db.set_exten, "🎧 Extension")

# Sample
@pbot.on_callback_query(filters.regex("settings_sample_toggle"))
async def toggle_sample(client, cq):
    await cycle_toggle(cq, SAMPLE_VALUES, db.get_sample_value, db.set_sample_value, "🎯 Sample", suffix=" sec")

# Caption/Thumbnail
@pbot.on_callback_query(filters.regex("settings_set_caption"))
async def ask_caption(client, cq):
    await cq.message.edit_text(
        "📝 Send new caption\n\nYou can use:\n`{filename}` `{duration}` `{filesize}`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]])
    )

@pbot.on_callback_query(filters.regex("settings_set_thumbnail"))
async def ask_thumbnail(client, cq):
    await cq.message.edit_text(
        "🖼️ Send new thumbnail (photo only)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]])
    )

# Metadata
@pbot.on_callback_query(filters.regex("settings_toggle_metadata"))
async def metadata_menu(client, cq):
    fields = ["title", "artist", "audio", "video", "author", "subtitle"]
    buttons = [
        [
            InlineKeyboardButton(f"🎧 {field.title()}", callback_data=f"set_metadata_{field}"),
            InlineKeyboardButton(f"🗑 {field.title()}", callback_data=f"delete_metadata_{field}")
        ] for field in fields
    ]
    buttons.append([InlineKeyboardButton("♻️ Reset All", callback_data="reset_all_metadata")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="settings_menu")])

    await cq.message.edit_text("🛠 **Metadata Settings**\nChoose field to update or reset.", reply_markup=InlineKeyboardMarkup(buttons))

@pbot.on_callback_query(filters.regex(r"set_metadata_(title|artist|audio|video|author|subtitle)"))
async def set_metadata_value(client, cq):
    field = cq.matches[0].group(1)
    message = METADATA_KEYS[field]  # e.g., "Send me the new value for title:"
    
    await cq.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="settings_toggle_metadata")]
        ])
    )

@pbot.on_message(filters.reply, group=-1)
async def handle_user_reply(client, message):
    user_id = message.from_user.id
    reply_message = message.reply_to_message

    reply_text = reply_message.text or reply_message.caption or ""

    async def handle_metadata():
        try:
            field_name = next(key for key, prompt in METADATA_KEYS.items() if prompt in reply_text)
            metadata = await db.get_metadata(user_id) or {}
            metadata[field_name] = message.text
            await db.set_metadata(user_id, metadata)
            await message.reply(f"✅ **{field_name.capitalize()}** updated to `{message.text}`!")
        except Exception as e:
            await message.reply(f"❌ Failed to update metadata: {e}")
        finally:
            await message.delete()

    async def handle_caption_update():
        try:
            await db.set_caption(user_id, message.text)
            await message.reply("✅ Your caption has been updated!")
        except Exception as e:
            await message.reply(f"❌ Failed to update caption: {str(e)}")
        finally:
            await message.delete()

    async def handle_thumbnail_update():
        if message.photo:
            await db.set_thumbnail(user_id, message.photo.file_id)
            await message.reply("✅ Your thumbnail has been updated!")
        else:
            await message.reply("❌ Please send a valid image as the thumbnail.")
        await message.delete()

    # Dispatch based on prompt in replied message
    if any(prompt in reply_text for prompt in METADATA_KEYS.values()):
        await handle_metadata()
    elif "Send new caption" in reply_text:
        await handle_caption_update()
    elif "Send new thumbnail" in reply_text:
        await handle_thumbnail_update()

# Delete logic
@pbot.on_callback_query(filters.regex("settings_delete"))
async def delete_menu(client, cq):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗑 Caption", callback_data="delete_caption"),
            InlineKeyboardButton("🗑 Thumbnail", callback_data="delete_thumbnail")
        ],
        [
            InlineKeyboardButton("🗑 Chat ID", callback_data="delete_chatid")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="settings_menu")
        ]
    ])
    await cq.message.edit_text("🧹 Select item to delete:", reply_markup=buttons)

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
    await cq.answer(f"🗑 {field.title()} reset!", show_alert=False)
    await metadata_menu(client, cq)

@pbot.on_callback_query(filters.regex("reset_all_metadata"))
async def reset_all_metadata(client, cq):
    await db.set_metadata(cq.from_user.id, {key: "t.me/devil_testing_bot" for key in METADATA_KEYS})
    await cq.answer("✅ All metadata reset.", show_alert=False)
    await metadata_menu(client, cq)
