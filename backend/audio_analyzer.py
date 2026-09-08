import numpy as np
from scipy.io import wavfile


class AudioAnalyzer:
    def __init__(self, audioPath, targetFPS=60, numBars=64, attackFactor=0.45, decayFactor=0.15):
        self.sampleRate, data = wavfile.read(audioPath)
        
        if len(data.shape) > 1:
            self.audioData = np.mean(data, axis=1)
        else:
            self.audioData = data.copy()

        if np.issubdtype(self.audioData.dtype, np.integer):
            info = np.iinfo(self.audioData.dtype)
            self.audioData = self.audioData.astype(np.float32) / max(abs(info.min), abs(info.max))
        else:
            self.audioData = self.audioData.astype(np.float32)

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

    def getFrameData(self, frameIndex):
        if frameIndex >= self.totalFrames:
            return np.zeros(self.numBars, dtype=np.float32)

        centerSample = frameIndex * self.samplesPerFrame + (self.samplesPerFrame // 2)
        startSample = max(0, centerSample - (self.fftSize // 2))
        endSample = startSample + self.fftSize

        audioChunk = self.audioData[startSample:endSample]
        if len(audioChunk) < self.fftSize:
            audioChunk = np.pad(audioChunk, (0, self.fftSize - len(audioChunk)))

        windowedChunk = audioChunk * self.window
        fftMag = np.abs(np.fft.rfft(windowedChunk))

        # Interpolate continuous spectrum across frequencies to prevent bin collision
        rawBars = np.interp(self.barFreqs, self.fftFreqs, fftMag)

        # Apply slight spatial smoothing to eliminate rigid adjacent bar locks
        kernel = np.array([0.15, 0.70, 0.15])
        rawBars = np.convolve(rawBars, kernel, mode='same')

        # Auto Gain Control peak decay
        self.peakHistory = np.maximum(self.peakHistory * 0.988, rawBars)
        currentBars = rawBars / np.maximum(self.peakHistory, 1e-4)
        currentBars = np.clip(currentBars, 0.02, 1.0)

        # Dual-Stage Temporal Smoothing (Separate Attack vs Decay)
        smoothedBars = np.zeros(self.numBars, dtype=np.float32)
        for i in range(self.numBars):
            prev = self.previousFramebars[i]
            target = currentBars[i]
            if target > prev:
                # Attack phase: prevents instant jumpy snapping
                smoothedBars[i] = prev + (target - prev) * self.attackFactor
            else:
                # Decay phase: smooth floating drop
                smoothedBars[i] = prev + (target - prev) * self.decayFactor

        self.previousFramebars = smoothedBars.copy()
        return smoothedBars