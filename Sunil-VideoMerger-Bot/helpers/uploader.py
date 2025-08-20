"""
Modified uploader module with dual upload capability
Uploads to both Telegram and GoFile.io simultaneously
"""

import asyncio
import time
from configs import Config
from helpers.database.access_db import db
from helpers.display_progress import progress_for_pyrogram, humanbytes
from helpers.gofile_uploader import GoFileUploader
from humanfriendly import format_timespan
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


async def UploadVideo(bot: Client, cb: CallbackQuery, merged_vid_path: str, 
                     width, height, duration, video_thumbnail, file_size):
    """Enhanced upload function with dual upload capability"""
    try:
        # Initialize GoFile uploader
        gofile_uploader = GoFileUploader()

        # Start both uploads simultaneously
        telegram_task = upload_to_telegram(
            bot, cb, merged_vid_path, width, height, duration, 
            video_thumbnail, file_size
        )

        gofile_task = upload_to_gofile(gofile_uploader, merged_vid_path, cb.message)

        # Wait for both uploads to complete
        telegram_result, gofile_result = await asyncio.gather(
            telegram_task, gofile_task, return_exceptions=True
        )

        # Send final message with both links
        await send_final_message(bot, cb, telegram_result, gofile_result, merged_vid_path, 
                                duration, file_size)

    except Exception as err:
        print(f"Failed to upload video!\nError: {err}")
        try:
            await cb.message.edit(f"❌ Upload failed!\n**Error:**\n`{err}`")
        except:
            pass


async def upload_to_telegram(bot: Client, cb: CallbackQuery, merged_vid_path: str, 
                           width, height, duration, video_thumbnail, file_size):
    """Upload video to Telegram"""
    try:
        sent_ = None
        upload_as_doc = await db.get_upload_as_doc(cb.from_user.id)

        if upload_as_doc is False:
            c_time = time.time()
            sent_ = await bot.send_video(
                chat_id=cb.message.chat.id,
                video=merged_vid_path,
                width=width,
                height=height,
                duration=duration,
                thumb=video_thumbnail,
                caption=f"📱 **Telegram Upload Complete**\n\n**File:** `{os.path.basename(merged_vid_path)}`",
                progress=progress_for_pyrogram,
                progress_args=(
                    "📱 Uploading to Telegram ...",
                    cb.message,
                    c_time
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Developer", url="https://t.me/AbirHasan2005")
                ]])
            )
        else:
            c_time = time.time()
            sent_ = await bot.send_document(
                chat_id=cb.message.chat.id,
                document=merged_vid_path,
                caption=f"📱 **Telegram Upload Complete**\n\n**File:** `{os.path.basename(merged_vid_path)}`",
                thumb=video_thumbnail,
                progress=progress_for_pyrogram,
                progress_args=(
                    "📱 Uploading to Telegram ...",
                    cb.message,
                    c_time
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Developer", url="https://t.me/AbirHasan2005")
                ]])
            )

        # Log to admin channel
        if Config.LOG_CHANNEL:
            forward_ = await sent_.forward(chat_id=Config.LOG_CHANNEL)
            await forward_.reply_text(
                text=f"**User:** [{cb.from_user.first_name}](tg://user?id={cb.from_user.id})\n"
                     f"**Username:** `{cb.from_user.username}`\n"
                     f"**UserID:** `{cb.from_user.id}`",
                disable_web_page_preview=True,
                quote=True
            )

        return {
            'success': True,
            'message': sent_,
            'file_link': f"https://t.me/c/{str(cb.message.chat.id)[4:]}/{sent_.message_id}"
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


async def upload_to_gofile(gofile_uploader: GoFileUploader, file_path: str, message):
    """Upload video to GoFile.io"""
    try:
        # Update status
        await message.edit("🌐 Starting GoFile.io upload...")

        result = await gofile_uploader.upload_file(file_path, message)

        if result:
            return {
                'success': True,
                'download_page': result['download_page'],
                'file_id': result['file_id']
            }
        else:
            return {'success': False, 'error': 'GoFile upload failed'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


async def send_final_message(bot: Client, cb: CallbackQuery, telegram_result, 
                           gofile_result, file_path: str, duration, file_size):
    """Send final message with both upload results"""
    try:
        filename = os.path.basename(file_path)
        duration_str = format_timespan(duration)
        size_str = humanbytes(file_size)

        # Build message content
        message_parts = [
            "🎉 **Video Merge & Upload Complete!**",
            "",
            f"📁 **File:** `{filename}`",
            f"⏱ **Duration:** `{duration_str}`", 
            f"💾 **Size:** `{size_str}`",
            "",
            "📥 **Download Links:**"
        ]

        buttons = []

        # Add Telegram link if successful
        if isinstance(telegram_result, dict) and telegram_result.get('success'):
            message_parts.append("✅ **Telegram:** Upload Successful")
            if telegram_result.get('file_link'):
                buttons.append([InlineKeyboardButton("📱 Telegram Download", 
                                                   url=telegram_result['file_link'])])
        else:
            error = getattr(telegram_result, 'args', ['Unknown error'])[0] if isinstance(telegram_result, Exception) else telegram_result.get('error', 'Unknown error')
            message_parts.append(f"❌ **Telegram:** {error}")

        # Add GoFile link if successful
        if isinstance(gofile_result, dict) and gofile_result.get('success'):
            message_parts.append("✅ **GoFile.io:** Upload Successful")
            buttons.append([InlineKeyboardButton("🌐 GoFile Download", 
                                                url=gofile_result['download_page'])])
        else:
            error = getattr(gofile_result, 'args', ['Unknown error'])[0] if isinstance(gofile_result, Exception) else gofile_result.get('error', 'Unknown error')
            message_parts.append(f"❌ **GoFile.io:** {error}")

        # Add developer button
        buttons.append([InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/AbirHasan2005")])

        final_message = "\n".join(message_parts)

        # Send final message
        await bot.send_message(
            chat_id=cb.message.chat.id,
            text=final_message,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
        )

        # Clean up the processing message
        try:
            await cb.message.delete()
        except:
            pass

    except Exception as e:
        print(f"Error sending final message: {e}")
        try:
            await cb.message.edit("✅ Upload completed! Check above messages for download links.")
        except:
            pass
