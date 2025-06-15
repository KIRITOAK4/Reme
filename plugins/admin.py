import os
import sys
import time
import io
import asyncio
import logging
import datetime
from pytz import timezone
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from helper.database import db
from helper.utils import humanbytes, split_and_send_message
from Krito import pbot, ADMIN, LOG_CHANNEL, BOT_UPTIME
from Krito.txt import Txt

# === LOGGER ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IST = timezone("Asia/Kolkata")

# ==================== fetch
@pbot.on_message(filters.command("fetch"))
async def fetch_user_data(client, message: Message):
    if message.from_user.id not in ADMIN:
        return await message.reply_text("🛑 Whom do you think you are?", reply_to_message_id=message.id)

    args = message.text.strip().split()
    if len(args) != 2:
        return await message.reply_text("⚠️ Usage: `/fetch <user_id|all>`", quote=True)

    target = args[1]
    data_list = []

    if target == "all":
        async for user in db.col.find({}):
            data_list.append(user)
    elif target.isdigit():
        user = await db.col.find_one({"_id": int(target)})
        if not user:
            return await message.reply_text("❌ User not found in the database.", quote=True)
        data_list.append(user)
    else:
        return await message.reply_text("⚠️ Invalid argument. Use user ID or `all`.", quote=True)

    final_text = ""
    for user_data in data_list:
        uid = user_data.get("_id")
        final_text += f"📄 User Data for ID {uid}:\n\n"
        for key, value in user_data.items():
            if key == "_id":
                continue
            if key == "filled_at" and value:
                try:
                    value = datetime.datetime.fromisoformat(value).astimezone(IST).isoformat()
                except:
                    pass
            if key == "time" and value:
                try:
                    value = datetime.datetime.fromtimestamp(float(value), IST).isoformat()
                except:
                    pass
            if key == "space_used":
                value = humanbytes(value)
            final_text += f"{key}: {value}\n"
        final_text += "\n" + "=" * 40 + "\n\n"

    file = io.BytesIO(final_text.encode("utf-8"))
    file.name = "user_data.txt"
    await message.reply_document(file, caption="📦 Here's the user data.")

# ==================== stats / status
@pbot.on_message(filters.command(["stats", "status"]))
async def get_stats(bot, message):
    if message.from_user.id not in ADMIN:
        return await message.reply_text("🛑 Whom do you think you are?", reply_to_message_id=message.id)

    total_users = await db.total_users_count()
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - BOT_UPTIME))
    start_t = time.time()
    st = await message.reply('**Aᴄᴄᴇssɪɴɢ Tʜᴇ Dᴇᴛᴀɪʟs.....**')
    time_taken_s = (time.time() - start_t) * 1000
    await st.edit(text=f"**--Bᴏᴛ Sᴛᴀᴛᴜꜱ--** \n\n**⌚️ Bᴏᴛ Uᴩᴛɪᴍᴇ:** {uptime} \n**🐌 Cᴜʀʀᴇɴᴛ Pɪɴɢ:** `{time_taken_s:.3f} ᴍꜱ` \n**👭 Tᴏᴛᴀʟ Uꜱᴇʀꜱ:** `{total_users}`")

# ==================== fetch_user
@pbot.on_message(filters.command("fetch_user"))
async def fetch_users(client, message):
    if message.from_user.id not in ADMIN:
        return await message.reply_text("🛑 Whom do you think you are?", reply_to_message_id=message.id)

    users = await db.get_all_users()
    total_space = 0
    user_data = []

    async for user in users:
        user_id = user["_id"]
        space_used = user.get("space_used", 0)
        filled_at = user.get("filled_at")

        if space_used > 0:
            total_space += space_used
            if filled_at:
                try:
                    dt = datetime.datetime.fromisoformat(filled_at)
                    filled_at_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    filled_at_str = str(filled_at)
                user_data.append(f"User: {user_id}, Space Used: {humanbytes(space_used)}, Filled At: {filled_at_str}")
            else:
                user_data.append(f"User: {user_id}, Space Used: {humanbytes(space_used)}")

    response = "\n".join(user_data) + f"\n\nTotal Space Used: {humanbytes(total_space)}" if user_data else "No users have used storage."
    await split_and_send_message(message, response)

# ==================== restart
@pbot.on_message(filters.private & filters.command("restart"))
async def restart_bot(b, m):
    if m.from_user.id not in ADMIN:
        return await m.reply_text("🛑 Whom do you think you are?", reply_to_message_id=m.id)
    await m.reply_text("🔄__Restarting...__")
    os.execl(sys.executable, sys.executable, *sys.argv)

# ==================== reset_time
@pbot.on_message(filters.command("reset_time"))
async def reset_space(client, message):
    if message.from_user.id not in ADMIN:
        return await message.reply_text("🛑 Whom do you think you are?", reply_to_message_id=message.id)
    try:
        command_parts = message.text.split()

        if len(command_parts) == 2 and command_parts[1].lower() == "all":
            all_users_cursor = await db.get_all_users()
            async for user in all_users_cursor:
                user_id = user["_id"]
                await db.set_space_used(user_id, 0)
                await db.reset_filled_time(user_id)
                try:
                    await pbot.send_message(user_id, "✅ Your used space and limit lock has been reset. You can upload again.")
                except Exception as e:
                    await message.reply_text(f"❌ Failed to notify user {user_id}. Error: {e}")
            return await message.reply_text("✅ Space usage and reset time cleared for all users.")

        elif len(command_parts) == 2:
            user_id = int(command_parts[1])
            current_space_used = await db.get_space_used(user_id)
            if current_space_used is None:
                return await message.reply_text(f"⚠️ No data found for user {user_id}.")
            await db.set_space_used(user_id, 0)
            await db.reset_filled_time(user_id)
            await message.reply_text(f"✅ User {user_id}'s space and reset time have been cleared.\n(Previous usage: {current_space_used} bytes)")
            try:
                await pbot.send_message(user_id, "✅ Your used space and limit lock has been reset. You can upload again.")
            except Exception as e:
                await message.reply_text(f"❌ Failed to notify user {user_id}. Error: {e}")
        else:
            await message.reply_text("⚠️ Invalid format! Use: `/reset_time <user_id>` or `/reset_time all`")

    except ValueError:
        await message.reply_text("⚠️ Invalid user ID format. Please provide a valid user ID.")
    except Exception as e:
        await message.reply_text(f"❌ An error occurred while resetting space usage: {e}")

# ==================== update_metadata
@pbot.on_message(filters.command("update_metadata"))
async def update_db_command(client, message):
    if message.from_user.id not in ADMIN:
        return await message.reply_text("🛑 Whom do you think you are?", reply_to_message_id=message.id)
    try:
        await db.update_db()
        await message.reply_text("Field for old users has been updated successfully.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

# ==================== broadcast
@pbot.on_message(filters.reply & filters.command("broadcast"))
async def broadcast_handler(bot: Client, m: Message):
    if m.from_user.id not in ADMIN:
        return await m.reply_text("🛑 Whom do you think you are?", reply_to_message_id=m.id)

    await bot.send_message(LOG_CHANNEL, f"{m.from_user.mention} or {m.from_user.id} Iꜱ ꜱᴛᴀʀᴛᴇᴅ ᴛʜᴇ Bʀᴏᴀᴅᴄᴀꜱᴛ......")
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    sts_msg = await m.reply_text("Bʀᴏᴀᴅᴄᴀꜱᴛ Sᴛᴀʀᴛᴇᴅ..!") 
    done, failed, success = 0, 0, 0
    start_time = time.time()
    total_users = await db.total_users_count()

    async for user in all_users:
        sts = await send_msg(user['_id'], broadcast_msg)
        if sts == 200:
            success += 1
        else:
            failed += 1
        if sts == 400:
            await db.delete_user(user['_id'])
        done += 1
        if done % 20 == 0:
            await sts_msg.edit(f"Bʀᴏᴀᴅᴄᴀꜱᴛ Iɴ Pʀᴏɢʀᴇꜱꜱ:\nTᴏᴛᴀʟ Uꜱᴇʀꜱ: {total_users}\nCᴏᴍᴩʟᴇᴛᴇᴅ: {done}/{total_users}\nSᴜᴄᴄᴇꜱꜱ: {success}\nFᴀɪʟᴇᴅ: {failed}")

    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts_msg.edit(f"Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ:\nCᴏᴍᴩʟᴇᴛᴇᴅ Iɴ `{completed_in}`\n\nTᴏᴛᴀʟ Uꜱᴇʀꜱ: {total_users}\nCᴏᴍᴩʟᴇᴛᴇᴅ: {done}/{total_users}\nSᴜᴄᴄᴇꜱꜱ: {success}\nFᴀɪʟᴇᴅ: {failed}")

# ==================== send_msg
async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=int(user_id))
        return 200
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await send_msg(user_id, message)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        logger.info(f"{user_id} : User issue (deactivated/blocked/invalid ID)")
        return 400
    except Exception as e:
        logger.error(f"{user_id} : {e}")
        return 500

# ==================== /fadd ====================
@pbot.on_message(filters.command("fadd"))
async def force_add_multiple_fields(client, message: Message):
    if message.from_user.id not in ADMIN:
        return await message.reply_text("🛑 Whom do you think you are?", reply_to_message_id=message.id)

    args = message.text.split(maxsplit=2)

    if len(args) < 3:
        return await message.reply_text(
            "**⚠️ Usage:**\n"
            "`/fadd <user_id> field=value field2=value2 ...`\n\n"
            "**🔧 Example:**\n"
            "`/fadd 123456789 chat_id=None file_id=None caption=None token=None time=None exten=None template=None sample_value=0 space_used=0 filled_at=None uploadtype=None`",
            quote=True
        )

    try:
        user_id = int(args[1])
        field_data_raw = args[2].split()

        update_data = {}
        for item in field_data_raw:
            if '=' not in item:
                continue
            key, val = item.split('=', 1)
            val = val.strip()
            if val.lower() == 'none':
                val = None
            elif val.lower() == 'true':
                val = True
            elif val.lower() == 'false':
                val = False
            else:
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except:
                    pass

            update_data[key] = val

        user = await db.col.find_one({"_id": user_id})
        if not user:
            return await message.reply_text("❌ User not found in database.", quote=True)

        await db.col.update_one({"_id": user_id}, {"$set": update_data})
        await message.reply_text(f"✅ Updated user `{user_id}` with fields:\n```json\n{update_data}\n```")
    except Exception as e:
        await message.reply_text(f"⚠️ Error: `{e}`")
        
                
