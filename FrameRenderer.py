import os
import cv2
import numpy as np
import subprocess
from scipy.io import wavfile

# Import Python's built-in UI libraries
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

class  FrameRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.width, self.height = settings["resolution"]
        barBackground = np.array([[settings["tertiaryColor"]], [settings["secondaryColor"]], [settings["primaryColor"]]], dtype = np.unint8)
        self.staticBarBackground = cv2.resize(barBackground, (self.width, self.height), interpolation = cv2.INTER_LINEAR)

    def renderFrame(self. audioFrameData):
        frame = np.zeros((self.height, self.width, 3), dtype = np.uint8)
        frame[:] = self.settings["bgColor"]
        mask = np.zeros((self.height, self.width), dtype = np.unint8)
        count = len(audioFrameData)
        borderWidth = self.settings["borderWidth"]
        gap = self.settings["barGap"]
        baselineY = self.height - borderWidth
        usableWidth = self.width - (borderWidth * 2)
        usableHeight = self.height - (borderWidth * 2)
        barWidth = max(1, int((usableWidth - (gap * (count + 1))) / count))
        maxbarPixels = int(usableHeight * self.settings["maxHeightPercent"])

        for i in range(count):
            amplitude = audioFramedata[i]
            barHeight = int(amplitude * maxBarPixels)
            x1 = borderWidth + (gap * (i + 1)) + (i * barWidth)
            x2 = x1 + barWidth
            y1 = baselineY - barHeight
            cv2.rectangle(mask, (x1, y1), (x2, baselineY), 255, -1)
        
        cv2.copyTo(src = self.staticBarBackground, mask = mask, dst = frame)
        self._drawText(frame)
        self._drawBorder(frame)
        return frame
    def _drawText(self, frame):
        borderWidth = self.settings["borderWidth"]
        if borderWidth <= 0: return
        cv2.rectangle(frame, (0, 0), (self.width, self.height), self.settings["borderColor1"], borderWidth)
        cv2.rectangle(frame, (borderWidth, borderWidth), (self.width - borderWidth, self.height - borderWidth), self.settings["borderColor2"], 1)