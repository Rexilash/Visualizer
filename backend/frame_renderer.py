import cv2
import numpy as np


class FrameRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.width, self.height = settings["resolution"]
        self.scale = self.height / 1080.0
        borderWidth = self.settings["borderWidth"]
        usableHeight = self.height - (borderWidth * 2)
        maxBarPixels = int(usableHeight * self.settings["maxHeightPct"])

        barBackground = np.array([
            [settings["tertiaryColor"]], 
            [settings["secondaryColor"]],
            [settings["primaryColor"]],
        ], dtype=np.uint8)
        gradient = cv2.resize(barBackground, (self.width, maxBarPixels), interpolation=cv2.INTER_LINEAR)

        self.staticBarBackground = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        baselineY = self.height - borderWidth
        top_y = max(0, baselineY - maxBarPixels)
        self.staticBarBackground[top_y:baselineY, :] = gradient

    def renderFrame(self, audioFrameData):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = self.settings["bgColor"]

        # Layer 1: Draw faded text onto background
        self._drawText(frame)

        count = len(audioFrameData)
        if count == 0:
            self._drawBorder(frame)
            return frame

        # Layer 2: Audio spectrum bars over text
        mask = np.zeros((self.height, self.width), dtype=np.uint8)
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

        cv2.copyTo(src=self.staticBarBackground, mask=mask, dst=frame)

        # Layer 3: Framing border
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

        text_items = [
            (self.settings["title"], titleY, titleScale, self.settings["titleColor"], titleThick),
            (self.settings["artist"], artistY, artistScale, self.settings["artistColor"], artistThick)
        ]

        for text, y_baseline, scale, color, thickness in text_items:
            if not text:
                continue

            # 1. Get exact text dimensions
            (text_w, text_h), baseline = cv2.getTextSize(text, font, scale, thickness)
            if text_w == 0 or text_h == 0:
                continue

            # 2. Define local container bounds (ROI) on the frame
            box_x1 = max(0, margin)
            box_y1 = max(0, y_baseline - text_h - 2)
            box_x2 = min(self.width, margin + text_w + 10)
            box_y2 = min(self.height, y_baseline + baseline + 2)

            box_h = box_y2 - box_y1
            box_w = box_x2 - box_x1

            if box_h <= 0 or box_w <= 0:
                continue

            # 3. Create isolated container and alpha mask for this text block
            container = np.zeros((box_h, box_w, 3), dtype=np.uint8)
            mask = np.zeros((box_h, box_w), dtype=np.uint8)

            local_x = margin - box_x1
            local_y = y_baseline - box_y1

            cv2.putText(container, text, (local_x, local_y), font, scale, color, thickness, cv2.LINE_AA)
            cv2.putText(mask, text, (local_x, local_y), font, scale, 255, thickness, cv2.LINE_AA)

            # 4. Local gradient scaled strictly to this container's height (100% top to 30% bottom)
            fade_1d = np.linspace(1.0, 0.3, box_h, dtype=np.float32)
            local_alpha = (mask / 255.0).astype(np.float32) * fade_1d[:, None]
            local_alpha = local_alpha[:, :, None]

            # 5. Blend local container directly onto frame background ROI
            frame_roi = frame[box_y1:box_y2, box_x1:box_x2].astype(np.float32)
            container_float = container.astype(np.float32)

            blended_roi = frame_roi * (1.0 - local_alpha) + container_float * local_alpha
            frame[box_y1:box_y2, box_x1:box_x2] = np.clip(blended_roi, 0, 255).astype(np.uint8)

    def _drawBorder(self, frame):
        borderWidth = self.settings["borderWidth"]
        if borderWidth <= 0:
            return
        cv2.rectangle(frame, (0, 0), (self.width, self.height), self.settings["borderColor1"], borderWidth)
        cv2.rectangle(frame, (borderWidth, borderWidth), (self.width - borderWidth, self.height - borderWidth), self.settings["borderColor2"], 1)