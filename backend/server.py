# server.py
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import Response
from render_config import RenderConfig
from preview_panel import FrameRenderer
import cv2
import numpy as np

app = FastAPI()
config = RenderConfig()

@app.post("/config/update")
def update_config(bars: int, res_key: str, primary_rgb: list[int]):
    config.num_bars = bars
    config.selected_res_key = res_key
    config.rgb_primary = tuple(primary_rgb)
    return {"status": "ok"}

@app.get("/preview")
def get_preview():
    # Render frame using existing FrameRenderer
    settings = config.get_renderer_settings(title="PREVIEW", override_res=(1280, 720))
    sample_bars = np.sin(np.linspace(0, np.pi, config.num_bars)) * 0.75 + 0.1
    
    renderer = FrameRenderer(settings)
    bgr_frame = renderer.renderFrame(sample_bars)
    
    # Encode BGR numpy array directly to JPEG bytes for the HTTP response
    _, buffer = cv2.imencode('.jpg', bgr_frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")