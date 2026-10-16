import os
import sys
import platform

def get_ffmpeg_cmd():
    """Dynamically locates bundled ffmpeg binary or falls back to system PATH."""
    is_windows = platform.system() == "Windows"
    ffmpeg_name = "ffmpeg.exe" if is_windows else "ffmpeg"

    if getattr(sys, 'frozen', False):
        bundled_ffmpeg = os.path.join(sys._MEIPASS, ffmpeg_name)
        if os.path.exists(bundled_ffmpeg):
            return bundled_ffmpeg
    
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    local_ffmpeg = os.path.join(base_dir, ffmpeg_name)
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    return "ffmpeg"