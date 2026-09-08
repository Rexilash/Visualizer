import cv2
import numpy as np
from scipy.io import wavfile


class  FrameRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.width, self.height = settings["resolution"]
        self.scale= self.height / 1080.0
        borderWidth = self.settings["borderWidth"]
        usableHeight = self.height - (borderWidth * 2)
        maxBarPixels = int(usableHeight * self.settings["maxHeightPct"])
        
        barBackground = np.array([
            [settings["tertiaryColor"]], 
            [settings["secondaryColor"]],
            [settings["primaryColor"]],
        ], dtype = np.uint8)
        gradient = cv2.resize(barBackground, (self.width, maxBarPixels), interpolation = cv2.INTER_LINEAR)

        self.staticBarBackground = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        baselineY = self.height - borderWidth
        top_y = max(0, baselineY - maxBarPixels)
        self.staticBarBackground[top_y:baselineY, :] = gradient

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
        total_bar_space = usableWidth - (gap * (count + 1))
        maxBarPixels = int(usableHeight * self.settings["maxHeightPct"])

        for i in range(count):
            amplitude = audioFrameData[i]
            barHeight = int(amplitude * maxBarPixels)
            bar_left = int(i * total_bar_space / count)
            bar_right = int((i + 1) * total_bar_space / count)
            x1 = borderWidth + (gap * (i + 1)) + bar_left
            x2 = borderWidth + (gap * (i + 1)) + bar_right
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