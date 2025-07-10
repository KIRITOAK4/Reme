import os
import time
import asyncio
from pyrogram.types import ForceReply
from helper.utils import progress_for_pyrogram
from helper.database import db
from .metaedit import generate_sample, process_rename
from Krito import ubot

async def handle_sample(client, cb, file, original_msg):
    if not file.file_name.endswith((".mkv", ".mp4")):
        await cb.answer("❌ Only .mkv or .mp4 files are supported.", show_alert=True)
        return

    user_id = cb.from_user.id
    sample_duration = await db.get_sample_value(user_id)
    if not sample_duration:
        await cb.answer("❌ Sample duration not set. Use /settings to configure.", show_alert=True)
        return

    input_path = f"downloads/{file.file_name}"
    output_path = f"downloads/sample_{os.path.splitext(file.file_name)[0]}.mp4"
    status = await cb.message.reply_text("📥 Downloading the file...")

    try:
        file_path = await client.download_media(
            original_msg,
            file_name=input_path,
            progress=progress_for_pyrogram,
            progress_args=("Downloading...", status, time.time())
        )
    except Exception as e:
        await status.edit(f"❌ Download failed: {e}")
        return

    sample_path = await generate_sample(input_path, output_path, user_id, status)
    if not sample_path:
        return

    await status.edit("📤 Uploading the sample...")
    try:
        await client.send_video(cb.message.chat.id, sample_path, caption="🎥 Sample Preview")
        await status.delete()
    except Exception as e:
        await status.edit(f"❌ Upload failed: {e}")
    finally:
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)

async def handle_auto_rename(client, cb, file, original_msg, season, episode, base_name):
    user_id = cb.from_user.id
    file_size = file.file_size

    template = await db.get_template(user_id) or "[S{season} Ep{episode}] {cz_name}"
    extn = await db.get_exten(user_id) or file.file_name.rsplit(".", 1)[-1]
    new_name = template.format(season=season or "01", episode=episode or "01", cz_name=base_name)
    new_name = f"{new_name}.{extn}"

    if file_size > 3.2 * 1024 * 1024 * 1024:
        await original_msg.reply_text("❌ This bot doesn't support files larger than 3.2GB.")
        return

    if file_size > 1.9 * 1024 * 1024 * 1024:
        if not (ubot and ubot.is_connected):
            await original_msg.reply_text(
                "+4GB support not active. Contact owner @devil_testing_bot.",
                reply_to_message_id=original_msg.id
            )
            return

    await process_rename(client, original_msg, new_name)

async def handle_rename(client, cb, file, original_msg):
    file_size = file.file_size
    filename = file.file_name

    if file_size > 3.2 * 1024 * 1024 * 1024:
        await original_msg.reply_text("❌ This bot doesn't support files larger than 3.2GB.")
        return

    if file_size > 1.9 * 1024 * 1024 * 1024:
        if not (ubot and ubot.is_connected):
            await original_msg.reply_text(
                "+4GB support not active. Contact owner @devil_testing_bot.",
                reply_to_message_id=original_msg.id
            )
            return

    await original_msg.reply_text(
        f"**__Please Enter New File Name...__**\n\n**Old File Name**: `{filename}`",
        reply_to_message_id=original_msg.id,
        reply_markup=ForceReply(True)
                               )
  
