import os
import random
import asyncio
from helper.database import db
from helper.utils import progress_for_pyrogram


async def change_metadata(input_path, output_path, metadata, ms):
    """
    Adds metadata to video/audio file using ffmpeg.

    :param input_path: Path to input file.
    :param output_path: Destination file with metadata added.
    :param metadata: Dictionary with optional keys: video_title, author, subtitle_title, audio_title, artist.
    :param ms: Pyrogram Message object to send status.
    :return: Path to updated file or None on failure.
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
            raise Exception("Failed to add metadata")

    except Exception as e:
        await ms.reply_text(f"❌ Error adding metadata: `{e}`")
        return None


async def generate_sample(input_path, output_path, user_id, ms):
    """
    Creates a sample clip from video using ffmpeg.

    :param input_path: Source file path.
    :param output_path: Where to save the sample clip.
    :param user_id: Telegram user ID to fetch sample duration preference.
    :param ms: Message for update/status.
    :return: Sample path or None on failure.
    """
    try:
        sample_duration = await db.get_sample_value(user_id)

        # Fetch total duration of input file
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
            await ms.edit(f"❌ Sample duration ({sample_duration}s) > video duration ({total_duration:.2f}s).")
            return None

        start_time = random.uniform(0, total_duration - sample_duration)

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
            raise Exception(stderr.decode().strip() or "Sample generation failed.")

    except Exception as e:
        await ms.reply_text(f"❌ Error generating sample: `{e}`")
        return None
