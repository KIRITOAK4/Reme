import os
import time
import asyncio
import shutil
from datetime import datetime
from pytz import timezone
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, ForceReply, CallbackQuery
from pymediainfo import MediaInfo

from helper.utils import progress_for_pyrogram, convert, humanbytes
from .metaedit import change_metadata
from helper.database import db
from plugins.chatid import get_chat_status
from Krito import ubot, pbot, USER_CHAT, MAX_SPACE

def create_temp_dir(user_id: int) -> str:
    ts = int(time.time() * 1000)
    path = f"downloads/{user_id}/{ts}"
    os.makedirs(path, exist_ok=True)
    return path

async def handle_metadata_info(client, cb: CallbackQuery, replied_msg):
    temp_path = None
    try:
        media = getattr(replied_msg, replied_msg.media.value, None)
        if not media or not media.file_name:
            await cb.answer("❌ Invalid media or missing filename.", show_alert=True)
            return

        msg = await cb.message.reply_text("📥 Downloading file for metadata...")
        temp_path = create_temp_dir(cb.from_user.id)
        file_path = os.path.join(temp_path, media.file_name)

        await client.download_media(
            message=replied_msg,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("Downloading...", msg, time.time())
        )

        media_info = MediaInfo.parse(file_path)
        if not media_info or not media_info.tracks:
            await msg.edit("❌ Failed to extract metadata.")
            return

        lines = []
        for track in media_info.tracks:
            lines.append(f"[{track.track_type}]")
            for key, value in track.to_data().items():
                if value:
                    lines.append(f"{key}: {value}")
            lines.append("")  # Add empty line between tracks

        txt_path = os.path.join(temp_path, f"{os.path.splitext(media.file_name)[0]}_metadata.txt")
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
        if temp_path and os.path.exists(temp_path):
            shutil.rmtree(temp_path, ignore_errors=True)

async def process_rename(client: Client, original_message: Message, new_name: str):
    user_id = original_message.from_user.id
    temp_path = create_temp_dir(user_id)
    try:
        file = getattr(original_message, original_message.media.value)
        file_path = os.path.join(temp_path, new_name)
        ms = await original_message.reply_text("📥 Downloading the file...")

        try:
            await client.download_media(
                message=original_message,
                file_name=file_path,
                progress=progress_for_pyrogram,
                progress_args=("Downloading...", ms, time.time())
            )
        except Exception as e:
            await ms.edit_text(f"❌ Download failed: {e}")
            return

        duration = 0
        try:
            media_info = MediaInfo.parse(file_path)
            for track in media_info.tracks:
                if track.track_type in ["Audio", "Video"] and track.duration:
                    duration = int(track.duration // 1000)
                    break
        except:
            pass

        await process_final_upload(client, original_message, file, file_path, new_name, duration, file_path, ms)

    except Exception as e:
        await original_message.reply_text(f"❌ An error occurred: {e}")
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)

@pbot.on_message(filters.private & filters.reply)
async def refunc(client: Client, message: Message):
    reply_message = message.reply_to_message
    if reply_message and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()

        original = await client.get_messages(message.chat.id, reply_message.id)
        ori_msg = original.reply_to_message
        file = getattr(ori_msg, ori_msg.media.value)

        extn = new_name.rsplit(".", 1)[-1] if "." in new_name else await db.get_exten(message.chat.id) or file.file_name.rsplit(".", 1)[-1]
        if "." not in new_name:
            new_name += f".{extn}"

        temp_path = create_temp_dir(message.from_user.id)
        file_path = os.path.join(temp_path, new_name)
        await reply_message.delete()
        ms = await message.reply_text("📥 Downloading the file...")
        try:
            await client.download_media(
                message=ori_msg,
                file_name=file_path,
                progress=progress_for_pyrogram,
                progress_args=("Downloading...", ms, time.time())
            )
        except Exception as e:
            await ms.edit(f"❌ Download failed: {e}")
            return

        duration = 0
        try:
            media_info = MediaInfo.parse(file_path)
            for track in media_info.tracks:
                if track.track_type in ["Audio", "Video"] and track.duration:
                    duration = int(track.duration // 1000)
                    break
            await ms.edit("✏️ Changing metadata...")
        except Exception as e:
            await ms.edit(f"❌ Metadata error: {e}")
            return

        metadata = await db.get_metadata(message.chat.id)
        if file_path.endswith(('.mkv', '.mp4', '.mp3')):
            os.makedirs("Metadata", exist_ok=True)
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

        await process_final_upload(client, message, file, updated_path, new_name, duration, file_path, ms)
        shutil.rmtree(temp_path, ignore_errors=True)

async def process_final_upload(client, message, file, updated_path, new_name, duration, file_path, ms):
    try:
        await ms.edit("📤 Uploading the file...")
        c_caption = await db.get_caption(message.chat.id)
        c_thumb = await db.get_thumbnail(message.chat.id)

        caption = c_caption.format(
            filename=new_name,
            filesize=humanbytes(file.file_size),
            duration=convert(duration)
        ) if c_caption else f"**{new_name}**"

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
