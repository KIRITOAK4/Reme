import random
import time
import os
import asyncio
from helper.database import db
from pyrogram import Client
from pyrogram.types import Message
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from datetime import datetime, timedelta
from pytz import timezone
from helper.utils import progress_for_pyrogram, convert, humanbytes
from .chatid import get_chat_status
from Krito import ubot, pbot, USER_CHAT, MAX_SPACE

async def change_metadata(input_path, output_path, metadata, ms):
    """
    Adds metadata to the given video file using ffmpeg.

    Parameters:
        input_path (str): Path to the input video file.
        output_path (str): Path to save the output video file with metadata.
        metadata (dict): Metadata dictionary containing keys like 'title', 'author', etc.
        ms (Message): Pyrogram message object for progress updates.
    """
    try:
        await ms.edit("Adding Metadata to the file...")
        command = [
            'ffmpeg', '-y', '-i', input_path, '-map', '0', '-c:s', 'copy', '-c:a', 'copy', '-c:v', 'copy',
            '-metadata', f'title={metadata["video_title"]}',
            '-metadata', f'author={metadata["author"]}',
            '-metadata:s:s', f'title={metadata["subtitle_title"]}',
            '-metadata:s:a', f'title={metadata["audio_title"]}',
            '-metadata', f'artist={metadata["artist"]}',
            output_path
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        print(e_response)
        print(t_response)

        if os.path.exists(output_path):
            await ms.edit("Metadata added successfully ✅")
            return output_path
        else:
            raise Exception("Failed to add metadata")
    except Exception as e:
        await ms.reply_text(f"Error adding metadata: {e}>")
        return None

async def generate_sample(input_path, output_path, user_id, ms):
    """
    Generates a sample clip from the input video file based on user-defined duration.

    Parameters:
        input_path (str): Path to the input video file.
        output_path (str): Path to save the sample clip.
        user_id (int): User ID to fetch the sample duration.
        ms (Message): Pyrogram message object for progress updates.
    """
    try:
        # Fetch sample duration from the database
        sample_duration = await db.get_sample_value(user_id)

        # Get video duration using ffprobe
        command = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(stderr.decode().strip() or "Error retrieving video duration.")

        total_duration = float(stdout.decode().strip())

        # Ensure the sample duration doesn't exceed the video duration
        if sample_duration > total_duration:
            await ms.edit(f"❌ The requested sample duration ({sample_duration}s) is longer than the total video duration ({total_duration}s).")
            return None

        start_time = random.uniform(0, total_duration - sample_duration)  # Start at a random point in the video

        # Generate sample using ffmpeg
        await ms.edit("Generating sample...")
        command = [
            'ffmpeg', '-y', '-i', input_path, '-ss', str(start_time),
            '-t', str(sample_duration), '-c', 'copy', output_path
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if os.path.exists(output_path):
            await ms.edit("Sample generated successfully ✅")
            return output_path
        else:
            raise Exception(stderr.decode().strip() or "Failed to generate sample.")
    
    except Exception as e:
        await ms.reply_text(f"❌ Error generating sample: {e}")
        return None

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
            return

        metadata = await db.get_metadata(original_message.chat.id)
        duration = 0

        try:
            meta = extractMetadata(createParser(file_path))
            if meta and meta.has("duration"):
                duration = meta.get("duration").seconds
        except:
            pass

        # Change metadata for specific file types
        # if file_path.endswith(('.mkv', '.mp4', '.mp3')):
        #     updated_path = await change_metadata(input_path=file_path, output_path=f"Metadata/{new_name}", metadata=metadata, ms=ms)
        # else:
        updated_path = file_path

        # Get user-defined caption and thumbnail
        c_caption = await db.get_caption(original_message.chat.id)
        c_thumb = await db.get_thumbnail(original_message.chat.id)
        caption = c_caption.format(filename=new_name, filesize=humanbytes(file.file_size), duration=convert(duration)) if c_caption else f"**{new_name}**"

        # Download thumbnail (if available)
        thumbnail_path = None
        if c_thumb or (file.thumbs and file.thumbs[0].file_id):
            try:
                thumb_id = c_thumb or file.thumbs[0].file_id
                thumbnail_path = await client.download_media(thumb_id)
                Image.open(thumbnail_path).convert("RGB").resize((320, 320)).save(thumbnail_path, "JPEG")
            except:
                pass

        # Determine upload client based on file size
        chat_id, verified = await get_chat_status(original_message.chat.id)
        value = 1.9 * 1024 * 1024 * 1024

        if file.file_size > value:
            fupload = USER_CHAT
            upload_client = ubot
        else:
            fupload = chat_id if chat_id and verified else original_message.chat.id
            upload_client = pbot

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
                    chat_id=chat_id if chat_id and verified else original_message.chat.id,
                    from_chat_id=suc.chat.id,
                    message_id=suc.message_id
                )

        except Exception as e:
            await ms.edit(f"❌ Upload error: {e}")
            return

        # Update storage usage in DB
        IST = timezone("Asia/Kolkata")
        current_space_used = await db.get_space_used(original_message.chat.id)
        await db.set_space_used(original_message.chat.id, current_space_used + file.file_size)
        updated_space = await db.get_space_used(message.chat.id)
        if updated_space > MAX_SPACE:
            await db.set_filled_time(message.chat.id, datetime.now(IST).isoformat())
                

        await ms.delete()

        # Cleanup files
        os.remove(updated_path)
        if thumbnail_path:
            os.remove(thumbnail_path)

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {e}")
        
