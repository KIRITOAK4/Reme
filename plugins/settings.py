from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from Krito import pbot
from helper.utils import humanbytes
from helper.function import get_page_gif
from .chatid import base_dir, get_chat_status
from helper.database import db
import os, random

# Directory for GIFs
random_gif = get_page_gif()  # Default settings image

def generate_buttons(button_data):
    """Generate InlineKeyboardMarkup from a list of (text, callback_data) tuples."""
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=callback)] for text, callback in button_data])

# Metadata fields mapping
METADATA_KEYS = {
    "title": "Send me the new value for title:",
    "artist": "Send me the new value for artist:",
    "audio": "Send me the new value for audio:",
    "video": "Send me the new value for video:",
    "author": "Send me the new value for author:",
    "subtitle": "Send me the new value for subtitle:"
}

@pbot.on_message(filters.private & filters.command("settings"))
async def settings_menu(client, message):
    user_id = message.from_user.id
    template = await db.get_template(user_id)
    upload_type = await db.get_uploadtype(user_id)
    exten = await db.get_exten(user_id)
    chat_id, verified = await get_chat_status(user_id)
    thumbnail = await db.get_thumbnail(user_id)
    metadata = await db.get_metadata(user_id)
    metadata_status = "False" if all(value == "t.me/devil_testing_bot" for value in metadata.values()) else "True"
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

@pbot.on_callback_query(filters.regex(r"settings_menu"))
async def settings_menu_callback(client, callback_query):
    user_id = callback_query.from_user.id
    template = await db.get_template(user_id)
    upload_type = await db.get_uploadtype(user_id)
    exten = await db.get_exten(user_id)
    chat_id, verified = await get_chat_status(user_id)
    thumbnail = await db.get_thumbnail(user_id)
    metadata = await db.get_metadata(user_id)
    metadata_status = "False" if all(value == "t.me/devil_testing_bot" for value in metadata.values()) else "True"
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
┃**--📮Chat ID--**: {chat_id} {"✅ Verified" if verified else "❌ Not Verified"}
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
        ("Set Sample Button", "settings_sample_button"),  # Add this line
        ("Delete Settings", "settings_delete")
    ])

    await callback_query.message.edit_text(caption, reply_markup=buttons)

@pbot.on_callback_query(filters.regex(r"settings_toggle_metadata"))
async def metadata_submenu(client, callback_query):
    buttons = generate_buttons([
        ("Set Title", "set_metadata_title"),
        ("Set Artist", "set_metadata_artist"),
        ("Set Audio", "set_metadata_audio"),
        ("Set Author", "set_metadata_author"),
        ("Set Video", "set_metadata_video"),
        ("Set Subtitle", "set_metadata_subtitle"),
        ("Back", "settings_menu")
    ])
    await callback_query.message.edit_text("Select the metadata field to update:", reply_markup=buttons)

@pbot.on_callback_query(filters.regex(r"set_metadata_(title|author|artist|audio|video|subtitle)"))
async def set_metadata_field(client, callback_query):
    field_name = callback_query.data.split("_")[-1]
    await callback_query.edit_message_text(
        METADATA_KEYS[field_name],
        reply_markup=generate_buttons([("Back", "settings_toggle_metadata")])
    )

@pbot.on_callback_query(filters.regex(r"settings_set_caption"))
async def set_caption_callback(client, callback_query):
    await callback_query.edit_message_text(
        "Send me the new caption to save. \n Few predifened caption u can use\n {filename}\n{duration}\n{filesize}",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )
        
@pbot.on_callback_query(filters.regex(r"settings_set_thumbnail"))
async def set_thumbnail_callback(client, callback_query):
    await callback_query.edit_message_text(
        "Send me the new thumbnail (as an image).",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )


@pbot.on_callback_query(filters.regex(r"settings_set_template"))
async def set_template_callback(client, callback_query):
    templates = [
        "[S {season} Ep {episode}] {cz_name}",
        "[s {season} ep {episode}] {cz_name}",
        "[S {season} EP {episode}] {cz_name}",
        "[Season {season} Episode {episode}] {cz_name}",
        "[Ep {episode}] {cz_name}",
        "[SEASON {season} EPISODE {episode}] {cz_name}"
    ]
    template_text = "\n".join([f"{i+1}. {template}" for i, template in enumerate(templates)])
    await callback_query.edit_message_text(
        f"Available Templates:\n\n{template_text}\n\nReply with the template number to set.",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )

@pbot.on_callback_query(filters.regex(r"settings_upload_option"))
async def set_upload_option_callback(client, callback_query):
    await callback_query.edit_message_text(
        "Choose upload mode:\n1. document\n2. video\n3. audio\n\nReply with the number to set.",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )

@pbot.on_callback_query(filters.regex(r"settings_set_extension"))
async def set_extension_callback(client, callback_query):
    await callback_query.edit_message_text(
        "Available extensions:\n1. mkv\n2. mp4\n3. mp3\n4. apk\n5. txt\n6. pdf\n\n\nReply with the number to set.",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )

@pbot.on_callback_query(filters.regex(r"settings_sample_button"))
async def settings_sample_button_callback(client, callback_query):
    user_id = callback_query.from_user.id
    current_value = await db.get_sample_value(user_id)
    await callback_query.message.edit_text(
        f"Current Sample Value: {current_value}\n\nReply with a new value (choose from 0, 30, 60, 90, or 120).",
        reply_markup=generate_buttons([("Back", "settings_menu")])
    )

@pbot.on_message(filters.reply, group=-1)
async def handle_user_reply(client, message):
    user_id = message.from_user.id
    reply_message = message.reply_to_message

    async def handle_metadata():
        field_name = next(key for key, value in METADATA_KEYS.items() if value == reply_message.caption)
        metadata = await db.get_metadata(user_id)
        metadata[field_name] = message.text
        await db.set_metadata(user_id, metadata)
        await message.reply(f"✅ **{field_name.capitalize()}** updated to `{message.text}`!")
        await message.delete()

    async def handle_caption_update():
        try:
            await db.set_caption(user_id, message.text)
            await message.reply("✅ Your caption has been updated!")
            await message.delete()
        except Exception as e:
            await message.reply(f"❌ Failed to update caption: {str(e)}")

    async def handle_thumbnail_update():
        if message.photo:
            await db.set_thumbnail(user_id, message.photo.file_id)
            await message.reply("✅ Your thumbnail has been updated!")
            await message.delete()
        else:
            await message.reply("❌ Please send a valid image as the thumbnail.")

    async def handle_template_choice():
        templates = [
            "[S{season} Ep{episode}] {cz_name}",
            "[s{season} ep{episode}] {cz_name}",
            "[S{season} EP{episode}] {cz_name}",
            "[Season{season} Episode{episode}] {cz_name}",
            "[Ep{episode}] {cz_name}",
            "[SEASON{season} EPISODE{episode}] {cz_name}",
        ]
        try:
            choice = int(message.text)
            if 1 <= choice <= len(templates):
                await db.set_template(user_id, templates[choice - 1])
                await message.reply("✅ Your template has been updated!")
                await message.delete()
            else:
                await message.reply("❌ Invalid template number.")
        except ValueError:
            await message.reply("❌ Invalid input. Please reply with a number.")

    async def handle_upload_mode_choice():
        upload_modes = {1: "document", 2: "video", 3: "audio"}
        try:
            mode = int(message.text)
            if mode in upload_modes:
                await db.set_uploadtype(user_id, upload_modes[mode])
                await message.reply("✅ Your upload mode has been updated!")
                await message.delete()
            else:
                await message.reply("❌ Invalid choice.")
        except ValueError:
            await message.reply("❌ Invalid input. Please reply with a number.")

    async def handle_extension_choice():
        extensions = {1: "mkv", 2: "mp4", 3: "mp3", 4: "apk", 5: "txt", 6: "pdf"}
        try:
            ext = int(message.text)
            if ext in extensions:
                await db.set_exten(user_id, extensions[ext])
                await message.reply("✅ Your extension has been updated!")
                await message.delete()
            else:
                await message.reply("❌ Invalid extension number.")
        except ValueError:
            await message.reply("❌ Invalid input. Please reply with a number.")

    async def handle_sample_value_update():
        user_id = message.from_user.id
        try:
            new_value = int(message.text)
            if new_value not in [0, 30, 60, 90, 120]:
                await message.reply("❌ Invalid sample value. Please choose from 0, 30, 60, 90, or 120.")
                return
            await db.set_sample_value(user_id, new_value)
            await message.reply(f"✅ Sample value updated to {new_value}!")
            await message.delete()
        except ValueError:
            await message.reply("❌ Invalid input. Please enter a number.")

    dispatch_table = {
        "Send me the new caption to save.": handle_caption_update,
        "Send me the new thumbnail (as an image).": handle_thumbnail_update,
        "Available Templates": handle_template_choice,
        "Choose upload mode": handle_upload_mode_choice,
        "Available extensions": handle_extension_choice,
        "Current Sample Value": handle_sample_value_update,
    }

    if reply_message.caption in METADATA_KEYS.values():
        await handle_metadata()
    else:
        for key, handler in dispatch_table.items():
            if key in reply_message.caption:
                await handler()
                return

# Delete Settings
@pbot.on_callback_query(filters.regex(r"settings_delete"))
async def delete_settings_callback(client, callback_query):
    buttons = generate_buttons([
        ("Delete Caption", "delete_caption"),
        ("Delete Thumbnail", "delete_thumbnail"),
        ("Delete Metadata", "delete_metadata"),
        ("Delete Chatid", "delete_chatid"),
        ("Back", "settings_menu")
    ])
    await callback_query.message.edit_text(
        "Select the setting to delete:",
        reply_markup=buttons
    )

@pbot.on_callback_query(filters.regex(r"delete_chatid"))
async def delete_chatid_callback(client, callback_query):
    user_id = callback_query.from_user.id
    user_data = base_dir.get(user_id)
    if user_data and "chat_id" in user_data:
        del base_dir[user_id]
        await callback_query.message.edit_text(
            "✅ Your Chat ID has been deleted successfully. Returning to settings."
        )
    else:
        await callback_query.message.edit_text(
            "❌ No Chat ID found to delete. Returning to settings."
        )
    await settings_menu_callback(client, callback_query)

@pbot.on_callback_query(filters.regex(r"delete_caption"))
async def delete_caption(client, callback_query):
    user_id = callback_query.from_user.id
    await db.set_caption(user_id, None)
    await callback_query.message.reply(
        "❌ Your Caption has been reset. Returning to settings.",
        reply_markup=None
    )
    await settings_menu_callback(client, callback_query)

@pbot.on_callback_query(filters.regex(r"delete_thumbnail"))
async def delete_thumbnail(client, callback_query):
    user_id = callback_query.from_user.id
    await db.set_thumbnail(user_id, None)
    await callback_query.message.reply(
        "❌ Your Thumbnail has been reset. Returning to settings.",
        reply_markup=None
    )
    await settings_menu_callback(client, callback_query)

@pbot.on_callback_query(filters.regex(r"delete_metadata"))
async def delete_metadata(client, callback_query):
    user_id = callback_query.from_user.id
    default_metadata = {
        "title": "t.me/devil_testing_bot",
        "author": "t.me/devil_testing_bot",
        "artist": "t.me/devil_testing_bot",
        "audio": "t.me/devil_testing_bot",
        "video": "t.me/devil_testing_bot",
        "subtitle": "t.me/devil_testing_bot"
    }
    await db.set_metadata(user_id, default_metadata)
    await callback_query.message.reply(
        "❌ Your Metadata has been reset to default values. Returning to settings.",
        reply_markup=None
    )
    await settings_menu_callback(client, callback_query)
    
