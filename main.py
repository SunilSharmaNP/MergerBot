# Enhanced VideoMerge-Bot with Direct Download & GoFile Integration


import asyncio
import os
import time
import re
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from configs import Config
from helpers.database.add_user import AddUserToDatabase
from helpers.check_gap import CheckTimeGap
from helpers.clean import CleanupManager
from helpers.downloader import DirectDownloader
from helpers.merger import VideoMerger, get_video_duration, get_video_resolution
from helpers.forcesub import ForceSub
from helpers.uploader import UploadVideo
from helpers.settings import OpenSettings
from helpers.broadcast import broadcast_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize bot
NubBot = Client(
    session_name=Config.SESSION_NAME,
    api_id=int(Config.API_ID),
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Global dictionaries for queue management
QueueDB = {}
ReplyDB = {}
cleanup_manager = CleanupManager()

def is_direct_video_url(text: str) -> bool:
    """Check if text contains a direct video URL"""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    if url_pattern.match(text):
        video_indicators = Config.SUPPORTED_VIDEO_FORMATS + ['.zip', '.rar', 'video', 'watch', 'dl', 'download']
        return any(indicator.lower() in text.lower() for indicator in video_indicators)
    return False

@NubBot.on_message(filters.command(["start", "ping"]) & filters.private)
async def start_handler(bot, message):
    try:
        await AddUserToDatabase(bot, message)
        
        if Config.UPDATES_CHANNEL:
            if not await ForceSub(bot, message):
                return
        
        await message.reply_text(
            text=Config.START_TEXT,
            quote=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Help", callback_data="help"),
                 InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
                [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/AbirHasan2005")]
            ])
        )
    except Exception as e:
        logger.error(f"Start handler error: {e}")

@NubBot.on_message(filters.command(["help"]) & filters.private)
async def help_handler(bot, message):
    await message.reply_text(Config.HELP_TEXT.format(max_videos=Config.MAX_VIDEOS), quote=True)

@NubBot.on_message(filters.command(["settings"]) & filters.private)
async def settings_handler(bot, message):
    await OpenSettings(message)

@NubBot.on_message(filters.command(["merge"]) & filters.private)
async def merge_handler(bot, message):
    user_id = message.from_user.id
    
    try:
        if user_id not in QueueDB or len(QueueDB.get(user_id, [])) < 2:
            await message.reply_text(Config.ERROR_MESSAGES['not_enough_videos'])
            return
        
        is_spam, wait_time = await CheckTimeGap(user_id)
        if is_spam:
            await message.reply_text(Config.ERROR_MESSAGES['spam_protection'].format(seconds=wait_time))
            return
        
        merge_message = await message.reply_text("🚀 **Initializing merge process...**")
        
        merger = VideoMerger(user_id)
        merged_video = await merger.merge_videos(QueueDB[user_id], merge_message)
        
        if merged_video:
            await merge_message.edit("✅ **Merge completed! Preparing for upload...**")
            
            duration = await get_video_duration(merged_video)
            width, height = await get_video_resolution(merged_video)
            file_size = os.path.getsize(merged_video)
            thumbnail_path = (await merger.generate_thumbnails(merged_video, count=1))[0]
            
            await UploadVideo(bot, message, merged_video, width, height, duration, thumbnail_path, file_size)
            
            if user_id in QueueDB: del QueueDB[user_id]
            if user_id in ReplyDB: del ReplyDB[user_id]
            await cleanup_manager.clean_user_directory(user_id)
        else:
            await merge_message.edit(Config.ERROR_MESSAGES['merge_failed'])

    except Exception as e:
        logger.error(f"Merge handler error: {e}")
        await message.reply_text(f"❌ **Error:** `{str(e)}`")

@NubBot.on_message(filters.command(["clear"]) & filters.private)
async def clear_handler(bot, message):
    user_id = message.from_user.id
    
    if user_id in QueueDB: del QueueDB[user_id]
    if user_id in ReplyDB: del ReplyDB[user_id]
    
    await cleanup_manager.clean_user_directory(user_id)
    await message.reply_text("✅ **Queue cleared successfully!**")

@NubBot.on_message((filters.video | filters.document) & filters.private)
async def media_handler(bot, message):
    user_id = message.from_user.id
    
    try:
        await AddUserToDatabase(bot, message)
        
        if Config.UPDATES_CHANNEL:
            if not await ForceSub(bot, message):
                return
        
        is_spam, wait_time = await CheckTime```(user_id)
        if is_spam:
            await message.reply_text(Config.ERROR_MESSAGES['spam_protection'].format(seconds=wait_time))
            return
        
        if len(QueueDB.get(user_id, [])) >= Config.MAX_VIDEOS:
            await message.reply_text(Config.ERROR_MESSAGES['queue_full'].format(max_videos=Config.MAX_VIDEOS))
            return

        media = message.video or message.document
        if not media.mime_type or "video" not``` media.mime_type:
            await message.reply_text("❌ Please send only video files.")
            return

        download_msg = await message.reply_text("📥 **Downloading video...**", quote=True)
        
        file_path = os.path.join(Config.DOWN_PATH, str(user_id), f"{time.time()}_{media.file_name or 'video.mp4'}")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        await bot.download_media(message, file_name=file_path)
        
        QueueDB.setdefault(user_id, []).append(file_path)
        ReplyDB.setdefault(user_id, []).append(download_msg.message_id)
        
        await download_msg.edit(
            f"✅ **Video added!**\n\n📁 **File:** `{os.path.basename(file_path)}`\n🎬 **Queue:** {len(QueueDB[user_id])}/{Config.MAX_VIDEOS}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔀 Merge Now", callback_data="merge_now")],
                [InlineKeyboardButton("🗑 Clear Queue", callback_data="clear_queue")]
            ])
        )

    except Exception as e:
        logger.error(f"Media handler error: {e}")
        await message.reply_text(f"❌ **Error:** `{str(e)}`")


@NubBot.on_message(filters.text & filters.private & ~filters.command())
async def url_handler(bot, message):
    user_id = message.from_user.id

    if is_direct_video_url(message.text):
        try:
            await AddUserToDatabase(bot, message)

            if Config.UPDATES_CHANNEL:
                if not await ForceSub(bot, message): return
            
            is_spam, wait_time = await CheckTimeGap(user_id)
            if is_spam:
                await message.reply_text(Config.ERROR_MESSAGES['spam_protection'].format(seconds=wait_time))
                return

            if len(QueueDB.get(user_id, [])) >= Config.MAX_VIDEOS:
                await message.reply```xt(Config.ERROR_MESSAGES['queue_full'].format(max_videos=Config.MAX_VIDEOS))
                return

            download_msg = await message.reply_text("🔄 **Processing URL...**", quote=True)
            
            async with DirectDownloader() as downloader:
                downloaded_file = await downloader.download_from_url(message.text, user_id, download_msg)
            
            if downloaded_file:
                QueueDB.setdefault(user_id, []).append(downloaded_file)
                ReplyDB.setdefault(user_id, []).append(download_msg.message_id)
                
                await download_msg.edit(
                    f"✅ **Download complete!**\n\n📁 **File:** `{os.path.basename(downloaded_file)}`\n🎬 **Queue:** {len(QueueDB[user_id])}/{Config.MAX_VIDEOS}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔀 Merge Now", callback_data="merge_now")],
                        [InlineKeyboardButton("🗑 Clear Queue", callback_data="clear_queue")]
                    ])
                )
            else:
                await download_msg.edit("❌ **Download failed!** Please check the URL and try again.")
        except Exception as e:
            logger.error(f"URL handler error: {e}")
            await message.reply_text(f"❌ **Error:** `{str(e)}`")
    else:
        await message.reply_text("Please send video files, direct video links, or use /help.")

@NubBot.on_callback_query()
async def callback_handler(bot, cb: CallbackQuery):
    user_id = cb.from_user.id
    
    if cb.data == "help":
        await cb.message.edit_text(Config.HELP_TEXT.format(max_videos=Config.MAX_VIDEOS), reply_markup=cb.message.reply_markup)
    elif cb.data == "settings":
        await OpenSettings(cb.message)
    elif cb.data == "merge_now":
        await cb.message.delete()
        await merge_handler(bot, cb.message)
    elif cb.data == "clear_queue":
        await clear_handler(bot, cb.message)
    elif cb.data.startswith("trigger") or cb.data.startswith("show"):
        # Handle settings callbacks
        await OpenSettings(cb)

    await cb.answer()

@NubBot.on_message(filters.command(["broadcast"]) & filters.user(Config.BOT_OWNER))
async def broadcast_command(bot, message):
    if message.reply_to_message:
        await broadcast_handler(message)
    else:
        await message.reply_text("Reply to a message to broadcast it.")

async def start_bot():
    logger.info("Starting Enhanced VideoMerge Bot...")
    await NubBot.start()
    logger.info("Bot started successfully!")
    # Start scheduled cleanup
    asyncio.create_task(cleanup_manager.start_cleanup_scheduler())
    await asyncio.Event().wait() # Keep running

if __name__ == "__main__":
    asyncio.run(start_bot())

