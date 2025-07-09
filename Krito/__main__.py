import logging
import asyncio
from datetime import datetime
from pytz import timezone
from aiohttp import web
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from route import web_server
from Krito import pbot, ubot, ADMIN, LOG_CHANNEL

# 🧠 𝐈𝐍𝐓𝐄𝐑𝐀𝐂𝐓𝐈𝐕𝐄 𝐋𝐎𝐆𝐆𝐈𝐍𝐆 𝐒𝐄𝐓𝐔𝐏
logging.basicConfig(
    format='[%(levelname)5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("🛠 𝐁𝐎𝐓-𝐒𝐓𝐀𝐑𝐓𝐔𝐏")


async def start_clients():
    logger.info("🔌 *𝐈𝐍𝐈𝐓*: Starting bot client...")
    await pbot.start()
    logger.info("✅ *𝐁𝐎𝐓*: 𝐎𝐧𝐥𝐢𝐧𝐞")

    if ubot:
        await ubot.start()
        logger.info("✅ *𝐔𝐒𝐄𝐑𝐁𝐎𝐓*: 𝐀𝐜𝐭𝐢𝐯𝐞")

    return pbot, ubot


async def main():
    pbot, ubot = await start_clients()
    me = await pbot.get_me()

    pbot.mention = me.mention
    pbot.username = me.username

    logger.info(f"🚀 *𝐁𝐎𝐓 𝐒𝐓𝐀𝐑𝐓𝐄𝐃*: {me.first_name} 💬")

    if WEBHOOK:
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", 8080).start()
        logger.info("🌐 *𝐖𝐄𝐁𝐇𝐎𝐎𝐊*: Listening on `0.0.0.0:8080`")

    for admin_id in ADMIN:
        try:
            await pbot.send_message(
                admin_id,
                f"**🤖 ʙᴏᴛ `{me.first_name}` ɪꜱ ɴᴏᴡ ᴏɴʟɪɴᴇ!**\n_𝐒𝐭𝐚𝐫𝐭𝐮𝐩 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥._"
            )
        except Exception as e:
            logger.warning(f"⚠️ *𝐀𝐃𝐌𝐈𝐍 𝐍𝐎𝐓𝐈𝐅𝐘 𝐅𝐀𝐈𝐋𝐄𝐃* {admin_id}: {e}")

    if LOG_CHANNEL:
        try:
            curr = datetime.now(timezone("Asia/Kolkata"))
            date = curr.strftime('%d %B, %Y')
            time = curr.strftime('%I:%M:%S %p')
            await pbot.send_message(
                LOG_CHANNEL,
                f"**🔄 ʀᴇꜱᴛᴀʀᴛ ʀᴇᴘᴏʀᴛ**\n\n📅 ᴅᴀᴛᴇ: `{date}`\n⏰ ᴛɪᴍᴇ: `{time}`\n🌍 ᴛɪᴍᴇᴢᴏɴᴇ: `Asia/Kolkata`\n💾 ᴠᴇʀꜱɪᴏɴ: `v{__version__} (Layer {layer})`"
            )
        except Exception as e:
            logger.warning(f"⚠️ *𝐋𝐎𝐆 𝐂𝐇𝐀𝐍𝐍𝐄𝐋 𝐅𝐀𝐈𝐋*: {e}")

    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("🛑 *𝐌𝐀𝐍𝐔𝐀𝐋 𝐒𝐓𝐎𝐏*: Bot halted via KeyboardInterrupt")
