from helper.database import db
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import os, sys, time, asyncio, logging, datetime
from Krito import pbot, ADMIN, LOG_CHANNEL, BOT_UPTIME
import subprocess
import importlib
from datetime import datetime
from Krito import Text2  # Import Text2 from Krito/__init__.py

@pbot.on_message(filters.command("update_log") & filters.user(ADMIN))
async def send_update_log(client, message):
    try:
        # Run Git command to get latest commit logs (last 5 commits)
        result = subprocess.run(
            ["git", "log", "--pretty=format:%h - %s (%cr)", "-5"],
            capture_output=True,
            text=True
        )

        commit_log = result.stdout.strip()
        if not commit_log:
            await message.reply_text("🚫 No recent updates found in the repository.")
            return

        # Fetch last updated date (latest commit timestamp)
        date_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%cd", "--date=iso"],
            capture_output=True,
            text=True
        )

        last_update = date_result.stdout.strip()
        if last_update:
            formatted_date = datetime.strptime(last_update, "%Y-%m-%d %H:%M:%S %z").strftime("%d %B %Y, %I:%M %p %Z")
            last_update_text = f"\n🕒 **Last Updated On:** {formatted_date}"
        else:
            last_update_text = "\n🕒 **Last Updated On:** Unknown"

        # Format the final update message
        update_message = f"🆕 **Latest Updates in Repo:**\n\n{commit_log}{last_update_text}"

        # Update Text2 dynamically
        with open("Krito/__init__.py", "r", encoding="utf-8") as file:
            lines = file.readlines()

        with open("Krito/__init__.py", "w", encoding="utf-8") as file:
            for line in lines:
                if line.startswith("Text2 ="):
                    file.write(f'Text2 = """{update_message}"""\n')
                else:
                    file.write(line)

        # Reload module to apply changes
        importlib.reload(Text2)

        # Send the update log
        await message.reply_text(update_message)

    except Exception as e:
        await message.reply_text(f"❌ Error fetching update logs: {e}")
        

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@pbot.on_message(filters.command(["stats", "status"]))
async def get_stats(bot, message):
    if message.from_user.id not in ADMIN:
        await message.reply_text("You are not authorized to use this command.", reply_to_message_id=message.id)
        return

    total_users = await db.total_users_count()
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - BOT_UPTIME))    
    start_t = time.time()
    st = await message.reply('**Aᴄᴄᴇssɪɴɢ Tʜᴇ Dᴇᴛᴀɪʟs.....**')    
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await st.edit(text=f"**--Bᴏᴛ Sᴛᴀᴛᴜꜱ--** \n\n**⌚️ Bᴏᴛ Uᴩᴛɪᴍᴇ:** {uptime} \n**🐌 Cᴜʀʀᴇɴᴛ Pɪɴɢ:** `{time_taken_s:.3f} ᴍꜱ` \n**👭 Tᴏᴛᴀʟ Uꜱᴇʀꜱ:** `{total_users}`")

@pbot.on_message(filters.private & filters.command("restart"))
async def restart_bot(b, m):
    if m.from_user.id not in ADMIN:
        await m.reply_text("You are not authorized to use this command.", reply_to_message_id=m.id)
        return
    await m.reply_text("🔄__Restarting...__")
    os.execl(sys.executable, sys.executable, *sys.argv)

@pbot.on_message(filters.command("reset_time") & filters.user(ADMIN))
async def reset_user_space(client, message):
    try:
        command_parts = message.text.split()
        
        if len(command_parts) == 2 and command_parts[1].lower() == "all":
            all_users = await db.get_all_users()
            for user in all_users:
                user_id = user["_id"]
                await db.set_space_used(user_id, 0)
                try:
                    await pbot.send_message(user_id, "Your used space has been reset to 0. Enjoy!")
                except Exception as e:
                    await message.reply_text(f"❌ Failed to notify user {user_id}. Error: {e}")
            await message.reply_text("✅ Space usage for all users has been reset to 0.")
        
        elif len(command_parts) == 2:
            user_id = int(command_parts[1])
            current_space_used = await db.get_space_used(user_id)
            
            if current_space_used is None:
                await message.reply_text(f"⚠️ No data found for user {user_id}.")
                return
            
            await db.set_space_used(user_id, 0)
            await message.reply_text(f"✅ User {user_id}'s space usage has been reset to 0.\n(Previous usage: {current_space_used} bytes)")
            try:
                await pbot.send_message(user_id, "Your used space has been reset to 0. Enjoy!")
            except Exception as e:
                await message.reply_text(f"❌ Failed to notify user {user_id}. Error: {e}")        
        else:
            await message.reply_text("⚠️ Invalid format! Use: `/reset_time <user_id>` or `/reset_time all`")    
    except ValueError:
        await message.reply_text("⚠️ Invalid user ID format. Please provide a valid user ID.")
    except Exception as e:
        await message.reply_text(f"❌ An error occurred while resetting space usage: {e}")

@pbot.on_message(filters.command("update_metadata") & filters.user(ADMIN))
async def update_metadata_for_old_users_command(client, message):
    try:
        await db.update_metadata_for_old_users()
        await message.reply_text("Metadata for old users has been updated successfully.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@pbot.on_message(filters.reply & filters.command("broadcast") & filters.user(ADMIN))
async def broadcast_handler(bot: Client, m: Message):
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
