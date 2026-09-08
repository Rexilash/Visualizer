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