import os
import cv2
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from AudioAnalyzer import AudioAnalyzer
from FrameRenderer import FrameRenderer

class VideoWriter:
    def __init__(self, window):
        self.window = window
        self.window.title("Visualizer")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        
        self.selectedWavPath = ""

        # Default RGB colors
        self.rgbPrimary = (255, 0, 150)
        self.rgbSecondary = (0, 255, 255)
        self.rgbTertiary = (0, 100, 255)
        self.rgbBg = (0, 0, 0)
        
        titleLbl = tk.Label(window, text = "Visualizer")
        titleLbl.pack(pady = 15)

        # Settings Panel
        configFrame = tk.LabelFrame(window, text = "Render Settings")
        configFrame.pack()

        # Resolutions
        tk.Label(configFrame,  text = "Resolution (16:9)")
        self.resOptions = {
            "HD (1280x720)": (1280, 720),
            "FHD (1920x1080)": (1920, 1080),
            "QHD (2560x1440)": (2560, 1440),
            "4K Ultra HD (3840x2160)": (3840, 2160)
        }
        self.resCombo = ttk.Combobox(configFrame, value = list(self.resOptions.keys()), state = "readonly")
        self.resCombo.set("FHD (1920x1080)")
        self.resCombo.grid()

        # Bar count selector
        tk.Label(configFrame, text = "Number of Audio Bars:").grid()
        self.barsSpinner = ttk.Spinbox(configFrame)
        self.barsSpinner.set(64)
        self.barsSpinner.grid()

        # Color customization
        tk.Label(configFrame, text = "Theme Color Scheming:").grid()
        colorBtnPanel = tk.Frame(configFrame)
        colorBtnPanel.grid()

        self.btnPrimary = tk.Button(colorBtnPanel, text = "Primary", command = lambda: self.pickColor("primary"))
        self.btnPrimary.pack()

        self.btnSecondary = tk.Button(colorBtnPanel, text = "Secondary", command = lambda: self.pickColor("secondary"))
        self.btnSecondary.pack()

        self.btnTertiary = tk.Button(colorBtnPanel, text = "Tertiary", command = lambda: self.pickColor("tertiary"))
        self.btnTertiary.pack()

        self.btnBg = tk.Button(colorBtnPanel, text = "Background", command = lambda: self.pickColor("background"))
        self.btnBg.pack()

        # File chooser
        browseBtn = tk.Button(window, text = "Select Audio/Video File", command = self.browseFile)
        browseBtn.pack(pady = 5)

        self.fileStatusLbl = tk.Label(window, text = "No Audio File Selected")
        self.fileStatusLbl.pack(pady = 5)

        # Progress bar
        self.progressBar = ttk.Progressbar(window, orient = "horizontal", length = 100, mode = "determinate")
        self.progressBar.pack(pady = 15)

        # Render button
        self.generateBtn = tk.Button(window, text = "Generate", command = self.processVideo)
        self.generateBtn.pack(pady = 10)

    def pickColor(self, target):
        colorInfo = colorchooser.askcolor(title = f"Choose {target.capitalize()} Color")
        if colorInfo[1]:
            hexColor = colorInfo[1]
            rgbTuple = colorInfo[0]

            brightness = (rgbTuple[0] * 299 +rgbTuple[1] * 587 + rgbTuple[2] * 114) / 1000
            textColor = "black" if brightness > 125 else "white"

            if target == "primary":
                self.rgbPrimary = rgbTuple
                self.btnPrimary.config(bg = hexColor, fg = textColor)
            elif target == "secondary":
                self.rgbSecondary = rgbTuple
                self.btnSecondary.config(bg = hexColor, fg = textColor)
            elif target == "tertiary":
                self.rgbTertiary = rgbTuple
                self.btnTertiary.config(bg = hexColor, fg = textColor)
            elif target == "background":
                self.rgbBg = rgbTuple
                self.btnBg.config(bg = hexColor, fg = textColor)

    def browseFile(self):
        mediaFilters = [
            ("All Supported Media", "*.mp3 *.wav *.m4a *.flac *.aac *.mp4 *.mkv *.mov"),
            ("Audio Tracks", "*.mp3 *.wav *.m4a *.flac *.aac"),
            ("Video Files", "*.mp4 *.mkv *.mov")
        ]
        filePath = filedialog.askopenfilename(title = "Select Audio File", filetypes = mediaFilters)
        if filePath:
            self.selectedWavPath = filePath
            filename = os.path.basename(filePath)
            self.fileStatusLbl.config(text = f"Loaded: {filename}")
            self.generateBtn.config(state = "normal")

    def processVideo(self):
        self.generateBtn.config(state = "disabled")
        self.window.update()

        chosenResKey = self.resCombo.get()
        resolutionTuple = self.resOptions[chosenResKey]
        configuredBars = int(self.barsSpinner.get())

        # Convert RGB to OpenCV BGR
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
                self.fileStatusLbl.config(text = "Unpacking audio streams...")
                self.window.update()

                convertCmd = ["ffmpeg", "-y", "-i", self.selectedWavPath, tempConvertedWav]
                subprocess.run(convertCmd, check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                analysisAudioPath = tempConvertedWav

            self.fileStatusLbl.config(text = "rendering frames...")
            self.window.update()

            audio = AudioAnalyzer(analysisAudioPath, targetFPS = 60, numBars = configuredBars)
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
            subprocess.run(ffmpegCmd, check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

            filename = os.path.basename(self.selectedWavPath)
            self.fileStatusLbl.config(text =  f"Loaded: {filename}", fg =  "green")
            messagebox.showinfo("Success", f"Video rendered and mixed successfully!\nSaved as: {outputMp4Path}")
        
        except FileNotFoundError:
            messagebox.showwarning("FFmpeg missing", f"Silent video master saved to folder.\nInstall Ffmpeg to support automatic audio merging.")
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
            self.generateBtn.config(state = "normal")