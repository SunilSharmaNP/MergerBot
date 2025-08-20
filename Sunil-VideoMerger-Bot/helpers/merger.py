"""
Enhanced video merger module with advanced FFmpeg operations
Provides comprehensive video merging with format detection and optimization
"""

import asyncio
import os
import time
import json
from typing import List, Optional, Dict, Any, Tuple
from configs import Config
from helpers.display_progress import humanbytes, TimeFormatter
from pyrogram.types import Message
import logging

logger = logging.getLogger(__name__)

class VideoMerger:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.work_dir = f"{Config.DOWN_PATH}/{user_id}"
        self.input_file = f"{self.work_dir}/input.txt"
        self.temp_dir = f"{self.work_dir}/temp"

        # Ensure directories exist
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    async def merge_videos(self, video_list: List[str], message: Message, 
                          format_: str = "mp4") -> Optional[str]:
        """
        Enhanced video merging with format validation and optimization
        """
        try:
            if len(video_list) < 2:
                await message.edit("❌ At least 2 videos required for merging!")
                return None

            logger.info(f"Starting merge for user {self.user_id} with {len(video_list)} videos")

            # Validate input videos
            valid_videos = await self._validate_videos(video_list, message)
            if not valid_videos:
                return None

            # Analyze videos for compatibility
            video_info = await self._analyze_videos(valid_videos, message)
            if not video_info:
                return None

            # Create input file for FFmpeg
            await self._create_input_file(valid_videos)

            # Determine output format and settings
            output_settings = self._get_optimal_settings(video_info, format_)
            output_path = f"{self.work_dir}/[@AbirHasan2005]_Merged.{output_settings['format']}"

            # Perform merge operation
            success = await self._execute_merge(output_path, output_settings, message)

            if success and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Merge completed: {output_path} ({humanbytes(file_size)})")
                return output_path
            else:
                logger.error("Merge failed - output file not created")
                return None

        except Exception as e:
            logger.error(f"Merge error for user {self.user_id}: {e}")
            await message.edit(f"❌ **Merge failed:** `{str(e)}`")
            return None

    async def _validate_videos(self, video_list: List[str], message: Message) -> List[str]:
        """Validate that all video files exist and are accessible"""
        valid_videos = []

        await message.edit("🔍 **Validating video files...**")

        for i, video_path in enumerate(video_list):
            if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                valid_videos.append(video_path)
                logger.debug(f"Video {i+1} validated: {os.path.basename(video_path)}")
            else:
                logger.warning(f"Invalid video file: {video_path}")

        if len(valid_videos) < 2:
            await message.edit(f"❌ Only {len(valid_videos)} valid videos found. Need at least 2!")
            return []

        if len(valid_videos) < len(video_list):
            await message.edit(f"⚠️ Using {len(valid_videos)}/{len(video_list)} valid videos for merge...")
            await asyncio.sleep(2)

        return valid_videos

    async def _analyze_videos(self, video_list: List[str], message: Message) -> Optional[Dict[str, Any]]:
        """Analyze video properties for optimal merge settings"""
        try:
            await message.edit("🔍 **Analyzing video properties...**")

            video_info = {
                'codecs': set(),
                'formats': set(),
                'resolutions': set(),
                'frame_rates': set(),
                'total_duration': 0,
                'total_size': 0,
                'videos': []
            }

            for video_path in video_list:
                # Get basic file info
                file_size = os.path.getsize(video_path)
                file_ext = os.path.splitext(video_path)[1].lower()

                video_info['formats'].add(file_ext)
                video_info['total_size'] += file_size

                # Try to get detailed video info using FFprobe
                detailed_info = await self._get_video_details(video_path)
                if detailed_info:
                    video_info['videos'].append({
                        'path': video_path,
                        'size': file_size,
                        'duration': detailed_info.get('duration', 0),
                        'codec': detailed_info.get('codec', 'unknown'),
                        'resolution': detailed_info.get('resolution', 'unknown'),
                        'fps': detailed_info.get('fps', 'unknown')
                    })

                    video_info['total_duration'] += detailed_info.get('duration', 0)
                    video_info['codecs'].add(detailed_info.get('codec', 'unknown'))
                    video_info['resolutions'].add(detailed_info.get('resolution', 'unknown'))
                    video_info['frame_rates'].add(detailed_info.get('fps', 'unknown'))

            logger.info(f"Analysis complete: {len(video_list)} videos, total size: {humanbytes(video_info['total_size'])}")
            return video_info

        except Exception as e:
            logger.error(f"Video analysis error: {e}")
            await message.edit("⚠️ **Video analysis failed, proceeding with basic merge...**")
            return {'formats': {'.mp4'}, 'total_size': sum(os.path.getsize(v) for v in video_list)}

    async def _get_video_details(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed video information using FFprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                data = json.loads(stdout.decode())

                # Extract video stream info
                video_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break

                if video_stream:
                    duration = float(data.get('format', {}).get('duration', 0))

                    return {
                        'duration': duration,
                        'codec': video_stream.get('codec_name', 'unknown'),
                        'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}",
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')) if '/' in str(video_stream.get('r_frame_rate', '0')) else 0,
                        'bitrate': int(video_stream.get('bit_rate', 0))
                    }
        except Exception as e:
            logger.debug(f"FFprobe failed for {video_path}: {e}")

        return None

    async def _create_input_file(self, video_list: List[str]):
        """Create FFmpeg input file list"""
        with open(self.input_file, 'w', encoding='utf-8') as f:
            for video_path in video_list:
                # Use absolute path and escape special characters
                escaped_path = video_path.replace('\', '/').replace("'", "\'")
                f.write(f"file '{escaped_path}'\n")

        logger.debug(f"Created input file: {self.input_file}")

    def _get_optimal_settings(self, video_info: Dict[str, Any], requested_format: str) -> Dict[str, Any]:
        """Determine optimal merge settings based on video analysis"""
        settings = {
            'format': requested_format.lower(),
            'method': 'concat',  # Default method
            'additional_args': []
        }

        # Analyze format compatibility
        formats = video_info.get('formats', set())
        if len(formats) == 1 and requested_format.lower() in str(formats):
            # All videos have same format, use fast concat
            settings['method'] = 'concat'
            settings['additional_args'] = ['-c', 'copy']  # Copy streams without re-encoding
        else:
            # Mixed formats, need re-encoding
            settings['method'] = 'filter_complex'
            settings['additional_args'] = [
                '-c:v', 'libx264',  # Video codec
                '-preset', 'medium',  # Encoding speed/quality balance
                '-crf', '23',  # Quality level
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k'  # Audio bitrate
            ]

        # Optimize based on total file size
        total_size = video_info.get('total_size', 0)
        if total_size > 1073741824:  # > 1GB
            settings['additional_args'].extend(['-preset', 'fast'])  # Faster encoding for large files

        return settings

    async def _execute_merge(self, output_path: str, settings: Dict[str, Any], 
                           message: Message) -> bool:
        """Execute the actual FFmpeg merge operation"""
        try:
            if settings['method'] == 'concat':
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', self.input_file
                ] + settings['additional_args'] + [
                    '-y',  # Overwrite output file
                    output_path
                ]
            else:
                # More complex merge for mixed formats
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', self.input_file
                ] + settings['additional_args'] + [
                    '-y',
                    output_path
                ]

            logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")

            # Start FFmpeg process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Monitor progress
            await message.edit("🔄 **Merging videos with FFmpeg...**\n\nThis may take several minutes...")

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=3600  # 1 hour timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await message.edit("❌ **Merge timeout!** Process took longer than 1 hour.")
                return False

            # Check result
            if process.returncode == 0:
                logger.info("FFmpeg merge completed successfully")
                return True
            else:
                error_msg = stderr.decode().strip()
                logger.error(f"FFmpeg merge failed: {error_msg}")
                await message.edit(f"❌ **FFmpeg Error:**\n```\n{error_msg[-500:]}\n```")
                return False

        except Exception as e:
            logger.error(f"Merge execution error: {e}")
            await message.edit(f"❌ **Merge execution failed:** `{str(e)}`")
            return False

    async def create_sample_video(self, video_path: str, duration: int = 30) -> Optional[str]:
        """Create a sample video from the merged result"""
        try:
            sample_path = f"{self.work_dir}/sample_{int(time.time())}.mp4"

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-t', str(duration),  # Sample duration
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '28',  # Slightly lower quality for smaller size
                '-c:a', 'aac',
                '-y',
                sample_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

            if process.returncode == 0 and os.path.exists(sample_path):
                logger.info(f"Sample video created: {sample_path}")
                return sample_path

        except Exception as e:
            logger.error(f"Sample creation error: {e}")

        return None

    async def generate_thumbnails(self, video_path: str, count: int = 3) -> List[str]:
        """Generate thumbnail images from the merged video"""
        thumbnails = []

        try:
            # Get video duration for thumbnail timing
            duration_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                video_path
            ]

            process = await asyncio.create_subprocess_exec(
                *duration_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()

            try:
                duration = float(stdout.decode().strip())
            except:
                duration = 60  # Default if duration detection fails

            # Generate thumbnails at different time points
            for i in range(count):
                time_point = (duration / (count + 1)) * (i + 1)
                thumbnail_path = f"{self.work_dir}/thumb_{i+1}_{int(time.time())}.jpg"

                thumb_cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(time_point),
                    '-vframes', '1',
                    '-q:v', '2',  # High quality
                    '-y',
                    thumbnail_path
                ]

                thumb_process = await asyncio.create_subprocess_exec(
                    *thumb_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                await thumb_process.communicate()

                if thumb_process.returncode == 0 and os.path.exists(thumbnail_path):
                    thumbnails.append(thumbnail_path)
                    logger.debug(f"Thumbnail created: {thumbnail_path}")

        except Exception as e:
            logger.error(f"Thumbnail generation error: {e}")

        return thumbnails

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.input_file):
                os.remove(self.input_file)

            # Clean temp directory
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)

            logger.info(f"Cleanup completed for user {self.user_id}")

        except Exception as e:
            logger.warning(f"Cleanup error for user {self.user_id}: {e}")

# Convenience functions for backward compatibility
async def MergeVideo(input_file: str, user_id: int, message: Message, format_: str) -> Optional[str]:
    """
    Legacy function wrapper for backward compatibility
    """
    try:
        # Read video list from input file
        video_list = []
        with open(input_file, 'r') as f:
            for line in f:
                if line.startswith("file '"):
                    video_path = line.strip()[6:-1]  # Remove "file '" and "'"
                    video_list.append(video_path)

        # Use new merger
        merger = VideoMerger(user_id)
        result = await merger.merge_videos(video_list, message, format_)
        merger.cleanup()

        return result

    except Exception as e:
        logger.error(f"Legacy merge function error: {e}")
        return None

# Additional utility functions
async def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            video_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()

        if process.returncode == 0:
            return float(stdout.decode().strip())
    except:
        pass

    return 0.0

async def get_video_resolution(video_path: str) -> Tuple[int, int]:
    """Get video resolution (width, height)"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            video_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()

        if process.returncode == 0:
            resolution = stdout.decode().strip()
            if 'x' in resolution:
                width, height = map(int, resolution.split('x'))
                return width, height
    except:
        pass

    return 1280, 720  # Default resolution

def validate_merge_compatibility(video_list: List[str]) -> Dict[str, Any]:
    """Validate if videos can be merged together"""
    compatibility = {
        'compatible': True,
        'issues': [],
        'recommendations': []
    }

    if len(video_list) < 2:
        compatibility['compatible'] = False
        compatibility['issues'].append("At least 2 videos required")
        return compatibility

    # Check file existence
    missing_files = [v for v in video_list if not os.path.exists(v)]
    if missing_files:
        compatibility['compatible'] = False
        compatibility['issues'].append(f"Missing files: {len(missing_files)}")

    # Check file sizes
    empty_files = [v for v in video_list if os.path.exists(v) and os.path.getsize(v) == 0]
    if empty_files:
        compatibility['compatible'] = False
        compatibility['issues'].append(f"Empty files: {len(empty_files)}")

    # Check formats
    formats = set()
    for video_path in video_list:
        if os.path.exists(video_path):
            ext = os.path.splitext(video_path)[1].lower()
            formats.add(ext)

    if len(formats) > 1:
        compatibility['recommendations'].append("Mixed formats detected - re-encoding will be required")

    return compatibility
