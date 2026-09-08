# Codebase Context Payload

## File: `frontend/lib/main.dart`
````dart
import 'package:flutter/material.dart';
import 'package:frontend/visualizer_screen.dart';

void main() {
  runApp(const Visualizer());
}

class Visualizer extends StatelessWidget {
  const Visualizer({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: "Visualizer",
      theme: ThemeData.dark(useMaterial3: true),
      home: const VisualizerStudioScreen()
    );
  }
}
````

## File: `frontend/lib/api_service.dart`
````dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';

  /// Cache-busted preview image URL for live streaming update
  static String getPreviewUrl() {
    return '$baseUrl/api/preview?t=${DateTime.now().millisecondsSinceEpoch}';
  }

  static Future<void> updateConfig({
    required String resKey,
    required int numBars,
    required List<int> rgbPrimary,
    required List<int> rgbSecondary,
    required List<int> rgbTertiary,
    required List<int> rgbBg,
  }) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/api/config'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'res_key': resKey,
          'num_bars': numBars,
          'rgb_primary': rgbPrimary,
          'rgb_secondary': rgbSecondary,
          'rgb_tertiary': rgbTertiary,
          'rgb_bg': rgbBg,
        }),
      );
    } catch (_) {}
  }

  static Future<bool> startRender(String audioPath, String outputPath) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/render/start'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'audio_path': audioPath, 'output_path': outputPath}),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<Map<String, dynamic>?> getRenderStatus() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/render/status'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (_) {}
    return null;
  }
}
````

## File: `frontend/lib/visualizer_screen.dart`
````dart
import 'package:flutter/material.dart';
import 'package:flutter/widget_previews.dart';
import '../widgets/config_panel.dart';
import 'widgets/preview.dart';
import 'api_service.dart';
import 'dart:async';
import 'package:file_picker/file_picker.dart';


class VisualizerStudioScreen extends StatefulWidget {
  const VisualizerStudioScreen({super.key});

  @override
  State<VisualizerStudioScreen> createState() => _VisualizerStudioScreenState();
}

class _VisualizerStudioScreenState extends State<VisualizerStudioScreen> {
  // Config State
  String selectedResolution = 'FHD (1920x1080)';
  double barCount = 64;
  String? selectedFilePath;
  bool isRendering = false;
  double renderProgress = 0.0;
  String previewUrl = ApiService.getPreviewUrl();
  Timer? _statusTimer;
  String customFileName = "Visualizer_output";
  String? selectedOutputPath;

  // Colors
  Color primaryColor = const Color(0xFFFF0096);
  Color secondaryColor = const Color(0xFF00FFFF);
  Color tertiaryColor = const Color(0xFF0064FF);
  Color bgColor = const Color(0xFF0F0F14);

  final List<String> resolutionOptions = [
    'HD (1280x720)',
    'FHD (1920x1080)',
    'QHD (2560x1440)',
    '4K Ultra HD (3840x2160)'
  ];

  @override
  void dispose() {
    _statusTimer?.cancel();
    super.dispose();
  }

  void _syncConfigToBackend() {
    ApiService.updateConfig(
      resKey: selectedResolution,
      numBars: barCount.toInt(),
      rgbPrimary: [primaryColor.red, primaryColor.green, primaryColor.blue],
      rgbSecondary: [secondaryColor.red, secondaryColor.green, secondaryColor.blue],
      rgbTertiary: [tertiaryColor.red, tertiaryColor.green, tertiaryColor.blue],
      rgbBg: [bgColor.red, bgColor.green, bgColor.blue],
    ).then((_) {
      setState(() {
        previewUrl = ApiService.getPreviewUrl();
      });
    });
  }

  void _handleColorChange(String label, Color color) {
    setState(() {
      switch (label) {
        case 'Primary':
          primaryColor = color;
          break;
        case 'Secondary':
          secondaryColor = color;
          break;
        case 'Tertiary':
          tertiaryColor = color;
          break;
        case 'BG':
          bgColor = color;
          break;
      }
    });
    _syncConfigToBackend();
  }

  Future<void> _selectSavePath() async {
    String formattedName = customFileName.trim().isEmpty ? 'visualizer_output' : customFileName.trim();
    if (!formattedName.toLowerCase().endsWith('.mp4')) {
      formattedName += '.mp4';
    }

    String? savePath = await FilePicker.saveFile(
      dialogTitle: "Select destination for rendered video",
      fileName: formattedName,
      allowedExtensions: ["mp4"],
      type: FileType.custom,
    );

    if (savePath != null) {
      setState(() {
        selectedOutputPath = savePath;
      });
    }
  }

  Future<void> _toggleRender() async {
    if (isRendering) {
      _statusTimer?.cancel();
      setState(() {
        isRendering = false;
        renderProgress = 0.0;
      });
      return;
    }

    if (selectedFilePath == null) return;

    // Use pre-selected path or prompt if not selected yet
    String? finalPath = selectedOutputPath;

    if (finalPath == null) {
      String formattedName = customFileName.trim().isEmpty ? 'visualizer_output' : customFileName.trim();
      if (!formattedName.toLowerCase().endsWith('.mp4')) {
        formattedName += '.mp4';
      }

      finalPath = await FilePicker.saveFile(
        dialogTitle: "Save rendered video as",
        fileName: formattedName,
        allowedExtensions: ["mp4"],
        type: FileType.custom,
      );

      if (finalPath == null) return; // User cancelled prompt
      setState(() {
        selectedOutputPath = finalPath;
      });
    }

    final started = await ApiService.startRender(selectedFilePath!, finalPath);
    if (started) {
      setState(() {
        isRendering = true;
        renderProgress = 0.0;
      });

      _statusTimer = Timer.periodic(const Duration(milliseconds: 500), (timer) async {
        final status = await ApiService.getRenderStatus();
        if (status != null) {
          final int progress = status['progress'] ?? 0;
          final int total = status['total_frames'] ?? 1;
          final bool active = status['is_rendering'] ?? false;

          setState(() {
            renderProgress = total > 0 ? progress / total : 0.0;
            isRendering = active;
          });

          if (!active) {
            timer.cancel();
          }
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0E),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            SizedBox(
              width: 380,
              child: ConfigPanel(
                selectedResolution: selectedResolution,
                resolutionOptions: resolutionOptions,
                barCount: barCount,
                selectedFilePath: selectedFilePath,
                isRendering: isRendering,
                renderProgress: renderProgress,
                primaryColor: primaryColor,
                secondaryColor: secondaryColor,
                tertiaryColor: tertiaryColor,
                bgColor: bgColor,
                onResolutionChanged: (val) {
                  if (val != null) {
                    setState(() => selectedResolution = val);
                    _syncConfigToBackend();
                  }
                },
                onBarCountChanged: (val) {
                  setState(() => barCount = val);
                  _syncConfigToBackend();
                },
                onColorChanged: _handleColorChange,
                onFileSelected: (path) => setState(() => selectedFilePath = path),
                onToggleRender: _toggleRender,
                outputFileName: customFileName,
                onOutputFileNameChanged: (val) => setState(() => customFileName = val),
                selectedOutputPath: selectedOutputPath,
                onSelectOutputPath: _selectSavePath,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: PreviewPanel(
                bgColor: bgColor,
                previewUrl: previewUrl,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Widget Preview Entrypoint
@Preview(name: 'Visualizer Studio Screen')
Widget visualizerStudioPreview() {
  return MaterialApp(
    theme: ThemeData.dark(useMaterial3: true),
    home: const VisualizerStudioScreen(),
  );
}
````

## File: `frontend/lib/widgets/config_panel.dart`
````dart
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'color_picker_section.dart';

class ConfigPanel extends StatelessWidget {
  final String selectedResolution;
  final List<String> resolutionOptions;
  final double barCount;
  final String? selectedFilePath;
  final bool isRendering;
  final double renderProgress;
  final Color primaryColor;
  final Color secondaryColor;
  final Color tertiaryColor;
  final Color bgColor;
  final String outputFileName;
  final ValueChanged<String> onOutputFileNameChanged;
  final String? selectedOutputPath;

  final ValueChanged<String?> onResolutionChanged;
  final ValueChanged<double> onBarCountChanged;
  final Function(String, Color) onColorChanged;
  final ValueChanged<String?> onFileSelected;
  final VoidCallback onToggleRender;
  final VoidCallback onSelectOutputPath;

  const ConfigPanel({
    super.key,
    required this.selectedResolution,
    required this.resolutionOptions,
    required this.barCount,
    required this.selectedFilePath,
    required this.isRendering,
    required this.renderProgress,
    required this.primaryColor,
    required this.secondaryColor,
    required this.tertiaryColor,
    required this.bgColor,
    required this.onResolutionChanged,
    required this.onBarCountChanged,
    required this.onColorChanged,
    required this.onFileSelected,
    required this.onToggleRender,
    required this.outputFileName,
    required this.onOutputFileNameChanged,
    required this.selectedOutputPath,
    required this.onSelectOutputPath
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Config',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const Divider(height: 24),
            Expanded(
              child: ListView(
                children: [
                  const Text('Resolution (16:9)', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: selectedResolution,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    items: resolutionOptions.map((res) {
                      return DropdownMenuItem(value: res, child: Text(res));
                    }).toList(),
                    onChanged: onResolutionChanged,
                  ),
                  const SizedBox(height: 20),

                  Text('Number of Audio Bars: ${barCount.toInt()}',
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  Slider(
                    value: barCount,
                    min: 16,
                    max: 256,
                    divisions: 15,
                    label: barCount.toInt().toString(),
                    onChanged: onBarCountChanged,
                  ),
                  const SizedBox(height: 20),

                  const Text('Theme Color Scheming', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 12),
                  ColorPickerSection(
                    primaryColor: primaryColor,
                    secondaryColor: secondaryColor,
                    tertiaryColor: tertiaryColor,
                    bgColor: bgColor,
                    onColorChanged: onColorChanged,
                  ),
                  const Text('Output Video Name', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 30),
                  ElevatedButton.icon(
                    onPressed: () async {
                      FilePickerResult? result = await FilePicker.pickFiles(
                        type: FileType.custom,
                        allowedExtensions: ['mp3', 'wav', 'mp4', 'mkv'],
                      );

                      if (result != null && result.files.single.path != null) {
                        onFileSelected(result.files.single.path);
                      }
                    },
                    icon: const Icon(Icons.folder_open),
                    label: const Text('Select Audio/Video File'),
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size.fromHeight(48),
                    ),
                  ),
                  const SizedBox(height: 15),
                  Text(
                    selectedFilePath != null
                        ? 'Loaded: ${selectedFilePath!.split('/').last}'
                        : 'No Audio File Selected',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: selectedFilePath != null ? Colors.greenAccent : Colors.grey,
                      fontSize: 12,
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: onSelectOutputPath,
                    icon: const Icon(Icons.drive_file_move_outlined),
                    label: const Text('Set Output Save Path'),
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size.fromHeight(48),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    selectedOutputPath != null
                        ? 'Save path: $selectedOutputPath'
                        : 'Destination: Not selected (will prompt on render)',
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: selectedOutputPath != null ? Colors.cyanAccent : Colors.grey,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            
            if (isRendering) ...[
              LinearProgressIndicator(value: renderProgress),
              const SizedBox(height: 12),
            ],
            ElevatedButton(
              onPressed: selectedFilePath == null ? null : onToggleRender,
              style: ElevatedButton.styleFrom(
                backgroundColor: isRendering
                    ? Colors.redAccent
                    : Theme.of(context).colorScheme.primary,
                foregroundColor: Colors.white,
                minimumSize: const Size.fromHeight(50),
              ),
              child: Text(
                isRendering ? 'Cancel Rendering' : 'Generate Video',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
````

## File: `frontend/lib/widgets/preview.dart`
````dart
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class PreviewPanel extends StatelessWidget {
  final Color bgColor;
  final String previewUrl;

  const PreviewPanel({
    super.key,
    required this.bgColor,
    required this.previewUrl,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Live Preview',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Center(
                  child: AspectRatio(
                    aspectRatio: 16 / 9,
                    child: Container(
                      color: bgColor,
                      child: Image.network(
                        previewUrl,
                        key: ValueKey(previewUrl),
                        fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) {
                          return Center(
                            child: Text(
                              "Connecting to API Preview Stream...",
                              style: TextStyle(color: Colors.white54)
                            )
                          );
                        },
                      )
                    ),
                  ),
                )
              )
            )
          ],
        ),
      ),
    );
  }
}
````

## File: `frontend/lib/widgets/color_picker_section.dart`
````dart
import 'package:flutter/material.dart';

class ColorPickerSection extends StatelessWidget {
  final Color primaryColor;
  final Color secondaryColor;
  final Color tertiaryColor;
  final Color bgColor;
  final Function(String label, Color color) onColorChanged;

  const ColorPickerSection({
    super.key,
    required this.primaryColor,
    required this.secondaryColor,
    required this.tertiaryColor,
    required this.bgColor,
    required this.onColorChanged,
  });

  void _pickColor(BuildContext context, String label, Color currentColor, ValueChanged<Color> onSelected) {
    final List<Color> colorPalette = [
      const Color(0xFFFF0096),
      const Color(0xFF00FFFF),
      const Color(0xFF0064FF),
      const Color(0xFF0F0F14),
      Colors.purpleAccent,
      Colors.amberAccent,
      Colors.greenAccent,
      Colors.deepOrangeAccent,
      Colors.black,
      Colors.white,
    ];

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Select $label Color'),
        content: Wrap(
          spacing: 12,
          runSpacing: 12,
          children: colorPalette.map((color) {
            return GestureDetector(
              onTap: () {
                onSelected(color);
                Navigator.pop(context);
              },
              child: CircleAvatar(
                backgroundColor: color,
                radius: 20,
                child: currentColor == color
                    ? Icon(
                        Icons.check,
                        color: color.computeLuminance() > 0.5 ? Colors.black : Colors.white,
                      )
                    : null,
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final chips = [
      (label: 'Primary', color: primaryColor),
      (label: 'Secondary', color: secondaryColor),
      (label: 'Tertiary', color: tertiaryColor),
      (label: 'BG', color: bgColor),
    ];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: chips.map((chip) {
        return InkWell(
          onTap: () => _pickColor(
            context,
            chip.label,
            chip.color,
            (selectedColor) => onColorChanged(chip.label, selectedColor),
          ),
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.all(4.0),
            child: Column(
              children: [
                CircleAvatar(
                  backgroundColor: chip.color,
                  radius: 18,
                ),
                const SizedBox(height: 4),
                Text(chip.label, style: const TextStyle(fontSize: 11)),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}
````

## File: `backend/video_engine.py`
````py
import os
import cv2
import subprocess
from .audio_analyzer import AudioAnalyzer
from .frame_renderer import FrameRenderer


class VideoEngine:
    def __init__(self, audio_path, config, progress_callback=None, status_callback=None, output_path=None):
        self.audio_path = audio_path
        self.config = config
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        self.temp_silent_video = "tempSilentRender.mp4"
        self.temp_converted_wav = "tempBackgroundDecode.wav"
        self.output_mp4_path = output_path

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def _update_progress(self, current, total):
        if self.progress_callback:
            self.progress_callback(current, total)

    def render(self):
        """Executes the rendering and mixing pipeline."""
        analysis_path = self.audio_path
        video_writer = None

        try:
            # 1. Convert non-wav formats
            if not self.audio_path.lower().endswith((".wav", ".wave")):
                self._update_status("Unpacking audio stream...")
                convert_cmd = ["ffmpeg", "-y", "-i", self.audio_path, self.temp_converted_wav]
                subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                analysis_path = self.temp_converted_wav

            self._update_status("Rendering video frames...")
            audio = AudioAnalyzer(analysis_path, targetFPS=60, numBars=self.config.num_bars)
            settings = self.config.get_renderer_settings()
            renderer = FrameRenderer(settings)

            width, height = settings["resolution"]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            video_writer = cv2.VideoWriter(self.temp_silent_video, fourcc, float(audio.fps), (width, height))

            # 2. Render loop
            for frame_idx in range(audio.totalFrames):
                bar_data = audio.getFrameData(frame_idx)
                completed_frame = renderer.renderFrame(bar_data)
                video_writer.write(completed_frame)

                if frame_idx % 15 == 0:
                    self._update_progress(frame_idx, audio.totalFrames)

            video_writer.release()
            video_writer = None

            # 3. Audio/Video FFmpeg merge
            self._update_status("Merging audio track...")
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", self.temp_silent_video, "-i", analysis_path, 
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", self.output_mp4_path
            ]
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._update_status(f"Completed: {os.path.basename(self.audio_path)}")
            return True

        finally:
            if video_writer is not None and video_writer.isOpened():
                video_writer.release()
            if os.path.exists(self.temp_silent_video):
                os.remove(self.temp_silent_video)
            if os.path.exists(self.temp_converted_wav):
                os.remove(self.temp_converted_wav)
````

## File: `backend/frame_renderer.py`
````py
import cv2
import numpy as np
from scipy.io import wavfile


class  FrameRenderer:
    def __init__(self, settings):
        self.settings = settings
        self.width, self.height = settings["resolution"]
        self.scale= self.height / 1080.0
        barBackground = np.array([[settings["tertiaryColor"]], [settings["secondaryColor"]], [settings["primaryColor"]]], dtype = np.uint8)
        self.staticBarBackground = cv2.resize(barBackground, (self.width, self.height), interpolation = cv2.INTER_LINEAR)

    def renderFrame(self, audioFrameData):
        frame = np.zeros((self.height, self.width, 3), dtype = np.uint8)
        frame[:] = self.settings["bgColor"]
        count = len(audioFrameData)
        if count == 0:
            self._drawText(frame)
            self._drawBorder(frame)
            return frame
        mask = np.zeros((self.height, self.width), dtype = np.uint8)
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
        
        cv2.copyTo(src = self.staticBarBackground, mask = mask, dst = frame)
        self._drawText(frame)
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
        cv2.putText(frame, self.settings["title"], (margin, titleY), font, titleScale, self.settings["titleColor"], titleThick, cv2.LINE_AA)
        cv2.putText(frame, self.settings["artist"], (margin, artistY), font, artistScale, self.settings["artistColor"], artistThick, cv2.LINE_AA)
    
    def _drawBorder(self, frame):
        borderWidth = self.settings["borderWidth"]
        if borderWidth <= 0: return
        cv2.rectangle(frame, (0, 0), (self.width, self.height), self.settings["borderColor1"], borderWidth)
        cv2.rectangle(frame, (borderWidth, borderWidth), (self.width - borderWidth, self.height - borderWidth), self.settings["borderColor2"], 1)
````

## File: `backend/server.py`
````py
import os
import cv2
import numpy as np
import threading
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from .render_config import RenderConfig
from .frame_renderer import FrameRenderer
from .video_engine import VideoEngine

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
    output_path: str

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
            status_callback=_status_callback,
            output_path=req.output_path
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
````

## File: `backend/audio_analyzer.py`
````py
import numpy as np
from scipy.io import wavfile


class AudioAnalyzer:
    def __init__(self, audioPath, targetFPS = 60, numBars = 64, smoothingFactor = 0.15):
        self.sampleRate, data  = wavfile.read(audioPath)
        if len(data.shape) > 1:
            self.audioData = np.mean(data, axis = 1)
        else:
            self.audioData = data
        
        if self.audioData.dtype == np.int16:
            self.audioData = self.audioData.astype(np.float32) / 32768.0
        elif self.audioData.dtype == np.int32:
            self.audioData = self.audioData.astype(np.float32) / 2147483648.0

        self.fps = targetFPS
        self.numBars = numBars
        self.smoothingFactor = smoothingFactor
        self.samplesPerFrame = int(self.sampleRate /  self.fps)
        self.totalFrames = int(len(self.audioData) / (self.samplesPerFrame))
        self.previousFramebars = np.zeros(self.numBars, dtype = np.float32)
        self.barEdges = np.logspace(np.log10(1), np.log10(self.samplesPerFrame // 2), self.numBars + 1).astype(int)

    def getFrameData(self,  frameIndex):
        if frameIndex >= self.totalFrames:
            return np.zeros(self.numBars, dtype = np.float32)
        startSample = frameIndex * self.samplesPerFrame
        endSample = startSample + self.samplesPerFrame
        audioChunk = self.audioData[startSample:endSample]
        if len(audioChunk) < self.samplesPerFrame:
            audioChunk = np.pad(audioChunk, (0, self.samplesPerFrame - len(audioChunk)))
        fftData = np.abs(np.fft.rfft(audioChunk))
        currentBars = np.zeros(self.numBars, dtype = np.float32)
        for i in range(self.numBars):
            startIdx = self.barEdges[i]
            endIdx = max(startIdx + 1, self.barEdges[i + 1])
            currentBars[i] = np.mean(fftData[startIdx:endIdx])
        currentBars =  currentBars * 2.5
        currentBars = np.clip(currentBars, 0.0, 1.0)
        for i in range(self.numBars):
            if currentBars[i] < self.previousFramebars[i]:
                currentBars[i] = (currentBars[i] * self.smoothingFactor) + (self.previousFramebars[i] * (1.0 - self.smoothingFactor))
        self.previousFramebars = currentBars.copy()
        return currentBars
````

## File: `backend/render_config.py`
````py
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
````
