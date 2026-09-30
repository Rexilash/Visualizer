import cv2
import numpy as np
import os


class FrameRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.width, self.height = settings["resolution"]
        self.scale = self.height / 1080.0

        self.bg_image =  None
        if settings.get("bg_mode") == "image" and settings.get("bg_image_path"):
            img_path = settings["bg_image_path"]
            if os.path.exists(img_path):
                loaded_img = cv2.imread(img_path)
                if loaded_img is not None:
                    self.bg_image = cv2.resize(loaded_img, (self.width, self.height), interpolation=cv2.INTER_AREA)

        # 1. Define Uniform Outer Margins / Inner Container Bounding Box
        self.margin_x = int(self.width * 0.1)
        self.margin_y = int(self.height * 0.1)

        self.container_x1 = self.margin_x
        self.container_x2 = self.width - self.margin_x
        self.container_y1 = self.margin_y
        self.container_y2 = self.height - self.margin_y

        self.container_w = self.container_x2 - self.container_x1
        self.container_h = self.container_y2 - self.container_y1

        # 2. Proportional Vertical Allocation inside Container
        self.max_bar_height = int(self.container_h * 0.74)  # Cap bar height
        self.bars_bottom = self.container_y1 + self.max_bar_height

        self.progress_y = self.container_y1 + int(self.container_h * 0.8025)
        self.title_y = self.container_y1 + int(self.container_h * 0.92)
        self.artist_y = self.container_y1 + int(self.container_h * 1)

        # Pre-generate vertical gradient matched strictly to container bar zone
        barBackground = np.array([
            [settings["tertiaryColor"]], 
            [settings["secondaryColor"]],
            [settings["primaryColor"]],
        ], dtype=np.uint8)
        gradient = cv2.resize(barBackground, (self.width, self.max_bar_height), interpolation=cv2.INTER_LINEAR)

        self.staticBarBackground = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.staticBarBackground[self.container_y1:self.bars_bottom, :] = gradient

    def _draw_rounded_rect(self, img, pt1, pt2, color, radius, thickness=-1):
        x1, y1 = pt1
        x2, y2 = pt2
        w, h = x2 - x1, y2 - y1

        if w <= 0 or h <= 0:
            return

        radius = max(1, min(radius, w // 2, h // 2))

        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)

        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, thickness)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, thickness)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, thickness)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, thickness)

    def renderFrame(self, audioFrameData, progress=0.0):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = self.settings["bgColor"]

        self._drawBars(frame, audioFrameData)
        self._drawProgressBar(frame, progress)
        self._drawText(frame)
        self._drawBorder(frame)

        return frame

    def _drawBars(self, frame, audioFrameData):
        count = len(audioFrameData)
        if count == 0:
            return

        mask = np.zeros((self.height, self.width), dtype=np.uint8)
        gap = max(8, int(16 * self.scale))
        total_gaps = gap * (count - 1)

        bar_width = max(2, (self.container_w - total_gaps) // count)
        total_rendered_w = (bar_width * count) + total_gaps
        start_x = self.container_x1 + (self.container_w - total_rendered_w) // 2

        corner_radius = max(2, int(bar_width // 2))

        for i in range(count):
            amplitude = audioFrameData[i]
            bar_h = int(amplitude * self.max_bar_height)

            if bar_h < corner_radius * 2:
                bar_h = corner_radius * 2

            x1 = start_x + i * (bar_width + gap)
            x2 = x1 + bar_width
            y1 = self.bars_bottom - bar_h
            y2 = self.bars_bottom

            self._draw_rounded_rect(mask, (x1, y1), (x2, y2), 255, radius=corner_radius, thickness=-1)

        cv2.copyTo(src=self.staticBarBackground, mask=mask, dst=frame)

    def _drawProgressBar(self, frame, progress):
        bar_h = max(4, int(6 * self.scale))

        x1 = self.container_x1
        y1 = self.progress_y
        x2 = self.container_x2
        y2 = self.progress_y + bar_h

        track_color = (50, 50, 60)
        self._draw_rounded_rect(frame, (x1, y1), (x2, y2), track_color, radius=bar_h // 2)

        if progress > 0.0:
            fill_x2 = int(x1 + (x2 - x1) * np.clip(progress, 0.0, 1.0))
            if fill_x2 > x1:
                self._draw_rounded_rect(frame, (x1, y1), (fill_x2, y2), self.settings["primaryColor"], radius=bar_h // 2)

    def _drawText(self, frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        titleScale = 2 * self.scale
        artistScale = 1.5 * self.scale
        titleThick = max(1, int(3 * self.scale))
        artistThick = max(1, int(2 * self.scale))

        if self.settings.get("title"):
            title = self.settings["title"]
            (w, _), _ = cv2.getTextSize(title, font, titleScale, titleThick)
            titleX = self.container_x1 + (self.container_w - w) // 2
            cv2.putText(frame, title, (titleX, self.title_y), font, titleScale, self.settings["titleColor"], titleThick, cv2.LINE_AA)

        if self.settings.get("artist"):
            artist = self.settings["artist"]
            (w, _), _ = cv2.getTextSize(artist, font, artistScale, artistThick)
            artistX = self.container_x1 + (self.container_w - w) // 2
            cv2.putText(frame, artist, (artistX, self.artist_y), font, artistScale, self.settings["artistColor"], artistThick, cv2.LINE_AA)

    def _drawBorder(self, frame):
        borderWidth = self.settings["borderWidth"]
        if borderWidth <= 0:
            return
        cv2.rectangle(frame, (0, 0), (self.width, self.height), self.settings["borderColor1"], borderWidth)
        cv2.rectangle(frame, (borderWidth, borderWidth), (self.width - borderWidth, self.height - borderWidth), self.settings["borderColor2"], 1)