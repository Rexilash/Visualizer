import os
import cv2
import sys
import subprocess
from audio_analyzer import AudioAnalyzer
from frame_renderer import FrameRenderer
import uuid
import tempfile
from utils import get_ffmpeg_cmd

class VideoEngine:
    """Manages full video frame generation, audio extraction, and FFmpeg muxing."""
    def __init__(self, audio_path, config, progress_callback=None, status_callback=None, output_path=None):
        self.audio_path = audio_path
        self.config = config
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        # Ensure output path always has a .mp4 extension for FFmpeg container muxing
        if output_path and not output_path.lower().endswith('.mp4'):
            output_path += '.mp4'
        self.output_mp4_path = output_path

        session_id = str(uuid.uuid4())[:8]
        temp_dir = tempfile.gettempdir()
        
        self.temp_silent_video = os.path.join(temp_dir, f"tempSilentRender_{session_id}.mp4")
        self.temp_converted_wav = os.path.join(temp_dir, f"tempBackgroundDecode_{session_id}.wav")
        
        # Place downloaded URL audio directly in the target output folder
        if self.audio_path.startswith(("http://", "https://")) and self.output_mp4_path:
            out_dir = os.path.dirname(self.output_mp4_path)
            base_name = os.path.splitext(os.path.basename(self.output_mp4_path))[0]
            self.target_downloaded_audio = os.path.join(out_dir, f"{base_name}_audio.wav")
        else:
            self.target_downloaded_audio = None

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def _update_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _download_url_audio(self, url: str):
        """Downloads audio streams from YouTube or media links directly to the target output folder."""
        self._update_status("Downloading audio stream from URL...")
        
        if any(domain in url.lower() for domain in ["youtube.com", "youtu.be", "music.youtube.com", "soundcloud.com"]):
            try:
                import yt_dlp
                if not self.target_downloaded_audio:
                    out_dir = os.path.dirname(self.output_mp4_path) if self.output_mp4_path else tempfile.gettempdir()
                    self.target_downloaded_audio = os.path.join(out_dir, "downloaded_audio.wav")
                
                base_path = os.path.splitext(self.target_downloaded_audio)[0]
                ffmpeg_dir = os.path.dirname(get_ffmpeg_cmd())
                
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': base_path,
                    'ffmpeg_location': ffmpeg_dir,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                    }],
                    'quiet': True,
                    'noplaylist': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv', 'mweb', 'ios', 'android']
                        }
                    },
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                return
            except Exception as e:
                raise RuntimeError(f"Failed to download media link via yt-dlp: {e}")

        # Fallback for direct static file URLs
        ffmpeg_bin = get_ffmpeg_cmd()
        target_wav = self.target_downloaded_audio or self.temp_converted_wav
        cmd = [ffmpeg_bin, "-y", "-i", url, "-acodec", "pcm_s16le", "-ar", "44100", target_wav]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def render(self):
        """Executes the rendering and mixing pipeline."""
        analysis_path = self.audio_path
        video_writer = None
        ffmpeg_bin = get_ffmpeg_cmd()
        downloaded_audio_used = False

        try:
            # 1. Process Network URLs or Non-WAV Files
            if self.audio_path.startswith(("http://", "https://")):
                self._download_url_audio(self.audio_path)
                analysis_path = self.target_downloaded_audio
                downloaded_audio_used = True
            elif not self.audio_path.lower().endswith((".wav", ".wave")):
                self._update_status("Unpacking audio stream...")
                convert_cmd = [
                    ffmpeg_bin, "-y", "-i", self.audio_path, 
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-acodec", "pcm_s16le", "-ar", "44100", self.temp_converted_wav
                ]
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
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", 
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                "-shortest", self.output_mp4_path
            ]
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._update_status(f"Completed: {os.path.basename(self.audio_path)}")
            
            # 5. Clean up downloaded source audio upon successful completion
            if downloaded_audio_used and self.target_downloaded_audio and os.path.exists(self.target_downloaded_audio):
                try:
                    os.remove(self.target_downloaded_audio)
                except Exception:
                    pass

            return True

        finally:
            if video_writer is not None and video_writer.isOpened():
                video_writer.release()
            if os.path.exists(self.temp_silent_video):
                os.remove(self.temp_silent_video)
            if os.path.exists(self.temp_converted_wav):
                os.remove(self.temp_converted_wav)