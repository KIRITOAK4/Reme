from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant
from helper.database import db
from Krito import pbot, FORCE_SUB

async def not_subscribed(_, client, message):
    await db.add_user(client, message)
    if not FORCE_SUB:
        return False
    try:
        for force_sub in FORCE_SUB:
            user = await client.get_chat_member(force_sub, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                break
        else:
            return False
    except UserNotParticipant:
        pass
    return True

@pbot.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    buttons = []
    text = (
        "**Sᴏʀʀʏ Dᴜᴅᴇ, Yᴏᴜ'ʀᴇ Nᴏᴛ Jᴏɪɴᴇᴅ ᴛᴏ Mʏ Cʜᴀɴɴᴇʟ 😐.**\n"
        "**Pʟᴇᴀꜱᴇ Jᴏɪɴ Oᴜʀ Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟ ᴛᴏ Cᴏɴᴛɪɴᴜᴇ Uꜱɪɴɢ ᴍᴇ.**"
    )

    try:
        for order, force_sub in enumerate(FORCE_SUB, start=1):
            invite_link = await client.export_chat_invite_link(force_sub)
            button = [InlineKeyboardButton(text=f"📢 Join Update {order} 📢", url=invite_link)]
            buttons.extend(button)
    except Exception as e:
        return await message.reply_text(text=f"An error occurred: {e}")

    button_pairs = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    reply_markup = InlineKeyboardMarkup(button_pairs)

    try:
        for force_sub in FORCE_SUB:
            user = await client.get_chat_member(force_sub, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                return await client.send_message(
                    message.from_user.id,
                    text="Sᴏʀʀʏ, Yᴏᴜ'ʀᴇ Bᴀɴɴᴇᴅ Fʀᴏᴍ Uꜱɪɴɢ Mᴇ."
                )
    except UserNotParticipant:
        return await message.reply_text(text=text, reply_markup=reply_markup)
        
