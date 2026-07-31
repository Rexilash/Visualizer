class RenderConfig:
    def __init__(self):
        self.res_options = {
            "HD (1280x720)": (1280, 720),
            "FHD (1920x1080)": (1920, 1080),
            "QHD (2560x1440)": (2560, 1440),
            "4K Ultra HD (3840x2160)": (3840, 2160)
        }
        self.selected_res_key = "FHD (1920x1080)"
        self.num_bars = 64
        
        # Color state (RGB)
        self.rgb_primary = (255, 0, 150)
        self.rgb_secondary = (0, 255, 255)
        self.rgb_tertiary = (0, 100, 255)
        self.rgb_bg = (15, 15, 20)

    @property
    def resolution(self):
        return self.res_options[self.selected_res_key]

    def get_renderer_settings(self, title="VISUALIZER RENDER", override_res=None):
        """Converts internal RGB state to OpenCV BGR dict format."""
        bgr_primary = (int(self.rgb_primary[2]), int(self.rgb_primary[1]), int(self.rgb_primary[0]))
        bgr_secondary = (int(self.rgb_secondary[2]), int(self.rgb_secondary[1]), int(self.rgb_secondary[0]))
        bgr_tertiary = (int(self.rgb_tertiary[2]), int(self.rgb_tertiary[1]), int(self.rgb_tertiary[0]))
        bgr_bg = (int(self.rgb_bg[2]), int(self.rgb_bg[1]), int(self.rgb_bg[0]))

        return {
            "resolution": override_res if override_res else self.resolution,
            "bgColor": bgr_bg,
            "title": title,
            "titleColor": (255, 255, 255),
            "artist": "Spectrum Visualizer Engine",
            "artistColor": (180, 180, 180),
            "primaryColor": bgr_primary,
            "secondaryColor": bgr_secondary,
            "tertiaryColor": bgr_tertiary,
            "borderWidth": 10,
            "borderColor1": (30, 30, 30),
            "borderColor2": bgr_primary,
            "barGap": 4,
            "maxHeightPct": 0.5
        }