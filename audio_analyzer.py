import numpy as np
from scipy.io import wavfile


class AudioAnalyzer:
    def __init__(self, audioPath, targetFPS = 60, numBars = 64, smoothingFactor = 0.15):
        self.sampleRate, data  = wavfile.read(audioPath)
        if len(data.shape) > 1:
            self.audioData = np.mean(data, axis = 1)
        else:
            self.audioData = data
        
        if self.audioData.dtype == np.int16:
            self.audioData = self.audioData.astype(np.float32) / 32768.0
        elif self.audioData.dtype == np.int32:
            self.audioData = self.audioData.astype(np.float32) / 2147483648.0

        self.fps = targetFPS
        self.numBars = numBars
        self.smoothingFactor = smoothingFactor
        self.samplesPerFrame = int(self.sampleRate /  self.fps)
        self.totalFrames = int(len(self.audioData) / (self.samplesPerFrame))
        self.previousFramebars = np.zeros(self.numBars, dtype = np.float32)
        self.barEdges = np.logspace(np.log10(1), np.log10(self.samplesPerFrame // 2), self.numBars + 1).astype(int)

    def getFrameData(self,  frameIndex):
        if frameIndex >= self.totalFrames:
            return np.zeros(self.numBars, dtype = np.float32)
        startSample = frameIndex * self.samplesPerFrame
        endSample = startSample + self.samplesPerFrame
        audioChunk = self.audioData[startSample:endSample]
        if len(audioChunk) < self.samplesPerFrame:
            audioChunk = np.pad(audioChunk, (0, self.samplesPerFrame - len(audioChunk)))
        fftData = np.abs(np.fft.rfft(audioChunk))
        currentBars = np.zeros(self.numBars, dtype = np.float32)
        for i in range(self.numBars):
            startIdx = self.barEdges[i]
            endIdx = max(startIdx + 1, self.barEdges[i + 1])
            currentBars[i] = np.mean(fftData[startIdx:endIdx])
        currentBars =  currentBars * 2.5
        currentBars = np.clip(currentBars, 0.0, 1.0)
        for i in range(self.numBars):
            if currentBars[i] < self.previousFramebars[i]:
                currentBars[i] = (currentBars[i] * self.smoothingFactor) + (self.previousFramebars[i] * (1.0 - self.smoothingFactor))
        self.previousFramebars = currentBars.copy()
        return currentBars