# Enhanced Configuration for VideoMerge-Bot
# (c) @AbirHasan2005

import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config(object):
    # --- REQUIRED VARIABLES ---
    # These must be set in your environment or .env file
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    MONGODB_URI = os.environ.get("MONGODB_URI")
    BOT_OWNER = os.environ.get("BOT_OWNER")

    # --- OPTIONAL VARIABLES WITH DEFAULTS ---
    SESSION_NAME = os.environ.get("SESSION_NAME", "VideoMerge-Bot-Enhanced")
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL")  # Can be None
    LOG_CHANNEL = os.environ.get("LOG_CHANNEL")          # Can be None
    DOWN_PATH = os.environ.get("DOWN_PATH", "./downloads")
    
    # Improved boolean handling
    BROADCAST_AS_COPY = os.environ.get("BROADCAST_AS_COPY", "False").lower() in ("true", "1", "yes")

    # Numeric configurations with type casting and defaults
    TIME_GAP = int(os.environ.get("TIME_GAP", 5))
    MAX_VIDEOS = int(os.environ.get("MAX_VIDEOS", 5))
    MAX_DOWNLOAD_SIZE = int(os.environ.get("MAX_DOWNLOAD_SIZE", 2147483648))  # 2GB
    DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", 300))  # 5 minutes
    CONCURRENT_DOWNLOADS = int(os.environ.get("CONCURRENT_DOWNLOADS", 3))
    MAX_RETRY_ATTEMPTS = int(os.environ.get("MAX_RETRY_ATTEMPTS", 3))
    CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 131072))  # 128KB
    
    # External service credentials (optional)
    STREAMTAPE_API_USERNAME = os.environ.get("STREAMTAPE_API_USERNAME")
    STREAMTAPE_API_PASS = os.environ.get("STREAMTAPE_API_PASS")
    GOFILE_API_TOKEN = os.environ.get("GOFILE_API_TOKEN")

    # --- STATIC TEXT AND MESSAGES ---
    START_TEXT = """
🎬 **Enhanced VideoMerge Bot**

Hi! I can merge multiple videos and provide download links from both Telegram and GoFile.io!

**New Features:**
✅ Direct download link support
✅ Dual upload (Telegram + GoFile.io)
✅ Enhanced progress tracking
✅ Docker deployment ready

Send video files or direct download links to get started!

Made with ❤️ by @AbirHasan2005
"""
    
    HELP_TEXT = """
🤖 **Enhanced VideoMerge Bot Help**

**Features:**
• Merge multiple video files
• Support for direct download links
• Dual upload (Telegram + GoFile.io)
• Custom thumbnail support

**How to Use:**
1️⃣ Send video files OR direct download links
2️⃣ Add up to {max_videos} videos to queue
3️⃣ Use /merge to combine them

**Commands:**
• /start - Start the bot
• /help - Show this help
• /merge - Merge queued videos
• /settings - Configure bot settings
• /clear - Clear video queue

Made with ❤️ by @AbirHasan2005
"""

    PROGRESS = """
Percentage : {0}%
Done: {1}
Total: {2}
Speed: {3}/s
ETA: {4}
"""

    # --- STATIC LISTS AND DICTIONARIES ---
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mkv', '.webm', '.avi', 'mov', '.m4v']
    USER_AGENT = "Mozilla/5.0 (VideoMerge-Bot-Enhanced/1.0)"
    
    ERROR_MESSAGES = {
        'invalid_url': "❌ Invalid URL or unsupported video format!",
        'file_too_large': "❌ File size exceeds limit of {max_size}!",
        'download_timeout': "❌ Download timed out after {timeout} seconds!",
        'network_error': "❌ Network error occurred. Please try again!",
        'server_error': "❌ Server returned error code {code}!",
        'queue_full': "❌ Maximum {max_videos} videos allowed in queue!",
        'not_enough_videos': "❌ At least 2 videos are required to merge!",
        'merge_failed': "❌ Video merge failed. Please try again!",
        'upload_failed': "❌ Upload to {platform} failed: {error}",
        'spam_protection': "⏳ Please wait {seconds} seconds before next request."
    }

# --- VALIDATION BLOCK ---
# This block checks for required environment variables at startup.
def validate_config(config_class):
    required_vars = ["API_ID", "API_HASH", "BOT_TOKEN", "MONGODB_URI", "BOT_OWNER"]
    missing_vars = [var for var in required_vars if not getattr(config_class, var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Try to cast numeric variables to ensure they are valid integers
    try:
        config_class.API_ID = int(config_class.API_ID)
        config_class.BOT_OWNER = int(config_class.BOT_OWNER)
    except (ValueError, TypeError) as e:
        raise ValueError(f"API_ID and BOT_OWNER must be valid integers. Error: {e}")

# Run validation when the module is imported
validate_config(Config)
