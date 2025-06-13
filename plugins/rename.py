import os
import re
import time
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from helper.token import validate_user, check_user_limit
from .chatid import get_chat_status
from .metaedit import process_rename, change_metadata, generate_sample
from Krito import ubot, pbot, USER_CHAT, MAX_SPACE

async def extract_season_episode(filename):
    season, episode = None, None
    pattern1 = re.compile(r'[\[\(\{\<]?\s*S(\d+)(?:E|EP)(\d+)\s*[\]\)\}\>]?', re.IGNORECASE)
    pattern2 = re.compile(r'[\[\(\{\<]?\s*S(\d+)\s*(?:E|EP|-\s*EP)(\d+)\s*[\]\)\}\>]?', re.IGNORECASE)
    pattern3 = re.compile(r'[\[\(\{\<]?\s*(?:E|EP)\s*(\d+)\s*[\]\)\}\>]?', re.IGNORECASE)
    pattern3_2 = re.compile(r'\s*-\s*(\d+)\s*')
    pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
    patternX = re.compile(r'(\d+)')

    match = pattern1.search(filename) or pattern2.search(filename) or pattern4.search(filename) or pattern3.search(filename) or pattern3_2.search(filename)

    if match:
        groups = match.groups()
        if len(groups) == 2:
            season, episode = groups
        elif len(groups) == 1:
            episode = groups[0]
    else:
        episode_match = patternX.search(filename)
        if episode_match:
            episode = episode_match.group(1)

    cleaned_filename = filename
    if match:
        cleaned_filename = re.sub(re.escape(match.group(0)), "", filename).strip()
    elif episode:
        cleaned_filename = re.sub(re.escape(episode), "", cleaned_filename).strip()

    cleaned_filename = re.sub(r"[\s._-]+$", "", cleaned_filename).strip()
    base_name, _ = os.path.splitext(cleaned_filename)
    return season, episode, base_name

@pbot.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    """Handles the start of the renaming process by showing options."""
    user_id = message.from_user.id
    
    is_blocked = not await check_user_limit(user_id)
    if is_blocked:
        error_msg, button = await validate_user(message)
        if error_msg:
            await message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(button) if button else None)
            return

    file = getattr(message, message.media.value)
    filename = file.file_name
    filesize = humanbytes(file.file_size)

    try:
        text = f"""**__What do you want me to do with this file?__**\n\n**File Name** :- `{filename}`\n\n**File Size** :- `{filesize}`"""
        buttons = [
            [InlineKeyboardButton("📝 𝚂𝚃𝙰𝚁𝚃 𝚁𝙴𝙽𝙰𝙼𝙴 📝", callback_data="rename"),
             InlineKeyboardButton("🔄 𝙰𝚄𝚃𝙾 𝚁𝙴𝙽𝙰𝙼𝙴 🔄", callback_data="auto_rename")],
            [InlineKeyboardButton("📋 𝚂𝙰𝙼𝙿𝙻𝙴 📋", callback_data="sample")]
        ]

        await message.reply_text(text=text, reply_to_message_id=message.id, reply_markup=InlineKeyboardMarkup(buttons))
        await asyncio.sleep(1)  # Prevents flood wait issues

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_text(text=text, reply_to_message_id=message.id, reply_markup=InlineKeyboardMarkup(buttons))

@pbot.on_callback_query(filters.regex(r"^(rename|sample|auto_rename)"))
async def callback_handler(client, callback_query):
    """Handles callback queries for rename, auto rename, and sample options."""
    try:
        callback_data = callback_query.data
        user_id = callback_query.from_user.id
        original_message = callback_query.message.reply_to_message

        if callback_data == "sample":
            file = getattr(original_message, original_message.media.value)
            if not file or not file.file_name.endswith(('.mkv', '.mp4')):
                await callback_query.answer("❌ Only .mkv or .mp4 files are supported.", show_alert=True)
                return

            await callback_query.message.delete()

            input_path = f"downloads/{file.file_name}"
            output_path = f"downloads/sample_{os.path.splitext(file.file_name)[0]}.mp4"
            ms = await callback_query.message.reply_text("📥 Downloading the file...")

            try:
                file_path = await client.download_media(
                    message=original_message,
                    file_name=input_path,
                    progress=progress_for_pyrogram,
                    progress_args=("Downloading...", ms, time.time())
                )
            except Exception as e:
                await ms.edit(f"❌ Download failed: {e}")
                return

            sample_path = await generate_sample(input_path, output_path, user_id, ms)
            if not sample_path:
                return

            await ms.edit("📤 Uploading the generated sample...")
            try:
                await client.send_video(
                    chat_id=callback_query.message.chat.id,
                    video=sample_path,
                    caption="🎥 Here is your sample!"
                )
                await ms.delete()
            except Exception as e:
                await ms.edit(f"❌ Failed to upload sample: {e}")
            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(output_path):
                    os.remove(output_path)
            return

        file = getattr(original_message, original_message.media.value)
        filename = file.file_name
        file_size = file.file_size

        await callback_query.message.delete()

        season, episode, frt_name = await extract_season_episode(filename)

        if file_size > 3.2 * 1024 * 1024 * 1024:
            await original_message.reply_text("❌ This bot doesn't support files larger than 3.2GB.")
            return

        if callback_data == "auto_rename":
            if file_size > 1.9 * 1024 * 1024 * 1024:
                if ubot and ubot.is_connected:
                    template = await db.get_template(user_id) or "[S{season} Ep{episode}] {cz_name}"
                    new_name = template.format(season=season or "01", episode=episode or "01", cz_name=frt_name)
                else:
                    await original_message.reply_text(
                        "+4GB support not active. Contact owner @devil_testing_bot.",
                        reply_to_message_id=original_message.id
                    )
                    return
            else:
                template = await db.get_template(user_id) or "[S{season} Ep{episode}] {cz_name}"
                new_name = template.format(season=season or "01", episode=episode or "01", cz_name=frt_name)

            extn = await db.get_exten(user_id) or (file.file_name.rsplit(".", 1)[-1] if file.file_name else "unknown")
            new_name = f"{new_name}.{extn}"

            await process_rename(client, original_message, new_name)
            return

        if callback_data == "rename":
            if file_size > 1.9 * 1024 * 1024 * 1024:
                if ubot and ubot.is_connected:
                    await original_message.reply_text(
                        text=f"**__Please Enter New File Name...__**\n\n**Old File Name**: `{filename}`",
                        reply_to_message_id=original_message.id,
                        reply_markup=ForceReply(True)
                    )
                else:
                    await original_message.reply_text(
                        "+4GB support not active. Contact owner @devil_testing_bot.",
                        reply_to_message_id=original_message.id
                    )
            else:
                await original_message.reply_text(
                    text=f"**__Please Enter New File Name...__**\n\n**Old File Name**: `{filename}`",
                    reply_to_message_id=original_message.id,
                    reply_markup=ForceReply(True)
                )

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        await callback_query.message.reply_text(f"❌ An error occurred in rename callback: {e}")
                            
@pbot.on_message(filters.private & filters.reply)
async def refunc(client, message):
    try:
        reply_message = message.reply_to_message
        if reply_message.reply_markup and isinstance(reply_message.reply_markup, ForceReply):
            new_name = message.text
            await message.delete()           
            original = await client.get_messages(message.chat.id, reply_message.id)
            ori_msg = original.reply_to_message
            file = getattr(ori_msg, ori_msg.media.value)

            if "." not in new_name:
                extn = await db.get_exten(message.chat.id)
                if not extn:
                    extn = file.file_name.rsplit(".", 1)[-1] if file.file_name else "unknown"
                new_name = f"{new_name}.{extn}"

            file_path = f"downloads/{new_name}"
            await reply_message.delete()
            ms = await message.reply_text("📥 Downloading the file...")
            
            try:
                path = await client.download_media(message=ori_msg, file_name=file_path, progress=progress_for_pyrogram, progress_args=("Downloading...", ms, time.time()))
            except Exception as e:
                await ms.edit_text(f"❌ Download failed: {e}")
                return

            metadata = await db.get_metadata(message.chat.id)
            video_title = metadata.get("video")
            audio_title = metadata.get("audio")
            subtitle_title = metadata.get("subtitle")
            artist_title = metadata.get("artist")
            author_title = metadata.get("author")
            
            duration = 0
            try:
                meta = extractMetadata(createParser(file_path))
                if meta and meta.has("duration"):
                    duration = meta.get("duration").seconds
            except Exception as e:
                await ms.edit(f"❌ Error extracting metadata: {e}")
                return

            if not os.path.isdir("Metadata"):
                os.mkdir("Metadata")

            if file_path.endswith(('.mkv', '.mp4', '.mp3')):
                new_metadata_path = f"Metadata/{new_name}"
                metadata_dict = {
                    "video_title": video_title,
                    "audio_title": audio_title,
                    "subtitle_title": subtitle_title,
                    "artist": artist_title,
                    "author": author_title
                }
                updated_path = await change_metadata(input_path=path, output_path=new_metadata_path, metadata=metadata_dict, ms=ms)
            else:
                updated_path = file_path
                await ms.edit("⏳ File format not supported for metadata change, proceeding with upload ⚡")

            # Fetch caption and thumbnail
            c_caption = await db.get_caption(message.chat.id)
            c_thumb = await db.get_thumbnail(message.chat.id)

            if c_caption:
                try:
                    caption = c_caption.format(
                        filename=new_name,
                        filesize=humanbytes(file.file_size),
                        duration=convert(duration)
                    )
                except Exception as e:
                    await ms.edit(f"❌ Caption formatting error: {e}")
                    return
            else:
                caption = f"**{new_name}**"

            thumbnail_path = None
            if file.thumbs or c_thumb:
                try:
                    if c_thumb:
                        thumbnail_path = await client.download_media(c_thumb)
                    else:
                        thumbnail_path = await client.download_media(file.thumbs[0].file_id)

                    Image.open(thumbnail_path).convert("RGB").resize((320, 320)).save(thumbnail_path, "JPEG")
                except Exception as e:
                    await ms.edit(f"❌ Error processing thumbnail: {e}")
                    return

            # Determine upload parameters
            chat_id, verified = await get_chat_status(message.chat.id)
            value = 1.9 * 1024 * 1024 * 1024

            if file.file_size > value:
                fupload = USER_CHAT
                upload_client = ubot
            else:
                fupload = chat_id if chat_id and verified else message.chat.id
                upload_client = pbot

            await ms.edit("📤 Uploading the file...")

            upload_type = await db.get_uploadtype(message.chat.id) or "document"
            send_func = {
                "document": upload_client.send_document,
                "video": upload_client.send_video,
                "audio": upload_client.send_audio,
            }.get(upload_type)

            if not send_func:
                await ms.edit_text("❌ Invalid upload type selected.")
                return

            try:
                # Prepare keyword arguments dynamically
                kwargs = {
                    "chat_id": fupload,
                    "caption": caption,
                    "thumb": thumbnail_path,
                    "progress": progress_for_pyrogram,
                    "progress_args": ("Uploading...", ms, time.time()),
                }

                if upload_type == "document":
                    kwargs["document"] = updated_path
                elif upload_type == "video":
                    kwargs["video"] = updated_path
                    kwargs["duration"] = duration
                elif upload_type == "audio":
                    kwargs["audio"] = updated_path
                    kwargs["duration"] = duration

                suc = await send_func(**kwargs)

                if upload_client == ubot:
                    await pbot.copy_message(
                        chat_id=chat_id if chat_id and verified else message.chat.id,
                        from_chat_id=suc.chat.id,
                        message_id=suc.message_id
                    )

            except Exception as e:
                os.remove(updated_path)
                os.remove(file_path)
                if thumbnail_path:
                    os.remove(thumbnail_path)
                await ms.edit(f"❌ Upload error: {e}")
                return

            current_space_used = await db.get_space_used(message.chat.id)
            await db.set_space_used(message.chat.id, current_space_used + file.file_size)
            updated_space = await db.get_space_used(message.chat.id)
            if updated_space > MAX_SPACE:
                await db.set_filled_time(message.chat.id, datetime.now(IST).isoformat())

            await ms.delete()
            os.remove(updated_path)
            os.remove(file_path)
            if thumbnail_path:
                os.remove(thumbnail_path)

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(updated_path):
            os.remove(updated_path)
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
