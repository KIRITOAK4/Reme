import logging
import asyncio
from datetime import datetime
from pytz import timezone
from aiohttp import web
from route import web_server
from pyrogram.raw.all import layer
from pyrogram import __version__, idle
from Krito import pbot, ubot, WEBHOOK, ADMIN, LOG_CHANNEL, BOT_UPTIME
from helper.token import schedule_daily_reset

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Start Pyrogram clients
        await pbot.start()
        if ubot is not None:
            await ubot.start()

        me = await pbot.get_me()
        pbot.mention = me.mention
        pbot.username = me.username
        logger.info(f"{me.first_name} Is Started.....✨️")

        # Schedule daily reset task
        asyncio.create_task(schedule_daily_reset())

        # Start web server if WEBHOOK is enabled
        if WEBHOOK:
            app = web.AppRunner(await web_server())
            await app.setup()
            site = web.TCPSite(app, "0.0.0.0", 8080)
            await site.start()
            logger.info("Web Server Started")

        # Notify admins
        for admin_id in ADMIN:
            try:
                await pbot.send_message(
                    admin_id,
                    f"**__{me.first_name} Iꜱ Sᴛᴀʀᴛᴇᴅ.....✨️__**"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

        # Send startup message to log channel
        if LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await pbot.send_message(
                    LOG_CHANNEL,
                    f"**__{me.mention} Iꜱ Rᴇsᴛᴀʀᴛᴇᴅ !!**\n\n"
                    f"📅 Dᴀᴛᴇ: `{date}`\n"
                    f"⏰ Tɪᴍᴇ: `{time}`\n"
                    f"🌐 Tɪᴍᴇᴢᴏɴᴇ: `Asia/Kolkata`\n\n"
                    f"🉐 Vᴇʀsɪᴏɴ: `v{__version__} (Layer {layer})`"
                )
            except Exception as e:
                logger.error(f"Failed to send log channel message: {e}")

        # Keep the application running
        await idle()

    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
    finally:
        # Properly stop clients
        await pbot.stop()
        if ubot is not None:
            await ubot.stop()
        logger.info("Bot Stopped Successfully")

if __name__ == "__main__":
    asyncio.run(main())
