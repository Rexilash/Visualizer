import os
import cv2
import subprocess
from audio_analyzer import AudioAnalyzer
from frame_renderer import FrameRenderer


class VideoEngine:
    def __init__(self, audio_path, config, progress_callback=None, status_callback=None):
        self.audio_path = audio_path
        self.config = config
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        self.temp_silent_video = "tempSilentRender.mp4"
        self.temp_converted_wav = "tempBackgroundDecode.wav"
        self.output_mp4_path = "completedRender.mp4"

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def _update_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def render(self):
        """Executes the rendering and mixing pipeline."""
        analysis_path = self.audio_path
        video_writer = None

        try:
            # 1. Convert non-wav formats
            if not self.audio_path.lower().endswith((".wav", ".wave")):
                self._update_status("Unpacking audio stream...")
                convert_cmd = ["ffmpeg", "-y", "-i", self.audio_path, self.temp_converted_wav]
                subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                analysis_path = self.temp_converted_wav

            self._update_status("Rendering video frames...")
            audio = AudioAnalyzer(analysis_path, targetFPS=60, numBars=self.config.num_bars)
            settings = self.config.get_renderer_settings()
            renderer = FrameRenderer(settings)

            width, height = settings["resolution"]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(self.temp_silent_video, fourcc, float(audio.fps), (width, height))

            # 2. Render loop
            for frame_idx in range(audio.totalFrames):
                bar_data = audio.getFrameData(frame_idx)
                completed_frame = renderer.renderFrame(bar_data)
                video_writer.write(completed_frame)

                if frame_idx % 15 == 0:
                    self._update_progress(frame_idx, audio.totalFrames)

            video_writer.release()
            video_writer = None

            # 3. Audio/Video FFmpeg merge
            self._update_status("Merging audio track...")
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", self.temp_silent_video, "-i", analysis_path, 
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