import argparse
import json
import os
import sys
import cv2
import numpy as np
import base64

from render_config import RenderConfig
from frame_renderer import FrameRenderer
from video_engine import VideoEngine


def parse_config(json_str: str) -> RenderConfig:
    config = RenderConfig()
    if not json_str:
        return config

    try:
        # Decode base64 first, with fallback to raw JSON string parsing
        try:
            decoded_bytes = base64.b64decode(json_str)
            data = json.loads(decoded_bytes.decode('utf-8'))
        except Exception:
            data = json.loads(json_str)
            
        if "res_key" in data and data["res_key"] in config.res_options:
            config.selected_res_key = data["res_key"]
        if "num_bars" in data:
            config.num_bars = int(data["num_bars"])
        if "title" in data:
            config.title = data["title"]
        if "artist" in data:
            config.artist = data["artist"]
        if "bg_mode" in data:
            config.bg_mode = data["bg_mode"]
        if "bg_image_path" in data:
            config.bg_image_path = data["bg_image_path"] or ""
        if "rgb_primary" in data:
            config.rgb_primary = tuple(data["rgb_primary"])
        if "rgb_secondary" in data:
            config.rgb_secondary = tuple(data["rgb_secondary"])
        if "rgb_tertiary" in data:
            config.rgb_tertiary = tuple(data["rgb_tertiary"])
        if "rgb_bg" in data:
            config.rgb_bg = tuple(data["rgb_bg"])
    except Exception as e:
        print(f"Config parse error: {e}", file=sys.stderr)

    return config


def generate_preview(config: RenderConfig, output_path: str):
    settings = config.get_renderer_settings(override_res=(1280, 720))
    sample_bars = np.sin(np.linspace(0, np.pi, config.num_bars)) * 0.9 + 0.1
    renderer = FrameRenderer(settings)
    bgr_frame = renderer.renderFrame(sample_bars, progress=0.45)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cv2.imwrite(output_path, bgr_frame)
    print(f"PREVIEW_READY:{output_path}", flush=True)


def execute_render(config: RenderConfig, audio_path: str, output_path: str):
    def progress_cb(current, total):
        print(f"PROGRESS:{current}:{total}", flush=True)

    def status_cb(msg):
        print(f"STATUS:{msg}", flush=True)

    engine = VideoEngine(
        audio_path=audio_path,
        config=config,
        progress_callback=progress_cb,
        status_callback=status_cb,
        output_path=output_path
    )
    engine.render()
    print(f"RENDER_COMPLETE:{output_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Spectrum Visualizer CLI Engine")
    parser.add_argument("--mode", choices=["preview", "render"], required=True)
    parser.add_argument("--config", type=str, default="")
    parser.add_argument("--audio", type=str, default="")
    parser.add_argument("--output", type=str, required=True)

    args = parser.parse_args()
    
    try:
        config = parse_config(args.config)

        if args.mode == "preview":
            generate_preview(config, args.output)
        elif args.mode == "render":
            if not args.audio:
                print("Error: --audio argument required for render mode", file=sys.stderr)
                sys.exit(1)
            execute_render(config, args.audio, args.output)
    except Exception as e:
        import traceback
        print("\n=== BACKEND CRASH TRACEBACK ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("===============================\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()