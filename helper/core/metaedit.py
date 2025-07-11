import os
import random
import asyncio
from helper.database import db
from helper.utils import progress_for_pyrogram
from Krito import ubot, pbot, USER_CHAT, MAX_SPACE


async def change_metadata(input_path, output_path, metadata, ms):
    """
    Adds metadata to the given video/audio file using ffmpeg.

    Parameters:
        input_path (str): Path to the input media file.
        output_path (str): Output path with metadata.
        metadata (dict): Metadata keys - video_title, author, subtitle_title, audio_title, artist.
        ms (Message): Pyrogram message object for status updates.
    """
    try:
        await ms.edit("⚙️ Adding metadata to the file...")

        command = [
            'ffmpeg', '-y', '-i', input_path, '-map', '0',
            '-c:s', 'copy', '-c:a', 'copy', '-c:v', 'copy',
            '-metadata', f'title={metadata.get("video_title", "")}',
            '-metadata', f'author={metadata.get("author", "")}',
            '-metadata:s:s', f'title={metadata.get("subtitle_title", "")}',
            '-metadata:s:a', f'title={metadata.get("audio_title", "")}',
            '-metadata', f'artist={metadata.get("artist", "")}',
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        print("===== FFmpeg STDERR =====\n", stderr.decode())
        print("===== FFmpeg STDOUT =====\n", stdout.decode())

        if os.path.exists(output_path):
            await ms.edit("✅ Metadata added successfully.")
            return output_path
        else:
            await ms.edit("❌ Metadata addition failed.")
            return None

    except Exception as e:
        await ms.reply_text(f"❌ Error adding metadata: `{e}`")
        return None


async def generate_sample(input_path, output_path, user_id, ms):
    """
    Generates a sample clip from the input video file using ffmpeg.

    Parameters:
        input_path (str): Path to the input video.
        output_path (str): Output path for the sample.
        user_id (int): User ID to fetch sample duration.
        ms (Message): Pyrogram message object for updates.
    """
    try:
        sample_duration = await db.get_sample_value(user_id)

        # Get total duration using ffprobe
        command = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(stderr.decode().strip() or "Error retrieving video duration.")

        total_duration = float(stdout.decode().strip())
        if sample_duration > total_duration:
            await ms.edit(f"❌ Requested sample duration ({sample_duration}s) is longer than video duration ({total_duration:.2f}s).")
            return None

        start_time = random.uniform(0, total_duration - sample_duration)

        # Generate sample
        await ms.edit("🎬 Generating sample...")
        command = [
            'ffmpeg', '-y', '-i', input_path, '-ss', str(start_time),
            '-t', str(sample_duration), '-c', 'copy', output_path
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if os.path.exists(output_path):
            await ms.edit("✅ Sample generated successfully.")
            return output_path
        else:
            raise Exception(stderr.decode().strip() or "Failed to generate sample.")

    except Exception as e:
        await ms.reply_text(f"❌ Error generating sample: `{e}`")
        return None
