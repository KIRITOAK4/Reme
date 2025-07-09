import logging
from datetime import datetime
from pytz import timezone
from pyrogram import __version__
from pyrogram.raw.all import layer
from Krito import pbot, ubot, ADMIN, LOG_CHANNEL

# 🧠 𝐈𝐍𝐓𝐄𝐑𝐀𝐂𝐓𝐈𝐕𝐄 𝐋𝐎𝐆𝐆𝐈𝐍𝐆 𝐒𝐄𝐓𝐔𝐏
logging.basicConfig(
    format='[%(levelname)5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("🛠 𝐁𝐎𝐓-𝐒𝐓𝐀𝐑𝐓𝐔𝐏")

# Start-up logic
async def start_bot():
    logger.info("🔌 Starting bot client...")
    await pbot.start()
    logger.info("✅ BOT is online")

    if ubot:
        await ubot.start()
        logger.info("✅ USERBOT is active")

    me = await pbot.get_me()
    pbot.mention = me.mention
    pbot.username = me.username

    logger.info(f"🚀 BOT STARTED: {me.first_name}")

    for admin_id in ADMIN:
        try:
            await pbot.send_message(
                admin_id,
                f"**🤖 BOT `{me.first_name}` is now online!**\n_Startup successful._"
            )
        except Exception as e:
            logger.warning(f"⚠️ ADMIN NOTIFY FAIL {admin_id}: {e}")

    if LOG_CHANNEL:
        try:
            curr = datetime.now(timezone("Asia/Kolkata"))
            date = curr.strftime('%d %B, %Y')
            time = curr.strftime('%I:%M:%S %p')
            await pbot.send_message(
                LOG_CHANNEL,
                f"**🔄 Restart Report**\n\n📅 Date: `{date}`\n⏰ Time: `{time}`\n🌍 Timezone: `Asia/Kolkata`\n💾 Version: `v{__version__} (Layer {layer})`"
            )
        except Exception as e:
            logger.warning(f"⚠️ LOG CHANNEL FAIL: {e}")



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())   # runs the async function main()
    loop.run_forever()                # keeps the bot alive
