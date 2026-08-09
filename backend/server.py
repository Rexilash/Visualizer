import os
import cv2
import numpy as np
import threading
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from render_config import RenderConfig
from frame_renderer import FrameRenderer
from video_engine import VideoEngine

app = FastAPI(title="Visualizer Engine API")

# Allow CORS requests from Flutter Desktop / Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# GLOBAL STATE
# -------------------------------------------------------------
config = RenderConfig()

render_state = {
    "is_rendering": False,
    "progress": 0,
    "total_frames": 0,
    "status_message": "Idle",
    "output_path": ""
}

# -------------------------------------------------------------
# PYDANTIC SCHEMAS
# -------------------------------------------------------------
class ConfigUpdateRequest(BaseModel):
    res_key: str = "FHD (1920x1080)"
    num_bars: int = 64
    rgb_primary: List[int] = [255, 0, 150]
    rgb_secondary: List[int] = [0, 255, 255]
    rgb_tertiary: List[int] = [0, 100, 255]
    rgb_bg: List[int] = [15, 15, 20]

class RenderStartRequest(BaseModel):
    audio_path: str

# -------------------------------------------------------------
# API ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/config")
def get_config():
    """Returns the current render configuration."""
    return {
        "selected_res_key": config.selected_res_key,
        "num_bars": config.num_bars,
        "rgb_primary": config.rgb_primary,
        "rgb_secondary": config.rgb_secondary,
        "rgb_tertiary": config.rgb_tertiary,
        "rgb_bg": config.rgb_bg,
        "available_resolutions": list(config.res_options.keys())
    }


@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    """Updates render settings and color schemes."""
    if req.res_key in config.res_options:
        config.selected_res_key = req.res_key
    config.num_bars = req.num_bars
    config.rgb_primary = tuple(req.rgb_primary)
    config.rgb_secondary = tuple(req.rgb_secondary)
    config.rgb_tertiary = tuple(req.rgb_tertiary)
    config.rgb_bg = tuple(req.rgb_bg)
    
    return {"status": "updated"}


@app.get("/api/preview")
def get_preview():
    """Generates a single JPEG preview frame based on the current configuration."""
    settings = config.get_renderer_settings(title="PREVIEW MODE", override_res=(1280, 720))
    
    # Generate synthetic spectrum data for preview canvas
    sample_bars = np.sin(np.linspace(0, np.pi, config.num_bars)) * 0.75 + 0.1
    
    renderer = FrameRenderer(settings)
    bgr_frame = renderer.renderFrame(sample_bars)
    
    # Encode BGR numpy array directly into JPEG bytes
    success, buffer = cv2.imencode('.jpg', bgr_frame)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode preview frame")
        
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@app.post("/api/render/start")
def start_render(req: RenderStartRequest):
    """Spawns video processing in a background thread."""
    if render_state["is_rendering"]:
        raise HTTPException(status_code=400, detail="Rendering is already in progress.")
        
    if not os.path.exists(req.audio_path):
        raise HTTPException(status_code=404, detail=f"Audio file not found: {req.audio_path}")

    # Reset State
    render_state["is_rendering"] = True
    render_state["progress"] = 0
    render_state["total_frames"] = 0
    render_state["status_message"] = "Initializing engine..."

    def _progress_callback(current, total):
        render_state["progress"] = current
        render_state["total_frames"] = total

    def _status_callback(msg):
        render_state["status_message"] = msg

    def _worker():
        engine = VideoEngine(
            audio_path=req.audio_path,
            config=config,
            progress_callback=_progress_callback,
            status_callback=_status_callback
        )
        try:
            engine.render()
            render_state["output_path"] = engine.output_mp4_path
        except Exception as e:
            render_state["status_message"] = f"Error: {str(e)}"
        finally:
            render_state["is_rendering"] = False

    threading.Thread(target=_worker, daemon=True).start()
    return {"status": "started"}


@app.get("/api/render/status")
def get_render_status():
    """Polled by Flutter to track rendering progress."""
    return render_state