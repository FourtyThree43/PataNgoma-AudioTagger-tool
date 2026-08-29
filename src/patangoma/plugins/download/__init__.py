"""Download plugins package for PataNgoma."""

from patangoma.plugins.download.aria2 import Aria2DownloadPlugin
from patangoma.plugins.download.yt_dlp import YtDlpDownloadPlugin

__all__ = ["Aria2DownloadPlugin", "YtDlpDownloadPlugin"]
