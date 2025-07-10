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
