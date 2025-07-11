import os
import time
import asyncio
from datetime import datetime
from pytz import timezone
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, ForceReply, CallbackQuery
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, convert, humanbytes
from .metaedit import change_metadata
from helper.database import db
from plugins.chatid import get_chat_status
from Krito import ubot, pbot, USER_CHAT, MAX_SPACE

async def handle_metadata_info(client, cb: CallbackQuery, replied_msg):
    txt_path = None
    try:
        media = getattr(replied_msg, replied_msg.media.value, None)
        if not media or not media.file_name:
            await cb.answer("❌ Invalid media or missing filename.", show_alert=True)
            return

        # Download file
        msg = await cb.message.reply_text("📥 Downloading file for metadata...")
        file_path = f"downloads/{media.file_name}"

        path = await client.download_media(
            message=replied_msg,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("Downloading...", msg, time.time())
        )

        # Extract metadata
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if not metadata:
            await msg.edit("❌ Failed to extract metadata.")
            return

        lines = metadata.exportPlaintext()  # Safe list of readable metadata lines
        txt_path = f"downloads/{os.path.splitext(media.file_name)[0]}_metadata.txt"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        await client.send_document(
            chat_id=cb.message.chat.id,
            document=txt_path,
            caption="📄 Metadata Info"
        )
        await msg.delete()

    except Exception as e:
        await cb.message.reply_text(f"❌ Metadata error: {e}")

    finally:
        # Clean up
        if txt_path and os.path.exists(txt_path):
            os.remove(txt_path)
        if os.path.exists(file_path):
            os.remove(file_path)

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

        updated_path = file_path
        await process_final_upload(client, original_message, file, updated_path, new_name, duration, file_path, ms)

    except Exception as e:
        await original_message.reply_text(f"❌ An error occurred: {e}")

@pbot.on_message(filters.private & filters.reply)
async def refunc(client: Client, message: Message):
    reply_message = message.reply_to_message
    if reply_message and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()

        original = await client.get_messages(message.chat.id, reply_message.id)
        ori_msg = original.reply_to_message
        file = getattr(ori_msg, ori_msg.media.value)

        if "." not in new_name:
            extn = await db.get_exten(message.chat.id) or file.file_name.rsplit(".", 1)[-1]
            new_name = f"{new_name}.{extn}"

        file_path = f"downloads/{new_name}"
        updated_path = None
        thumbnail_path = None

        ms = await message.reply_text("📥 Downloading the file...")
        try:
            path = await client.download_media(
                message=ori_msg, file_name=file_path,
                progress=progress_for_pyrogram,
                progress_args=("Downloading...", ms, time.time())
            )
        except Exception as e:
            await ms.edit(f"❌ Download failed: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        duration = 0  # fail-safe default
        try:
            meta = extractMetadata(createParser(file_path))
            if meta and meta.has("duration"):
                duration = meta.get("duration").seconds
            await ms.edit("✏️ Changing metadata...")
        except Exception as e:
            await ms.edit(f"❌ Metadata error: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        metadata = await db.get_metadata(message.chat.id)
        if file_path.endswith(('.mkv', '.mp4', '.mp3')):
            if not os.path.exists("Metadata"):
                os.mkdir("Metadata")
            updated_path = f"Metadata/{new_name}"
            metadata_dict = {
                "video_title": metadata.get("video"),
                "audio_title": metadata.get("audio"),
                "subtitle_title": metadata.get("subtitle"),
                "artist": metadata.get("artist"),
                "author": metadata.get("author")
            }
            updated_path = await change_metadata(file_path, updated_path, metadata_dict, ms)
            if not updated_path:
                return
        else:
            updated_path = file_path
            await ms.edit("⏳ File format not supported for metadata change, proceeding with upload ⚡")

        await process_final_upload(client, message, file, updated_path, new_name, duration, file_path)

async def process_final_upload(client, message, file, updated_path, new_name, duration, file_path, ms):
    try:
        await ms.edit("📤 Uploading the file...")

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
                raise Exception(f"Caption formatting error: {e}")
        else:
            caption = f"**{new_name}**"

        thumbnail_path = None
        if file.thumbs or c_thumb:
            try:
                thumb_id = c_thumb or file.thumbs[0].file_id
                thumbnail_path = await client.download_media(thumb_id)
                Image.open(thumbnail_path).convert("RGB").resize((320, 320)).save(thumbnail_path, "JPEG")
            except Exception as e:
                raise Exception(f"Thumbnail error: {e}")

        chat_id, verified = await get_chat_status(message.chat.id)
        is_big_file = file.file_size > 1.9 * 1024 * 1024 * 1024
        upload_client = ubot if is_big_file else pbot
        fupload = USER_CHAT if is_big_file else (chat_id if chat_id and verified else message.chat.id)

        upload_type = await db.get_uploadtype(message.chat.id) or "document"
        send_func = {
            "document": upload_client.send_document,
            "video": upload_client.send_video,
            "audio": upload_client.send_audio,
        }.get(upload_type)

        if not send_func:
            raise Exception("Invalid upload type selected")

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

        IST = timezone("Asia/Kolkata")
        used = await db.get_space_used(message.chat.id)
        await db.set_space_used(message.chat.id, used + file.file_size)

        if used + file.file_size > MAX_SPACE:
            await db.set_filled_time(message.chat.id, datetime.now(IST).isoformat())

        await ms.delete()

    finally:
        if os.path.exists(updated_path):
            os.remove(updated_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        if 'thumbnail_path' in locals() and thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
