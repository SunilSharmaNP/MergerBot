

from configs import Config
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant


async def ForceSub(bot, cmd):
    try:
        user = await bot.get_chat_member(chat_id=Config.UPDATES_CHANNEL, user_id=cmd.from_user.id)
        if user.status == "kicked":
            await bot.send_message(
                chat_id=cmd.from_user.id,
                text="You Are Banned From Updates Channel !",
                disable_web_page_preview=True
            )
            return 400
    except UserNotParticipant:
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="**You Have To Join My Updates Channel To Use Me**\n\nJoin Channel and Try Again!",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Join Channel", url=f"https://t.me/{Config.UPDATES_CHANNEL[1:]}")
                    ]
                ]
            ),
            disable_web_page_preview=True
        )
        return 400
    except Exception as e:
        print(f"ForceSub Error: {e}")
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="Something went wrong, please contact bot admin.",
            disable_web_page_preview=True
        )
        return 200
    return 200
