"""
Enhanced cleanup module with advanced file management
Provides comprehensive cleanup of temporary files and directories
"""

import os
import shutil
import asyncio
import time
from typing import List, Optional
from configs import Config
import logging

logger = logging.getLogger(__name__)

class CleanupManager:
    def __init__(self):
        self.base_path = Config.DOWN_PATH

    async def clean_user_directory(self, user_id: int, keep_recent: bool = False) -> bool:
        """Clean up user's download directory"""
        try:
            user_dir = f"{self.base_path}/{user_id}"

            if not os.path.exists(user_dir):
                logger.debug(f"User directory doesn't exist: {user_dir}")
                return True

            if keep_recent:
                # Keep files newer than 1 hour
                cutoff_time = time.time() - 3600
                await self._clean_old_files(user_dir, cutoff_time)
            else:
                # Remove entire directory
                shutil.rmtree(user_dir, ignore_errors=True)
                logger.info(f"Cleaned user directory: {user_dir}")

            return True

        except Exception as e:
            logger.error(f"Error cleaning user {user_id} directory: {e}")
            return False

    async def _clean_old_files(self, directory: str, cutoff_time: float):
        """Remove files older than cutoff time"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            logger.debug(f"Removed old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to remove {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning old files: {e}")

    async def cleanup_temp_files(self, patterns: List[str] = None) -> int:
        """Clean up temporary files matching patterns"""
        if patterns is None:
            patterns = ['*.tmp', '*.temp', 'input.txt', 'temp_*', '*.part']

        cleaned_count = 0

        try:
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    if any(self._matches_pattern(file, pattern) for pattern in patterns):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.debug(f"Removed temp file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to remove temp file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error during temp cleanup: {e}")

        logger.info(f"Cleaned {cleaned_count} temporary files")
        return cleaned_count

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern (simple wildcard support)"""
        if '*' not in pattern:
            return filename == pattern

        import fnmatch
        return fnmatch.fnmatch(filename, pattern)

    async def get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        pass
        except Exception as e:
            logger.error(f"Error calculating directory size: {e}")

        return total_size

    async def cleanup_large_files(self, max_size_mb: int = 100) -> List[str]:
        """Remove files larger than specified size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        removed_files = []

        try:
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getsize(file_path) > max_size_bytes:
                            os.remove(file_path)
                            removed_files.append(file_path)
                            logger.info(f"Removed large file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Error removing large file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error during large file cleanup: {e}")

        return removed_files

# Global cleanup manager instance
cleanup_manager = CleanupManager()

# Legacy function for backward compatibility
async def clean_downloads(user_id: int) -> bool:
    """Clean user downloads directory - legacy function"""
    return await cleanup_manager.clean_user_directory(user_id)

# Additional utility functions
async def scheduled_cleanup():
    """Perform scheduled cleanup of old files"""
    try:
        logger.info("Starting scheduled cleanup...")

        # Clean temp files
        temp_count = await cleanup_manager.cleanup_temp_files()

        # Clean old user directories (older than 24 hours)
        cutoff_time = time.time() - (24 * 3600)  # 24 hours

        if os.path.exists(Config.DOWN_PATH):
            for user_dir in os.listdir(Config.DOWN_PATH):
                user_path = os.path.join(Config.DOWN_PATH, user_dir)
                if os.path.isdir(user_path):
                    if os.path.getmtime(user_path) < cutoff_time:
                        try:
                            shutil.rmtree(user_path)
                            logger.info(f"Cleaned old user directory: {user_dir}")
                        except Exception as e:
                            logger.warning(f"Failed to clean {user_dir}: {e}")

        logger.info(f"Scheduled cleanup completed. Cleaned {temp_count} temp files.")

    except Exception as e:
        logger.error(f"Scheduled cleanup error: {e}")

async def get_storage_stats() -> dict:
    """Get storage usage statistics"""
    try:
        if not os.path.exists(Config.DOWN_PATH):
            return {'total_size': 0, 'file_count': 0, 'user_dirs': 0}

        total_size = await cleanup_manager.get_directory_size(Config.DOWN_PATH)

        file_count = 0
        user_dirs = 0

        for root, dirs, files in os.walk(Config.DOWN_PATH):
            file_count += len(files)
            if root != Config.DOWN_PATH:  # Count subdirectories as user dirs
                user_dirs += len(dirs)

        return {
            'total_size': total_size,
            'file_count': file_count,
            'user_dirs': user_dirs,
            'total_size_mb': total_size / (1024 * 1024)
        }

    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        return {'total_size': 0, 'file_count': 0, 'user_dirs': 0}

# Auto-cleanup scheduler
async def start_cleanup_scheduler():
    """Start automatic cleanup scheduler"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await scheduled_cleanup()
        except Exception as e:
            logger.error(f"Cleanup scheduler error: {e}")
            await asyncio.sleep(3600)  # Wait before retrying
