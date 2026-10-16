import numpy as np
import subprocess
import sys
import os
from utils import get_ffmpeg_cmd

class AudioAnalyzer:
    """
    Parses audio files using FFmpeg piping, performs Fast Fourier Transform (FFT) 
    frequency analysis, and calculates smoothed logarithmic frequency band magnitudes.
    """
    def __init__(self, audioPath, targetFPS=60, numBars=64, attackFactor=0.45, decayFactor=0.15):
        self.sampleRate = 44100
        ffmpeg_bin = get_ffmpeg_cmd()

        # Pipe any audio/video file directly into raw 16-bit PCM mono stream using FFmpeg
        cmd = [
            ffmpeg_bin, "-y", "-i", audioPath,
            "-f", "s16le", "-ac", "1", "-ar", str(self.sampleRate), "pipe:1"
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            data = np.frombuffer(result.stdout, dtype=np.int16)
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"FFmpeg audio decoding failed: {err_msg}")

        # Normalize 16-bit signed integer PCM to float32 range [-1.0, 1.0]
        self.audioData = data.astype(np.float32) / 32768.0

        self.fps = targetFPS
        self.numBars = numBars
        self.attackFactor = attackFactor  # Controls upward movement speed
        self.decayFactor = decayFactor    # Controls downward fall speed
        
        self.samplesPerFrame = int(self.sampleRate / self.fps)
        self.totalFrames = int(len(self.audioData) / self.samplesPerFrame)
        self.previousFramebars = np.zeros(self.numBars, dtype=np.float32)
        self.peakHistory = np.ones(self.numBars, dtype=np.float32) * 0.05

        # 4096 FFT size gives 10.7 Hz bin resolution for fine sub-bass distinction
        self.fftSize = 4096
        self.window = np.hanning(self.fftSize)

        # Logarithmic frequency distribution targets from 25 Hz to 12,000 Hz
        self.barFreqs = np.logspace(np.log10(25.0), np.log10(12000.0), self.numBars)
        self.fftFreqs = np.fft.rfftfreq(self.fftSize, 1.0 / self.sampleRate)
        self.processed_frames = self._precompute_all_frames()

    def _precompute_all_frames(self):
        """Pre-computes and smooths FFT spectra for all frames upfront."""
        frames_matrix = np.zeros((self.totalFrames, self.numBars), dtype=np.float32)
        prev_bars = np.zeros(self.numBars, dtype=np.float32)
        peak_history = np.ones(self.numBars, dtype=np.float32) * 0.05
        kernel = np.array([0.15, 0.70, 0.15])

        for f in range(self.totalFrames):
            center = f * self.samplesPerFrame + (self.samplesPerFrame // 2)
            start = max(0, center - (self.fftSize // 2))
            end = start + self.fftSize
            chunk = self.audioData[start:end]
            if len(chunk) < self.fftSize:
                chunk = np.pad(chunk, (0, self.fftSize - len(chunk)))

            fft_mag = np.abs(np.fft.rfft(chunk * self.window))
            raw_bars = np.interp(self.barFreqs, self.fftFreqs, fft_mag)
            raw_bars = np.convolve(raw_bars, kernel, mode='same')

            peak_history = np.maximum(peak_history * 0.992, raw_bars)
            # Add a 0.2 noise floor threshold so quiet sections don't auto-amplify to full height
            current_bars = np.clip(raw_bars / np.maximum(peak_history, 0.2), 0.0, 1.0)

            smoothed = np.where(
                current_bars > prev_bars,
                prev_bars + (current_bars - prev_bars) * self.attackFactor,
                prev_bars + (current_bars - prev_bars) * self.decayFactor
            )
            frames_matrix[f] = smoothed
            prev_bars = smoothed

        return frames_matrix

    def getFrameData(self, frameIndex):
        if frameIndex >= self.totalFrames:
            return np.zeros(self.numBars, dtype=np.float32)
        return self.processed_frames[frameIndex]