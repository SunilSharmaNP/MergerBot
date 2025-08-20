"""
Enhanced downloader module with direct URL download capability
Supports multiple video formats and provides progress tracking
"""

import aiohttp
import asyncio
import os
import time
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple
import tqdm.asyncio
from configs import Config
from helpers.display_progress import humanbytes, TimeFormatter


class DirectDownloader:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.concurrent_downloads = Config.CONCURRENT_DOWNLOADS

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=Config.DOWNLOAD_TIMEOUT)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': 'Mozilla/5.0 (VideoMerge-Bot)'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def download_from_url(self, url: str, user_id: int, message) -> Optional[str]:
        """
        Download video from direct URL
        Returns: Downloaded file path or None if failed
        """
        try:
            # Validate URL and get filename
            filename = self._get_filename_from_url(url)
            if not filename:
                await message.edit("❌ Invalid URL or unsupported file type!")
                return None

            download_path = f"{Config.DOWN_PATH}/{user_id}"
            os.makedirs(download_path, exist_ok=True)

            file_path = os.path.join(download_path, filename)

            # Check if file already exists
            if os.path.exists(file_path):
                file_path = self._get_unique_filename(file_path)

            # Start download with progress tracking
            success = await self._download_with_progress(url, file_path, message)

            if success:
                return file_path
            else:
                return None

        except Exception as e:
            await message.edit(f"❌ Download failed: {str(e)}")
            return None

    def _get_filename_from_url(self, url: str) -> Optional[str]:
        """Extract filename from URL"""
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path))

        if not filename or '.' not in filename:
            filename = "video.mp4"  # Default filename

        # Check if it's a supported video format
        supported_formats = ['.mp4', '.mkv', '.webm', '.avi', '.mov', '.m4v']
        if not any(filename.lower().endswith(fmt) for fmt in supported_formats):
            return None

        return filename

    def _get_unique_filename(self, file_path: str) -> str:
        """Generate unique filename if file exists"""
        base, ext = os.path.splitext(file_path)
        counter = 1
        while os.path.exists(file_path):
            file_path = f"{base}_{counter}{ext}"
            counter += 1
        return file_path

    async def _download_with_progress(self, url: str, file_path: str, message) -> bool:
        """Download file with progress tracking"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    await message.edit(f"❌ Server returned status {response.status}")
                    return False

                total_size = int(response.headers.get('Content-Length', 0))

                if total_size > Config.MAX_DOWNLOAD_SIZE:
                    await message.edit(
                        f"❌ File too large! "
                        f"Max size: {humanbytes(Config.MAX_DOWNLOAD_SIZE)}, "
                        f"File size: {humanbytes(total_size)}"
                    )
                    return False

                downloaded = 0
                start_time = time.time()
                last_update = 0

                with open(file_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        file.write(chunk)
                        downloaded += len(chunk)

                        # Update progress every 2 seconds
                        current_time = time.time()
                        if current_time - last_update > 2:
                            await self._update_progress(
                                message, downloaded, total_size, 
                                start_time, current_time
                            )
                            last_update = current_time

                # Final progress update
                await message.edit("✅ Download completed! Processing...")
                return True

        except asyncio.TimeoutError:
            await message.edit("❌ Download timed out!")
            return False
        except Exception as e:
            await message.edit(f"❌ Download error: {str(e)}")
            return False

    async def _update_progress(self, message, downloaded: int, total_size: int, 
                             start_time: float, current_time: float):
        """Update download progress message"""
        if total_size > 0:
            percentage = (downloaded / total_size) * 100
        else:
            percentage = 0

        elapsed_time = current_time - start_time
        if elapsed_time > 0:
            speed = downloaded / elapsed_time
            if total_size > 0:
                eta = (total_size - downloaded) / speed
                eta_str = TimeFormatter(int(eta * 1000))
            else:
                eta_str = "Unknown"
        else:
            speed = 0
            eta_str = "Unknown"

        progress_text = Config.DOWNLOAD_PROGRESS.format(
            round(percentage, 1),
            humanbytes(downloaded),
            humanbytes(total_size) if total_size > 0 else "Unknown",
            humanbytes(speed),
            eta_str
        )

        try:
            await message.edit(progress_text)
        except:
            pass  # Ignore edit errors
