from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
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
        "**Pʟᴇᴀꜱᴇ Jᴏɪɴ Oᴜʀ Uᴘᴅᴀᴛᴇ Cʜᴀɴɴᴇʟꜱ ᴛᴏ Cᴏɴᴛɪɴᴜᴇ Uꜱɪɴɢ ᴍᴇ.**"
    )

    try:
        for order, force_sub in enumerate(FORCE_SUB, start=1):
            invite_link = await client.export_chat_invite_link(force_sub)
            buttons.append(InlineKeyboardButton(f"📢 Join Update {order} 📢", url=invite_link))
    except Exception as e:
        return await message.reply_text(text=f"An error occurred: {e}")

    button_rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]

    for force_sub in FORCE_SUB:
        try:
            user = await client.get_chat_member(force_sub, message.from_user.id)
            if user.status == enums.ChatMemberStatus.BANNED:
                return await message.reply_text(
                    "🚫 You are **banned** from one of the required channels.\n"
                    "If you think this is a mistake, please appeal below.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("📝 Appeal Here", url="https://t.me/kirigayaakash")]]
                    )
                )
        except UserNotParticipant:
            pass
    button_rows.append([InlineKeyboardButton("🔄 Refresh", callback_data="refreshForceSub")])
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(button_rows))

@pbot.on_callback_query(filters.regex("refreshForceSub"))
async def refresh_force_sub(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    all_joined = True

    # Check if user has joined all channels
    for force_sub in FORCE_SUB:
        try:
            member = await client.get_chat_member(force_sub, user_id)
            if member.status not in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
                all_joined = False
                break
        except UserNotParticipant:
            all_joined = False
            break

    if all_joined:
        await query.message.edit_text("✅ Perfect! Now use me.")
        await query.answer("You're all set!", show_alert=False)
    else:
        await forces_sub(client, query.message)
        await query.answer("🔄 Still missing some channels. Try again after joining.", show_alert=False)

