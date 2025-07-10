import os
import time
import asyncio
from datetime import datetime
from pytz import timezone
from PIL import Image

from pyrogram import Client
from pyrogram.types import Message
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from plugins.chatid import get_chat_status
from Krito import ubot, pbot, USER_CHAT, MAX_SPACE

async def process_rename(client: Client, original_message: Message, new_name: str):
    try:
        file = getattr(original_message, original_message.media.value)
        file_path = f"downloads/{new_name}"
        ms = await original_message.reply_text("📥 Downloading the file...")

        try:
            path = await client.download_media(
                message=original_message, file_name=file_path,
                progress=progress_for_pyrogram, progress_args=("Downloading...", ms, time.time())
            )
        except Exception as e:
            await ms.edit_text(f"❌ Download failed: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        metadata = await db.get_metadata(original_message.chat.id)
        duration = 0

        try:
            meta = extractMetadata(createParser(file_path))
            if meta and meta.has("duration"):
                duration = meta.get("duration").seconds
        except:
            pass

        updated_path = file_path  # You can modify this if metadata processing is re-added

        c_caption = await db.get_caption(original_message.chat.id)
        c_thumb = await db.get_thumbnail(original_message.chat.id)
        caption = (
            c_caption.format(filename=new_name, filesize=humanbytes(file.file_size), duration=convert(duration))
            if c_caption else f"**{new_name}**"
        )

        thumbnail_path = None
        if c_thumb or (file.thumbs and file.thumbs[0].file_id):
            try:
                thumb_id = c_thumb or file.thumbs[0].file_id
                thumbnail_path = await client.download_media(thumb_id)
                Image.open(thumbnail_path).convert("RGB").resize((320, 320)).save(thumbnail_path, "JPEG")
            except:
                pass

        chat_id, verified = await get_chat_status(original_message.chat.id)
        is_big_file = file.file_size > 1.9 * 1024 * 1024 * 1024
        upload_client = ubot if is_big_file else pbot
        fupload = USER_CHAT if is_big_file else (chat_id if chat_id and verified else original_message.chat.id)

        await ms.edit("📤 Uploading the file...")

        upload_type = await db.get_uploadtype(original_message.chat.id) or "document"
        send_func = {
            "document": upload_client.send_document,
            "video": upload_client.send_video,
            "audio": upload_client.send_audio,
        }.get(upload_type)

        if not send_func:
            await ms.edit_text("❌ Invalid upload type selected.")
            return

        try:
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
                    chat_id=chat_id if chat_id and verified else original_message.chat.id,
                    from_chat_id=suc.chat.id,
                    message_id=suc.message_id
                )

        except Exception as e:
            await ms.edit(f"❌ Upload error: {e}")
            return

        # Update space
        IST = timezone("Asia/Kolkata")
        current_space_used = await db.get_space_used(original_message.chat.id)
        await db.set_space_used(original_message.chat.id, current_space_used + file.file_size)
        updated_space = await db.get_space_used(original_message.chat.id)
        if updated_space > MAX_SPACE:
            await db.set_filled_time(original_message.chat.id, datetime.now(IST).isoformat())

        await ms.delete()

    except Exception as e:
        await original_message.reply_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up files even if errors occur
        if os.path.exists(file_path):
            os.remove(file_path)
        if 'thumbnail_path' in locals() and thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
