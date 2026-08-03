import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser

from backend.render_config import RenderConfig
from backend.preview_panel import PreviewPanel
from backend.video_engine import VideoEngine


class VisualizerApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Visualizer Studio")
        self.window.geometry("960x520")
        self.window.resizable(False, False)

        self.config = RenderConfig()
        self.selected_file_path = ""
        
        # Enable Dark Mode by Default
        self.is_dark_mode = True

        # Theme Color Palette Definitions
        self.themes = {
            "dark": {
                "bg": "#181818",
                "card": "#242424",
                "fg": "#FFFFFF",
                "subtext": "#AAAAAA",
                "btn_bg": "#333333",
                "btn_fg": "#FFFFFF",
                "accent": "#2196F3"
            },
            "light": {
                "bg": "#F5F5F5",
                "card": "#FFFFFF",
                "fg": "#000000",
                "subtext": "#555555",
                "btn_bg": "#E0E0E0",
                "btn_fg": "#000000",
                "accent": "#2196F3"
            }
        }

        # Initialize TTK Styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Allows custom color overrides on TTK widgets

        # -------------------------------------------------------------
        # MAIN CONTAINERS
        # -------------------------------------------------------------
        self.main_container = tk.Frame(window)
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        self.left_panel = tk.Frame(self.main_container, width=420)
        self.left_panel.pack(side="left", fill="y", padx=(0, 15))

        # Preview Panel Component
        self.preview_panel = PreviewPanel(self.main_container)

        # -------------------------------------------------------------
        # LEFT PANEL CONTROLS
        # -------------------------------------------------------------
        # Header Frame (Title + Dark Mode Toggle)
        header_frame = tk.Frame(self.left_panel)
        header_frame.pack(fill="x", pady=(0, 5))

        self.title_lbl = tk.Label(header_frame, text="Config", font=("Helvetica", 14, "bold"))
        self.title_lbl.pack(side="left")

        self.theme_toggle_btn = tk.Button(
            header_frame, text="🌙 Dark", font=("Helvetica", 9),
            command=self._toggle_theme, relief="flat", padx=8
        )
        self.theme_toggle_btn.pack(side="right")

        # Config Panel Frame
        self.config_frame = ttk.LabelFrame(self.left_panel, text=" Render Settings ", padding=10)
        self.config_frame.pack(fill="x", pady=5)

        # Resolutions
        self.res_lbl = tk.Label(self.config_frame, text="Resolution (16:9)")
        self.res_lbl.grid(row=0, column=0, sticky="w", pady=5)

        self.res_combo = ttk.Combobox(self.config_frame, values=list(self.config.res_options.keys()), state="readonly", width=20)
        self.res_combo.set(self.config.selected_res_key)
        self.res_combo.grid(row=0, column=1, padx=5, pady=5)
        self.res_combo.bind("<<ComboboxSelected>>", self._on_res_changed)

        # Audio Bars
        self.bars_lbl = tk.Label(self.config_frame, text="Number of Audio Bars:")
        self.bars_lbl.grid(row=1, column=0, sticky="w", pady=5)

        self.bars_spinner = ttk.Spinbox(self.config_frame, from_=16, to=256, increment=16, width=18, command=self._on_bars_changed)
        self.bars_spinner.set(self.config.num_bars)
        self.bars_spinner.grid(row=1, column=1, padx=5, pady=5)
        self.bars_spinner.bind("<KeyRelease>", self._on_bars_changed)

        # Theme Colors
        self.color_scheme_lbl = tk.Label(self.config_frame, text="Theme Color Scheming:")
        self.color_scheme_lbl.grid(row=2, column=0, sticky="w", pady=5)

        self.color_btn_panel = tk.Frame(self.config_frame)
        self.color_btn_panel.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.btn_primary = tk.Button(self.color_btn_panel, text="Primary", width=6, command=lambda: self._pick_color("primary"))
        self.btn_primary.pack(side="left", padx=1)

        self.btn_secondary = tk.Button(self.color_btn_panel, text="Secondary", width=6, command=lambda: self._pick_color("secondary"))
        self.btn_secondary.pack(side="left", padx=1)

        self.btn_tertiary = tk.Button(self.color_btn_panel, text="Tertiary", width=6, command=lambda: self._pick_color("tertiary"))
        self.btn_tertiary.pack(side="left", padx=1)

        self.btn_bg = tk.Button(self.color_btn_panel, text="BG", width=4, command=lambda: self._pick_color("background"))
        self.btn_bg.pack(side="left", padx=1)

        # File Chooser & Status
        self.browse_btn = tk.Button(self.left_panel, text="Select Audio/Video File", command=self._browse_file, width=28)
        self.browse_btn.pack(pady=(15, 5))

        self.file_status_lbl = tk.Label(self.left_panel, text="No Audio File Selected", wraplength=350)
        self.file_status_lbl.pack(pady=2)

        # Progress Bar & Render Button
        self.progress_bar = ttk.Progressbar(self.left_panel, orient="horizontal", length=350, mode="determinate")
        self.progress_bar.pack(pady=10)

        self.generate_btn = tk.Button(
            self.left_panel, text="Generate", command=self._start_render_thread, 
            state="disabled", width=22, font=("Helvetica", 10, "bold")
        )
        self.generate_btn.pack(pady=5)

        # Apply Theme & Draw Initial Preview Frame
        self._apply_theme()
        self.preview_panel.refresh(self.config)

    # -------------------------------------------------------------
    # THEME MANAGEMENT
    # -------------------------------------------------------------
    def _toggle_theme(self):
        """Switches between dark and light themes."""
        self.is_dark_mode = not self.is_dark_mode
        self._apply_theme()

    def _apply_theme(self):
        """Applies current dark/light colors to all Tkinter and TTK widgets."""
        colors = self.themes["dark"] if self.is_dark_mode else self.themes["light"]

        # 1. Update Window & Main Frame Backgrounds
        self.window.config(bg=colors["bg"])
        self.main_container.config(bg=colors["bg"])
        self.left_panel.config(bg=colors["bg"])
        self.color_btn_panel.config(bg=colors["card"])

        # 2. Update Labels
        self.title_lbl.config(bg=colors["bg"], fg=colors["fg"])
        self.res_lbl.config(bg=colors["card"], fg=colors["fg"])
        self.bars_lbl.config(bg=colors["card"], fg=colors["fg"])
        self.color_scheme_lbl.config(bg=colors["card"], fg=colors["fg"])
        self.file_status_lbl.config(bg=colors["bg"], fg=colors["subtext"])

        # 3. Update Control Buttons
        self.browse_btn.config(bg=colors["btn_bg"], fg=colors["btn_fg"], activebackground=colors["card"])
        self.theme_toggle_btn.config(
            text="🌙 Dark Mode" if self.is_dark_mode else "☀️ Light Mode",
            bg=colors["btn_bg"], fg=colors["btn_fg"]
        )
        self.generate_btn.config(bg=colors["accent"], fg="#FFFFFF", activebackground="#1976D2")

        # 4. Configure TTK Styles (LabelFrames, Combobox, Spinbox, Progressbar)
        self.style.configure("TLabelframe", background=colors["card"], foreground=colors["fg"])
        self.style.configure("TLabelframe.Label", background=colors["card"], foreground=colors["fg"], font=("Helvetica", 9, "bold"))
        self.style.configure("TCombobox", fieldbackground=colors["bg"], background=colors["btn_bg"], foreground=colors["fg"])
        self.style.configure("TSpinbox", fieldbackground=colors["bg"], background=colors["btn_bg"], foreground=colors["fg"])
        self.style.configure("Horizontal.TProgressbar", troughcolor=colors["bg"], background=colors["accent"])

    # -------------------------------------------------------------
    # EVENT HANDLERS
    # -------------------------------------------------------------
    def _on_res_changed(self, event=None):
        self.config.selected_res_key = self.res_combo.get()
        self.preview_panel.refresh(self.config)

    def _on_bars_changed(self, event=None):
        try:
            self.config.num_bars = int(self.bars_spinner.get())
            self.preview_panel.refresh(self.config)
        except ValueError:
            pass

    def _pick_color(self, target):
        color_info = colorchooser.askcolor(title=f"Choose {target.capitalize()} Color")
        if color_info[1]:
            hex_color, rgb_tuple = color_info[1], color_info[0]
            brightness = (rgb_tuple[0] * 299 + rgb_tuple[1] * 587 + rgb_tuple[2] * 114) / 1000
            text_color = "black" if brightness > 125 else "white"

            if target == "primary":
                self.config.rgb_primary = rgb_tuple
                self.btn_primary.config(bg=hex_color, fg=text_color)
            elif target == "secondary":
                self.config.rgb_secondary = rgb_tuple
                self.btn_secondary.config(bg=hex_color, fg=text_color)
            elif target == "tertiary":
                self.config.rgb_tertiary = rgb_tuple
                self.btn_tertiary.config(bg=hex_color, fg=text_color)
            elif target == "background":
                self.config.rgb_bg = rgb_tuple
                self.btn_bg.config(bg=hex_color, fg=text_color)

            self.preview_panel.refresh(self.config)

    def _browse_file(self):
        filters = [("All Supported Media", "*.mp3 *.wav *.m4a *.flac *.aac *.mp4 *.mkv *.mov")]
        file_path = filedialog.askopenfilename(title="Select Audio File", filetypes=filters)
        if file_path:
            self.selected_file_path = file_path
            filename = os.path.basename(file_path)
            self.file_status_lbl.config(text=f"Loaded: {filename}")
            self.generate_btn.config(state="normal")

    def _start_render_thread(self):
        """Dispatches video processing to a background thread to keep UI smooth."""
        self.generate_btn.config(state="disabled")
        threading.Thread(target=self._run_render_pipeline, daemon=True).start()

    def _run_render_pipeline(self):
        engine = VideoEngine(
            audio_path=self.selected_file_path,
            config=self.config,
            progress_callback=self._update_progress_ui,
            status_callback=self._update_status_ui
        )
        try:
            if engine.render():
                messagebox.showinfo("Success", f"Video rendered successfully!\nSaved as: {engine.output_mp4_path}")
        except FileNotFoundError:
            messagebox.showwarning("FFmpeg Missing", "Install FFmpeg to support automatic audio merging.")
        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong: {str(e)}")
        finally:
            self.progress_bar["value"] = 0
            self.generate_btn.config(state="normal")

    def _update_progress_ui(self, current, total):
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current

    def _update_status_ui(self, text):
        self.file_status_lbl.config(text=text)