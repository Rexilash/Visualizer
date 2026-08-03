import os
import cv2
import subprocess
import numpy as np                          # Added missing NumPy import
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageTk             # Added missing PIL import

from backend.audio_analyzer import AudioAnalyzer
from backend.frame_renderer import FrameRenderer


class VideoWriter:
    def __init__(self, window):
        self.window = window
        self.window.title("Visualizer")
        # Landscape geometry fits side-by-side panels better than 800x800
        self.window.geometry("960x480")
        self.window.resizable(False, False)
        
        self.selectedWavPath = ""

        # Default RGB colors
        self.rgbPrimary = (255, 0, 150)
        self.rgbSecondary = (0, 255, 255)
        self.rgbTertiary = (0, 100, 255)
        self.rgbBg = (15, 15, 20)

        # Main Container
        mainContainer = tk.Frame(window)
        mainContainer.pack(fill="both", expand=True, padx=15, pady=15)

        # Left Column (Controls)
        leftPanel = tk.Frame(mainContainer, width=420)
        leftPanel.pack(side="left", fill="y", padx=(0, 15))

        # Right Column (Preview)
        rightPanel = tk.LabelFrame(mainContainer, text=" Live Preview ", padx=10, pady=10)
        rightPanel.pack(side="right", fill="both", expand=True)

        # -------------------------------------------------------------
        # LEFT PANEL WIDGETS
        # -------------------------------------------------------------
        titleLbl = tk.Label(leftPanel, text="Config", font=("Helvetica", 14, "bold"))
        titleLbl.pack(anchor="w", pady=(0, 5))

        # Attached configFrame to leftPanel instead of window
        configFrame = tk.LabelFrame(leftPanel, text=" Render Settings ", padx=10, pady=10)
        configFrame.pack(fill="x", pady=5)

        # Resolutions (Explicit Grid Coordinates)
        tk.Label(configFrame, text="Resolution (16:9)").grid(row=0, column=0, sticky="w", pady=5)
        self.resOptions = {
            "HD (1280x720)": (1280, 720),
            "FHD (1920x1080)": (1920, 1080),
            "QHD (2560x1440)": (2560, 1440),
            "4K Ultra HD (3840x2160)": (3840, 2160)
        }
        self.resCombo = ttk.Combobox(configFrame, values=list(self.resOptions.keys()), state="readonly", width=20)
        self.resCombo.set("FHD (1920x1080)")
        self.resCombo.grid(row=0, column=1, padx=5, pady=5)
        self.resCombo.bind("<<ComboboxSelected>>", lambda e: self.updatePreview())

        # Bar Count Selector (Explicit Grid Coordinates)
        tk.Label(configFrame, text="Number of Audio Bars:").grid(row=1, column=0, sticky="w", pady=5)
        self.barsSpinner = ttk.Spinbox(
            configFrame, from_=16, to=256, increment=16, width=18, 
            command=self.updatePreview
        )
        self.barsSpinner.set(64)
        self.barsSpinner.grid(row=1, column=1, padx=5, pady=5)
        self.barsSpinner.bind("<KeyRelease>", lambda e: self.updatePreview())

        # Color Customization (Explicit Grid Coordinates)
        tk.Label(configFrame, text="Theme Color Scheming:").grid(row=2, column=0, sticky="w", pady=5)
        colorBtnPanel = tk.Frame(configFrame)
        colorBtnPanel.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.btnPrimary = tk.Button(colorBtnPanel, text="Primary", width=6, command=lambda: self.pickColor("primary"))
        self.btnPrimary.pack(side="left", padx=1)

        self.btnSecondary = tk.Button(colorBtnPanel, text="Secondary", width=6, command=lambda: self.pickColor("secondary"))
        self.btnSecondary.pack(side="left", padx=1)

        self.btnTertiary = tk.Button(colorBtnPanel, text="Tertiary", width=6, command=lambda: self.pickColor("tertiary"))
        self.btnTertiary.pack(side="left", padx=1)

        self.btnBg = tk.Button(colorBtnPanel, text="BG", width=4, command=lambda: self.pickColor("background"))
        self.btnBg.pack(side="left", padx=1)

        # File Chooser attached to leftPanel
        browseBtn = tk.Button(leftPanel, text="Select Audio/Video File", command=self.browseFile, width=28)
        browseBtn.pack(pady=(15, 5))

        self.fileStatusLbl = tk.Label(leftPanel, text="No Audio File Selected", fg="gray", wraplength=350)
        self.fileStatusLbl.pack(pady=2)

        # Progress Bar attached to leftPanel
        self.progressBar = ttk.Progressbar(leftPanel, orient="horizontal", length=350, mode="determinate")
        self.progressBar.pack(pady=10)

        # Render Button attached to leftPanel
        self.generateBtn = tk.Button(
            leftPanel, text="Generate", command=self.processVideo, 
            state="disabled", width=22, bg="#2196F3", fg="white", font=("Helvetica", 10, "bold")
        )
        self.generateBtn.pack(pady=5)

        # -------------------------------------------------------------
        # RIGHT PANEL WIDGETS
        # -------------------------------------------------------------
        self.previewCanvas = tk.Label(rightPanel, bg="black")
        self.previewCanvas.pack(fill="both", expand=True)

        self.updatePreview()

    def updatePreview(self):
        try:
            configuredBars = int(self.barsSpinner.get())
        except ValueError:
            configuredBars = 64

        bgrPrimary = (int(self.rgbPrimary[2]), int(self.rgbPrimary[1]), int(self.rgbPrimary[0]))
        bgrSecondary = (int(self.rgbSecondary[2]), int(self.rgbSecondary[1]), int(self.rgbSecondary[0]))
        bgrTertiary = (int(self.rgbTertiary[2]), int(self.rgbTertiary[1]), int(self.rgbTertiary[0]))
        bgrBg = (int(self.rgbBg[2]), int(self.rgbBg[1]), int(self.rgbBg[0]))

        settings = {
            "resolution": (1280, 720),
            "bgColor": bgrBg,
            "title": "PREVIEW MODE",
            "titleColor": (255, 255, 255),
            "artist": "Sample Audio Spectrum",
            "artistColor": (180, 180, 180),
            "primaryColor": bgrPrimary,
            "secondaryColor": bgrSecondary,
            "tertiaryColor": bgrTertiary,
            "borderWidth": 10,
            "borderColor1": (30, 30, 30),
            "borderColor2": bgrPrimary,
            "barGap": 4,
            "maxHeightPct": 0.5
        }

        sampleBars = np.sin(np.linspace(0, np.pi, configuredBars)) * 0.75 + 0.1
        
        renderer = FrameRenderer(settings)
        bgrFrame = renderer.renderFrame(sampleBars)

        rgbFrame = cv2.cvtColor(bgrFrame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgbFrame)
        img = img.resize((480, 270), Image.Resampling.LANCZOS)
        
        tkImg = ImageTk.PhotoImage(image=img)
        self.previewCanvas.config(image=tkImg)
        self.previewCanvas.image = tkImg

    def pickColor(self, target):
        colorInfo = colorchooser.askcolor(title=f"Choose {target.capitalize()} Color")
        if colorInfo[1]:
            hexColor = colorInfo[1]
            rgbTuple = colorInfo[0]

            brightness = (rgbTuple[0] * 299 + rgbTuple[1] * 587 + rgbTuple[2] * 114) / 1000
            textColor = "black" if brightness > 125 else "white"

            if target == "primary":
                self.rgbPrimary = rgbTuple
                self.btnPrimary.config(bg=hexColor, fg=textColor)
            elif target == "secondary":
                self.rgbSecondary = rgbTuple
                self.btnSecondary.config(bg=hexColor, fg=textColor)
            elif target == "tertiary":
                self.rgbTertiary = rgbTuple
                self.btnTertiary.config(bg=hexColor, fg=textColor)
            elif target == "background":
                self.rgbBg = rgbTuple
                self.btnBg.config(bg=hexColor, fg=textColor)

            self.updatePreview()

    def browseFile(self):
        mediaFilters = [
            ("All Supported Media", "*.mp3 *.wav *.m4a *.flac *.aac *.mp4 *.mkv *.mov"),
            ("Audio Tracks", "*.mp3 *.wav *.m4a *.flac *.aac"),
            ("Video Files", "*.mp4 *.mkv *.mov")
        ]
        filePath = filedialog.askopenfilename(title="Select Audio File", filetypes=mediaFilters)
        if filePath:
            self.selectedWavPath = filePath
            filename = os.path.basename(filePath)
            self.fileStatusLbl.config(text=f"Loaded: {filename}", fg="black")
            self.generateBtn.config(state="normal")

    def processVideo(self):
        self.generateBtn.config(state="disabled")
        self.window.update()

        chosenResKey = self.resCombo.get()
        resolutionTuple = self.resOptions[chosenResKey]
        configuredBars = int(self.barsSpinner.get())

        bgrPrimary = (int(self.rgbPrimary[2]), int(self.rgbPrimary[1]), int(self.rgbPrimary[0]))
        bgrSecondary = (int(self.rgbSecondary[2]), int(self.rgbSecondary[1]), int(self.rgbSecondary[0]))
        bgrTertiary = (int(self.rgbTertiary[2]), int(self.rgbTertiary[1]), int(self.rgbTertiary[0]))
        bgrBg = (int(self.rgbBg[2]), int(self.rgbBg[1]), int(self.rgbBg[0]))

        settings = {
            "resolution": resolutionTuple,
            "bgColor": bgrBg,
            "title": "DYNAMIC THEME RENDER",
            "titleColor": (255, 255, 255),
            "artist": "Engine v2 Configured",
            "artistColor": (180, 180, 180),
            "primaryColor": bgrPrimary,
            "secondaryColor": bgrSecondary,
            "tertiaryColor": bgrTertiary,
            "borderWidth": 10,
            "borderColor1": (30, 30, 30),
            "borderColor2": bgrPrimary,
            "barGap": 4,
            "maxHeightPct": 0.5
        }

        width, height = settings["resolution"]
        tempSilentVideo = "tempSilentRender.mp4"
        tempConvertedWav = "tempBackgroundDecode.wav"
        outputMp4Path = "completedRender.mp4"

        analysisAudioPath = self.selectedWavPath
        videoWriter = None

        try:
            if not self.selectedWavPath.lower().endswith((".wav", ".wave")):
                self.fileStatusLbl.config(text="Unpacking audio streams...")
                self.window.update()

                convertCmd = ["ffmpeg", "-y", "-i", self.selectedWavPath, tempConvertedWav]
                subprocess.run(convertCmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                analysisAudioPath = tempConvertedWav

            self.fileStatusLbl.config(text="Rendering frames...")
            self.window.update()

            audio = AudioAnalyzer(analysisAudioPath, targetFPS=60, numBars=configuredBars)
            renderer = FrameRenderer(settings)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            videoWriter = cv2.VideoWriter(tempSilentVideo, fourcc, float(audio.fps), (width, height))

            self.progressBar["maximum"] = audio.totalFrames

            for frameIdx in range(audio.totalFrames):
                barData = audio.getFrameData(frameIdx)
                completedFrame = renderer.renderFrame(barData)
                videoWriter.write(completedFrame)

                if frameIdx % 15 == 0:
                    self.progressBar["value"] = frameIdx
                    self.window.update()
            
            videoWriter.release()
            videoWriter = None

            ffmpegCmd = ["ffmpeg", "-y", "-i", tempSilentVideo, "-i", analysisAudioPath, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", outputMp4Path]
            subprocess.run(ffmpegCmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            filename = os.path.basename(self.selectedWavPath)
            self.fileStatusLbl.config(text=f"Completed: {filename}", fg="green")
            messagebox.showinfo("Success", f"Video rendered and mixed successfully!\nSaved as: {outputMp4Path}")
        
        except FileNotFoundError:
            messagebox.showwarning("FFmpeg missing", "Silent video master saved to folder.\nInstall FFmpeg to support automatic audio merging.")
        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong: {str(e)}")
        finally:
            if videoWriter is not None and videoWriter.isOpened():
                videoWriter.release()
            if os.path.exists(tempSilentVideo):
                os.remove(tempSilentVideo)
            if os.path.exists(tempConvertedWav):
                os.remove(tempConvertedWav)
            self.progressBar["value"] = 0
            self.generateBtn.config(state="normal")