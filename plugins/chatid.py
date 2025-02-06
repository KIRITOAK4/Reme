import asyncio
from Krito import pbot
from pyrogram.enums import ChatMemberStatus
from pyrogram import filters

# Base directory to store temporary user data
base_dir = {}

# Command to set the chat ID
@pbot.on_message(filters.private & filters.command('set_chatid'))
async def set_chatid_command(client, message):
    try:
        chat_id = int(message.text.split(" ", 1)[1])
        base_dir[message.from_user.id] = {"chat_id": chat_id, "verified": False}
        await message.reply_text(
            "✅ Chat ID has been set successfully.\nPlease use /verify command within 60 seconds to complete the process.",
            reply_to_message_id=message.id
        )
        await asyncio.sleep(60)
        if message.from_user.id in base_dir and not base_dir[message.from_user.id]["verified"]:
            await client.leave_chat(chat_id)
            del base_dir[message.from_user.id]
            await message.reply_text("❌ Verification failed. Chat ID has been reset.")
    except ValueError:
        await message.reply_text("⚠️ Error: Invalid chat ID. Please provide a numeric value.", reply_to_message_id=message.id)
    except IndexError:
        await message.reply_text("⚠️ Error: Please provide a valid chat ID.\nUsage: /set_chatid <chat_id>", reply_to_message_id=message.id)
    except Exception as e:
        await message.reply_text(f"⚠️ An unexpected error occurred: {e}", reply_to_message_id=message.id)

# Command to verify if the bot and user are both admins in the chat
@pbot.on_message(filters.private & filters.command('verify'))
async def verify_command(client, message):
    try:
        user_data = base_dir.get(message.from_user.id)  # Retrieve user data
        if not user_data:
            await message.reply_text("❌ You need to set the chat ID first using /set_chatid.")
            return

        chat_id = user_data["chat_id"]
        bot_member = await client.get_chat_member(chat_id, "me")
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            await message.reply_text("❌ Verification failed. Bot must be an admin in the group or channel.")
            return
        try:
            user_member = await client.get_chat_member(chat_id, message.from_user.id)
        except Exception:
            await message.reply_text("❌ Verification failed. You are not a member of the specified group or channel.")
            return
        if user_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            base_dir[message.from_user.id]["verified"] = True
            await message.reply_text("✅ Verification successful! Both you and the bot are admins.")
        else:
            await message.reply_text(
                "❌ Verification failed. You must be an admin or owner of the specified group or channel."
            )
    except Exception as e:
        await message.reply_text(f"⚠️ An error occurred during verification: {e}")

async def get_chat_status(user_id):
    user_data = base_dir.get(user_id)  # Replace `base_dir` with your persistent storage
    if user_data:
        chat_id = user_data.get("chat_id", None)
        verified = user_data.get("verified", False)
        return chat_id, verified
    return "None", False
