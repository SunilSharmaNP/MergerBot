

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def make_buttons(videos_list: list):
    buttons = []
    for video in videos_list:
        video_name = str(video).split("/")[-1]
        buttons.append([InlineKeyboardButton(video_name, callback_data=f"del_{video}")])
    return InlineKeyboardMarkup(buttons)
