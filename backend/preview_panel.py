import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from backend.frame_renderer import FrameRenderer


class PreviewPanel:
    def __init__(self, parent_frame):
        self.container = tk.LabelFrame(parent_frame, text=" Live Preview ", padx=10, pady=10)
        self.container.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Label(self.container, bg="black")
        self.canvas.pack(fill="both", expand=True)

    def refresh(self, config):
        """Renders a single preview frame based on the current RenderConfig."""
        settings = config.get_renderer_settings(title="PREVIEW MODE", override_res=(1280, 720))
        
        # Synthetic bar waveform
        sample_bars = np.sin(np.linspace(0, np.pi, config.num_bars)) * 0.75 + 0.1
        
        renderer = FrameRenderer(settings)
        bgr_frame = renderer.renderFrame(sample_bars)

        # Convert OpenCV BGR -> RGB -> PIL Image -> Tkinter Image
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame).resize((480, 270), Image.Resampling.LANCZOS)
        
        tk_img = ImageTk.PhotoImage(image=img)
        self.canvas.config(image=tk_img)
        self.canvas.image = tk_img  # Maintain reference