"""
Enhanced VideoMerge-Bot Helper Modules
Provides comprehensive video processing, downloading, and uploading capabilities
"""

__version__ = "2.0.0"
__author__ = "AbirHasan2005"

# Import only the modules that actually exist
try:
    from .downloader import DirectDownloader
except ImportError:
    DirectDownloader = None

try:
    from .gofile_uploader import GoFileUploader
except ImportError:
    GoFileUploader = None

try:
    from .uploader import UploadVideo
except ImportError:
    UploadVideo = None

try:
    from .merger import VideoMerger
except ImportError:
    VideoMerger = None

try:
    from .display_progress import humanbytes, TimeFormatter
except ImportError:
    humanbytes = None
    TimeFormatter = None

# Only include items that were successfully imported
__all__ = [item for item in [
    'DirectDownloader',
    'GoFileUploader', 
    'UploadVideo',
    'VideoMerger',
    'humanbytes',
    'TimeFormatter'
] if item is not None]
