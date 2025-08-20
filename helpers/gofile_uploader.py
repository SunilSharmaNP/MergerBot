"""
GoFile.io integration module for parallel uploads
Provides seamless file upload to GoFile.io with error handling
"""

import aiohttp
import asyncio
import os
from typing import Optional, Dict, Any
from configs import Config


class GoFileUploader:
    def __init__(self):
        self.upload_endpoint = Config.GOFILE_UPLOAD_ENDPOINT
        self.api_token = Config.GOFILE_API_TOKEN

    async def upload_file(self, file_path: str, message=None) -> Optional[Dict[str, Any]]:
        """
        Upload file to GoFile.io
        Returns: Upload response with download link or None if failed
        """
        try:
            if not os.path.exists(file_path):
                if message:
                    await message.edit("❌ File not found for GoFile upload!")
                return None

            # Get file size for progress tracking
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)

            if message:
                await message.edit(f"🌐 Uploading to GoFile.io: {filename}")

            # Create form data for upload
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as file:
                    # Prepare form data
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', file, filename=filename)

                    # Add token if available (for account uploads)
                    if self.api_token:
                        form_data.add_field('token', self.api_token)

                    # Upload with timeout
                    timeout = aiohttp.ClientTimeout(total=600)  # 10 minutes for upload

                    async with session.post(
                        self.upload_endpoint,
                        data=form_data,
                        timeout=timeout
                    ) as response:

                        if response.status == 200:
                            result = await response.json()

                            if result.get('status') == 'ok':
                                download_page = result['data']['downloadPage']

                                if message:
                                    await message.edit(f"✅ GoFile upload completed!\n🔗 Link: {download_page}")

                                return {
                                    'success': True,
                                    'download_page': download_page,
                                    'file_id': result['data'].get('code'),
                                    'file_size': file_size,
                                    'filename': filename
                                }
                            else:
                                error_msg = result.get('message', 'Unknown error')
                                if message:
                                    await message.edit(f"❌ GoFile upload failed: {error_msg}")
                                return None
                        else:
                            if message:
                                await message.edit(f"❌ GoFile server error: {response.status}")
                            return None

        except asyncio.TimeoutError:
            if message:
                await message.edit("❌ GoFile upload timed out!")
            return None
        except Exception as e:
            if message:
                await message.edit(f"❌ GoFile upload error: {str(e)}")
            return None

    async def get_server(self) -> Optional[str]:
        """Get best available GoFile server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.gofile.io/getServer') as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('status') == 'ok':
                            return result['data']['server']
            return None
        except:
            return None
