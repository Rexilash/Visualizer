import os
import cv2
import sys
import subprocess
from audio_analyzer import AudioAnalyzer
from frame_renderer import FrameRenderer
import uuid
import tempfile


def get_ffmpeg_cmd():
    """Dynamically locates bundled ffmpeg.exe or falls back to system PATH."""
    if getattr(sys, 'frozen', False):
        bundled_ffmpeg = os.path.join(sys._MEIPASS, "ffmpeg.exe")
        if os.path.exists(bundled_ffmpeg):
            return bundled_ffmpeg
    
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    local_ffmpeg = os.path.join(base_dir, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    return "ffmpeg"


class VideoEngine:
    """Manages full video frame generation, audio extraction, and FFmpeg muxing."""
    def __init__(self, audio_path, config, progress_callback=None, status_callback=None, output_path=None):
        self.audio_path = audio_path
        self.config = config
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        session_id = str(uuid.uuid4())[:8]
        temp_dir = tempfile.gettempdir()
        
        # Save temp files to OS temp directory to avoid permission errors
        self.temp_silent_video = os.path.join(temp_dir, f"tempSilentRender_{session_id}.mp4")
        self.temp_converted_wav = os.path.join(temp_dir, f"tempBackgroundDecode_{session_id}.wav")
        self.output_mp4_path = output_path

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def _update_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _download_url_audio(self, url: str):
        """Streams direct network audio URLs to a local 16-bit PCM WAV using FFmpeg."""
        self._update_status("Fetching audio stream from URL...")
        ffmpeg_bin = get_ffmpeg_cmd()
        cmd = [ffmpeg_bin, "-y", "-i", url, "-acodec", "pcm_s16le", "-ar", "44100", self.temp_converted_wav]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def render(self):
        """Executes the rendering and mixing pipeline."""
        analysis_path = self.audio_path
        video_writer = None
        ffmpeg_bin = get_ffmpeg_cmd()

        try:
            # 1. Process Network URLs or Non-WAV Files
            if self.audio_path.startswith(("http://", "https://")):
                self._download_url_audio(self.audio_path)
                analysis_path = self.temp_converted_wav
            elif not self.audio_path.lower().endswith((".wav", ".wave")):
                self._update_status("Unpacking audio stream...")
                convert_cmd = [ffmpeg_bin, "-y", "-i", self.audio_path, "-acodec", "pcm_s16le", "-ar", "44100", self.temp_converted_wav]
                subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                analysis_path = self.temp_converted_wav

            # 2. Setup Audio FFT Analyzer & Frame Renderer
            self._update_status("Rendering video frames...")
            audio = AudioAnalyzer(analysis_path, targetFPS=60, numBars=self.config.num_bars)
            settings = self.config.get_renderer_settings()
            renderer = FrameRenderer(settings)

            width, height = settings["resolution"]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(self.temp_silent_video, fourcc, float(audio.fps), (width, height))

            # 3. Render loop
            for frame_idx in range(audio.totalFrames):
                bar_data = audio.getFrameData(frame_idx)
                progress = frame_idx / float(max(1, audio.totalFrames))
                completed_frame = renderer.renderFrame(bar_data, progress=progress)
                video_writer.write(completed_frame)

                if frame_idx % 15 == 0:
                    self._update_progress(frame_idx, audio.totalFrames)

            video_writer.release()
            video_writer = None

            # 4. Audio/Video FFmpeg merge
            self._update_status("Merging audio track...")
            ffmpeg_cmd = [
                ffmpeg_bin, "-y", "-i", self.temp_silent_video, "-i", analysis_path, 
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", self.output_mp4_path
            ]
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._update_status(f"Completed: {os.path.basename(self.audio_path)}")
            return True

        finally:
            if video_writer is not None and video_writer.isOpened():
                video_writer.release()
            if os.path.exists(self.temp_silent_video):
                os.remove(self.temp_silent_video)
            if os.path.exists(self.temp_converted_wav):
                os.remove(self.temp_converted_wav)