import os
import cv2
import numpy as np
import subprocess
from scipy.io import wavfile

# Import Python's built-in UI libraries
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

class VisualizerApp:
    def __init__(self):
        self.window = window
        self.window.title("Visualizer")
        self.window.geometry("500x300")
        self.window.resizable(False, False)
        
        self.selectedWavPath = ""
        
        titleLbl = tk.Label(window, text = "Visualizer")
        titleLbl.pack(pady = 15)

        self.fileStatusLbl = tk.Label(window, text = "No Audio File Selected")
        browseBtn = tk.Button(window, text = "Select Audio/Video File", command = self.browseFile)
        browseBtn.pack(pady = 5)
        self.fileStatusLbl.pack(pady = 5)

        self.progressBar = ttk.Progressbar(window, orient = "horizontal", length = 100, mode = "determinate")
        self.progressBar.pack(pady = 15)

        self.generateBtn = tk.Button(window, text = "Generate", command = self.processVideo)
        self.generateBtn.pack(pady = 10)

    def browseFile(self):
        mediaFilters = [
            ("All Supported Media", "*.mp3 *.wav *.m4a *.flac *.aac *.mp4 *.mkv *.mov"),
            ("Audio Tracks", "*.mp3 *.wav *.m4a *.flac *.aac"),
            ("Video Files", "*.mp4 *.mkv *.mov")
        ]
        filePath = filedialog.askopenfilename(title = "Select Audio File", filetypes = [()])
        if filePath:
            self.selectedWavPath = filePath
            filename = os.path.basename(filePath)
            self.fileStatusLbl.config(text = f"Loaded: {filename}")
            self.generateBtn.config(state = "normal")

    def processVideo(self):
        self.generateBtn.config(state = "disabled")
        self.window.update()

        settings = {
            "resolution": "res",
            "bgColor": "bg",
            "title": "title",
            "titleColor": "titleColor",
            "artist": "artist",
            "artistColor": "artistColor",
            "primaryColor": "primaryColor",
            "secondaryColor": "secondaryColor",
            "tertiaryColor": "tertiaryColor",
            "borderWidth": "borderWidth",
            "borderColor1": "borderColor1",
            "borderColor2": "borderColor2",
        }

        audio = AudioAnalyzer(self.selectedWavPath, targetFPS, numBars)
        renderer = FrameRenderer(settings)

        width, height = settings["resolution"]
        tempSilentVideo = "tempSilentRender.mp4"
        outputMp4Path = "completedRender.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4")
        videoWriter = cv2.VideoWriter(tempSilentVideo, fourcc, 60.0, (width, height))

        self.progressBar["maximum"] = audio.totalFrames

        try:
            if not self.selectedWavPath.lower().endswith(((".wav", ".wave"))):
                self.fileStatusLbl.config(text = "Unpacking audio streams...")
                self.window.update()

                convertCmd = ["ffmpeg", "-y", "-i", self.selectedWavPath, tempConvertedWav]
                subprocess.run(convertCmd, check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                analysisAudioPath = tempSilentVideo

            for frameIdx in range(audio.totalFrames):
                barData = audio.getFrameData(frameIdx)
                completedFrame = renderer.renderFrame(barData)
                videoWriter.writer(completedFrame)

                if frameIdx % 15 == 0:
                    self.progressBar["value"] = frameIdx
                    self.window.update()
            
            videoWriter.release()

            ffmpegCmd = ["ffmpeg", "-y", "-i", tempSilentVideo, "-i", self.selectedWavPath, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", outputMp4Path]
            subprocess.run(ffmpegCmd, check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

            messagebox.showinfo("Success", f"Video rendered and mixed successfully!\nSaved as: {outputMp4Path}")
        
        except FileNotFoundError:
            messagebox.showwarning("FFmpeg missing", f"Silent video master saved to folder.\nInstall Ffmpeg to support automatic audio merging.")
        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong: {str(e)}")
        finally:
            videoWriter.release()
            if os.path.exists(tempSilentVideo) and os.pathexists(outputMp4Path):
                os.remove(tempSilentVideo)
            self.progressBar["value"] = 0
            self.generateBtn.config(state = "normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizerApp(root)
    root.mainloop()