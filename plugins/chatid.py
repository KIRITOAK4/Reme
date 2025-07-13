import asyncio
from Krito import pbot
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

# In-memory storage for temporary user chat ID verification
base_dir = {}

# /set_chatid <chat_id>
@pbot.on_message(filters.private & filters.command('set_chatid'))
async def set_chatid_command(client, message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2 or not args[1].lstrip("-").isdigit():
        return await message.reply_text(
            "⚠️ Please provide a valid numeric chat ID.\nUsage: `/set_chatid <chat_id>`", quote=True
        )

    chat_id = int(args[1])

    # Attempt to join the chat to verify presence
    try:
        await client.get_chat(chat_id)
    except Exception as e:
        return await message.reply_text(f"❌ Invalid or inaccessible chat ID.\nError: {e}")

    # Temporarily store and wait for verification
    base_dir[user_id] = {"chat_id": chat_id, "verified": False}

    await message.reply_text(
        "✅ Chat ID set.\nVerify within 60 seconds using `/verify`.",
        quote=True
    )

    await asyncio.sleep(60)

    # Cleanup after timeout if still unverified
    if base_dir.get(user_id, {}).get("verified") is False:
        base_dir.pop(user_id, None)
        try:
            await client.leave_chat(chat_id)
        except Exception:
            pass
        await message.reply_text("❌ Verification timeout. Chat ID has been cleared.")

# /verify
@pbot.on_message(filters.private & filters.command('verify'))
async def verify_command(client, message):
    user_id = message.from_user.id
    data = base_dir.get(user_id)

    if not data:
        return await message.reply_text("❌ Please set a chat ID first using `/set_chatid <chat_id>`.")

    chat_id = data.get("chat_id")

    # Check if bot is admin
    try:
        bot_member = await client.get_chat_member(chat_id, "me")
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            base_dir.pop(user_id, None)
            await client.leave_chat(chat_id)
            return await message.reply_text("❌ Bot is not an admin. Left the chat and reset chat ID.")
    except Exception as e:
        base_dir.pop(user_id, None)
        await client.leave_chat(chat_id)
        return await message.reply_text(f"❌ Couldn't verify bot status. Left the chat.\nError: {e}")

    # Check if user is admin or owner
    try:
        user_member = await client.get_chat_member(chat_id, user_id)
        if user_member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            base_dir.pop(user_id, None)
            await client.leave_chat(chat_id)
            return await message.reply_text("❌ You must be an admin or owner. Left the chat and reset chat ID.")
    except Exception:
        base_dir.pop(user_id, None)
        await client.leave_chat(chat_id)
        return await message.reply_text("❌ You are not a member of that chat. Left and reset.")

    # Passed all checks — verified
    base_dir[user_id]["verified"] = True
    await message.reply_text("✅ Verified successfully! Both you and the bot are admins.")

# Helper
async def get_chat_status(user_id):
    data = base_dir.get(user_id)
    if data:
        return data.get("chat_id", "None"), data.get("verified", False)
    return "None", False
    
