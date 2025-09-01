import re
import time
import os
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import (
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaDocument,
    InputMediaVideo,
    InputMediaAnimation,
    InputMediaAudio
)
from helper.token import validate_user
from Krito import pbot


@pbot.on_message(filters.private & filters.command("editmedia"))
async def edit_media(client, message):
    replied_message = message.reply_to_message

    # Ensure the command is replied to a media message
    if not replied_message:
        await message.reply_text("⚠️ Please reply to the media you want to edit and provide a Telegram message URL.")
        return

    try:
        # ✅ Validate user using validate_user
        error_msg, button = await validate_user(message)
        if error_msg:
            await message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(button))
            return
    except Exception as e:
        await message.reply_text(f"⚠️ Validation error: {e}")
        return

    try:
        # ✅ Extract URL
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            await message.reply_text("⚠️ Please provide a valid Telegram message URL.")
            return
        url = parts[1].strip()

        # ✅ Patterns for Telegram URLs
        pattern_private = r"(?:https?://)?t\.me/c/(\d+)/(\d+)"
        pattern_public = r"(?:https?://)?t\.me/([\w\d_]+)/(\d+)"

        chatid = None
        msg_id = None

        if re.match(pattern_private, url):
            match = re.match(pattern_private, url)
            chatid = int("-100" + match.group(1))
            msg_id = int(match.group(2))
        elif re.match(pattern_public, url):
            match = re.match(pattern_public, url)
            chatid = match.group(1)
            msg_id = int(match.group(2))

        if not chatid or not msg_id:
            await message.reply_text("⚠️ Invalid URL format.")
            return

        # ✅ Validate user permissions in target chat
        user_id = message.from_user.id
        try:
            member = await client.get_chat_member(chat_id=chatid, user_id=user_id)
        except Exception:
            await message.reply_text("⚠️ You are not a member of that channel/group.")
            return

        if member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            await message.reply_text("⚠️ You don't have permission to edit messages in that chat.")
            return

        # ✅ Detect media type for editing
        if replied_message.photo:
            media = InputMediaPhoto(media=replied_message.photo.file_id, caption=replied_message.caption or "")
        elif replied_message.document:
            media = InputMediaDocument(media=replied_message.document.file_id, caption=replied_message.caption or "")
        elif replied_message.video:
            media = InputMediaVideo(media=replied_message.video.file_id, caption=replied_message.caption or "")
        elif replied_message.animation:
            media = InputMediaAnimation(media=replied_message.animation.file_id, caption=replied_message.caption or "")
        elif replied_message.audio:
            media = InputMediaAudio(media=replied_message.audio.file_id, caption=replied_message.caption or "")
        else:
            await message.reply_text("⚠️ Unsupported media type.")
            return

        # ✅ Edit message media
        try:
            await client.edit_message_media(chat_id=chatid, message_id=msg_id, media=media)
            await message.reply_text("✅ Message edited successfully.")
        except Exception as e:
            await message.reply_text(f"⚠️ Failed to edit message: {e}")

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")
    if replied_message.photo:
        media = InputMediaPhoto(media=replied_message.photo.file_id, caption=replied_message.caption and replied_message.caption.html)
    elif replied_message.document:
        media = InputMediaDocument(media=replied_message.document.file_id, caption=replied_message.caption and replied_message.caption.html)
    elif replied_message.video:
        media = InputMediaVideo(media=replied_message.video.file_id, caption=replied_message.caption and replied_message.caption.html)
    elif replied_message.animation:
        media = InputMediaAnimation(media=replied_message.animation.file_id, caption=replied_message.caption and replied_message.caption.html)
    elif replied_message.audio:
        media = InputMediaAudio(media=replied_message.audio.file_id, caption=replied_message.caption and replied_message.caption.html)
    else:
        await message.reply_text("⚠️ Unsupported media type.")
        return

    try:
        # Extract URL and parse it
        url = message.text.split(" ", 1)[1]
        chatid = None
        msg_id = None

        if "t.me" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                if "c" in parts[3]:
                    chatid = int("-100" + parts[4])
                    msg_id = int(parts[5])
                else:
                    chatid = parts[3]
                    msg_id = int(parts[4])

        # Verify if user and bot have sufficient permissions
        if chatid and msg_id:
            try:
                is_admin = await client.get_chat_member(chat_id=chatid, user_id=user_id)
            except UserNotParticipant:
                await message.reply_text("⚠️ You are not a member of this channel, so you can't edit this message.")
                return

            # Check user permissions
            if is_admin.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
                try:
                    await client.edit_message_media(chat_id=chatid, message_id=msg_id, media=media)
                    await message.reply_text("✅ Message edited successfully.")
                except Exception as e:
                    await message.reply_text(f"⚠️ Failed to edit message: {str(e)}")
            else:
                await message.reply_text("⚠️ You don't have the permission to edit messages in this channel.")
        else:
            await message.reply_text("⚠️ Invalid URL format.")
    except IndexError:
        await message.reply_text("⚠️ Please provide a valid URL.")
    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred: {e}")
