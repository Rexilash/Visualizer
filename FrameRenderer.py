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
        self.scale= self.height / 1080.0
        barBackground = np.array([[settings["tertiaryColor"]], [settings["secondaryColor"]], [settings["primaryColor"]]], dtype = np.uint8)
        self.staticBarBackground = cv2.resize(barBackground, (self.width, self.height), interpolation = cv2.INTER_LINEAR)

    def renderFrame(self, audioFrameData):
        frame = np.zeros((self.height, self.width, 3), dtype = np.uint8)
        frame[:] = self.settings["bgColor"]
        count = len(audioFrameData)
        if count == 0:
            self._drawText(frame)
            self._drawBorder(frame)
            return frame
        mask = np.zeros((self.height, self.width), dtype = np.uint8)
        borderWidth = self.settings["borderWidth"]
        gap = self.settings["barGap"]
        baselineY = self.height - borderWidth
        usableWidth = self.width - (borderWidth * 2)
        usableHeight = self.height - (borderWidth * 2)
        barWidth = max(1, int((usableWidth - (gap * (count + 1))) / count))
        maxBarPixels = int(usableHeight * self.settings["maxHeightPct"])

        for i in range(count):
            amplitude = audioFrameData[i]
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
        font = cv2.FONT_HERSHEY_SIMPLEX
        margin = int(self.settings["borderWidth"] + (60 * self.scale))
        titleScale = 2.5 * self.scale
        artistScale = 1.2 * self.scale
        titleY = int(150 * self.scale)
        artistY = int(240 * self.scale)
        titleThick = max(1, int(5 * self.scale))
        artistThick = max(1, int(2 * self.scale))
        cv2.putText(frame, self.settings["title"], (margin, titleY), font, titleScale, self.settings["titleColor"], titleThick, cv2.LINE_AA)
        cv2.putText(frame, self.settings["artist"], (margin, artistY), font, artistScale, self.settings["artistColor"], artistThick, cv2.LINE_AA)
    
    def _drawBorder(self, frame):
        borderWidth = self.settings["borderWidth"]
        if borderWidth <= 0: return
        cv2.rectangle(frame, (0, 0), (self.width, self.height), self.settings["borderColor1"], borderWidth)
        cv2.rectangle(frame, (borderWidth, borderWidth), (self.width - borderWidth, self.height - borderWidth), self.settings["borderColor2"], 1)