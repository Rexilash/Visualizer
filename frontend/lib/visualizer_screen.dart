import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import '../widgets/config_panel.dart';
import 'widgets/preview.dart';
import 'cli_service.dart';

class VisualizerStudioScreen extends StatefulWidget {
  const VisualizerStudioScreen({super.key});

  @override
  State<VisualizerStudioScreen> createState() => _VisualizerStudioScreenState();
}

class _VisualizerStudioScreenState extends State<VisualizerStudioScreen> {
  String selectedResolution = 'FHD (1920x1080)';
  double barCount = 32;

  String songTitle = "VISUALIZER RENDER";
  String artistName = "Spectrum Visualizer Engine";

  String bgMode = "color";
  String? bgImagePath;

  String audioSourceMode = "file";
  String audioUrl = "";
  String? selectedFilePath;

  bool isRendering = false;
  double renderProgress = 0.0;
  String renderStatusMessage = "Idle";
  File? previewFile;
  
  Timer? _debounceTimer;
  StreamSubscription? _renderSubscription;
  String customFileName = "Visualizer_output";
  String? selectedOutputPath;

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
  void initState() {
    super.initState();
    _syncConfigToBackend();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _renderSubscription?.cancel();
    super.dispose();
  }

  String _buildConfigJson() {
    return jsonEncode({
      'res_key': selectedResolution,
      'num_bars': barCount.toInt(),
      'title': songTitle,
      'artist': artistName,
      'bg_mode': bgMode,
      'bg_image_path': bgImagePath ?? '',
      'rgb_primary': [primaryColor.red, primaryColor.green, primaryColor.blue],
      'rgb_secondary': [secondaryColor.red, secondaryColor.green, secondaryColor.blue],
      'rgb_tertiary': [tertiaryColor.red, tertiaryColor.green, tertiaryColor.blue],
      'rgb_bg': [bgColor.red, bgColor.green, bgColor.blue],
    });
  }

  void _syncConfigToBackend() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 200), () async {
      final tempDir = Directory.systemTemp;
      final tempPreviewPath = p.join(tempDir.path, 'visualizer_preview.jpg');

      final success = await CliService.generatePreview(
        configJson: _buildConfigJson(),
        outputPath: tempPreviewPath,
      );

      if (success && mounted) {
        setState(() {
          previewFile = File(tempPreviewPath);
        });
      }
    });
  }

  void _handleColorChange(String label, Color color) {
    setState(() {
      switch (label) {
        case 'Primary': primaryColor = color; break;
        case 'Secondary': secondaryColor = color; break;
        case 'Tertiary': tertiaryColor = color; break;
        case 'BG': bgColor = color; break;
      }
    });
    _syncConfigToBackend();
  }

  Future<void> _selectSavePath() async {
    String formattedName = customFileName.trim().isEmpty ? 'visualizer_output' : customFileName.trim();
    if (!formattedName.toLowerCase().endsWith('.mp4')) formattedName += '.mp4';

    String? savePath = await FilePicker.saveFile(
      dialogTitle: "Select destination for rendered video",
      fileName: formattedName,
      allowedExtensions: ["mp4"],
      type: FileType.custom,
    );

    if (savePath != null) {
      setState(() => selectedOutputPath = savePath);
    }
  }

  Future<void> _toggleRender() async {
    if (isRendering) {
      CliService.cancelRender();
      _renderSubscription?.cancel();
      setState(() {
        isRendering = false;
        renderProgress = 0.0;
        renderStatusMessage = "Cancelled";
      });
      return;
    }

    String audioSource = audioSourceMode == 'file' ? (selectedFilePath ?? '') : audioUrl.trim();
    if (audioSource.isEmpty) return;

    String? finalPath = selectedOutputPath;
    if (finalPath == null) {
      String formattedName = customFileName.trim().isEmpty ? 'visualizer_output' : customFileName.trim();
      if (!formattedName.toLowerCase().endsWith('.mp4')) formattedName += '.mp4';

      finalPath = await FilePicker.saveFile(
        dialogTitle: "Save rendered video as",
        fileName: formattedName,
        allowedExtensions: ["mp4"],
        type: FileType.custom,
      );

      if (finalPath == null) return;
      setState(() => selectedOutputPath = finalPath);
    }

    setState(() {
      isRendering = true;
      renderProgress = 0.0;
      renderStatusMessage = "Starting render engine...";
    });

    final stream = CliService.startRender(
      audioPath: audioSource,
      configJson: _buildConfigJson(),
      outputPath: finalPath,
    );

    _renderSubscription = stream.listen((event) {
      if (!mounted) return;
      setState(() {
        if (event['type'] == 'progress') {
          final int current = event['current'] ?? 0;
          final int total = event['total'] ?? 1;
          renderProgress = total > 0 ? current / total : 0.0;
        } else if (event['type'] == 'status') {
          renderStatusMessage = event['message'] ?? '';
        } else if (event['type'] == 'complete' || event['type'] == 'error') {
          isRendering = false;
        }
      });
    });
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
              width: 400,
              child: ConfigPanel(
                selectedResolution: selectedResolution,
                resolutionOptions: resolutionOptions,
                barCount: barCount,
                title: songTitle,
                artist: artistName,
                bgMode: bgMode,
                bgImagePath: bgImagePath,
                audioSourceMode: audioSourceMode,
                audioUrl: audioUrl,
                selectedFilePath: selectedFilePath,
                isRendering: isRendering,
                renderProgress: renderProgress,
                primaryColor: primaryColor,
                secondaryColor: secondaryColor,
                tertiaryColor: tertiaryColor,
                bgColor: bgColor,
                outputFileName: customFileName,
                selectedOutputPath: selectedOutputPath,
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
                onTitleChanged: (val) {
                  setState(() => songTitle = val);
                  _syncConfigToBackend();
                },
                onArtistChanged: (val) {
                  setState(() => artistName = val);
                  _syncConfigToBackend();
                },
                onBgModeChanged: (val) {
                  setState(() => bgMode = val);
                  _syncConfigToBackend();
                },
                onBgImageSelected: (path) {
                  setState(() => bgImagePath = path);
                  _syncConfigToBackend();
                },
                onAudioSourceModeChanged: (val) => setState(() => audioSourceMode = val),
                onAudioUrlChanged: (val) => setState(() => audioUrl = val),
                onColorChanged: _handleColorChange,
                onFileSelected: (path) => setState(() => selectedFilePath = path),
                onToggleRender: _toggleRender,
                onOutputFileNameChanged: (val) => setState(() => customFileName = val),
                onSelectOutputPath: _selectSavePath,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: PreviewPanel(
                bgColor: bgColor,
                previewFile: previewFile,
              ),
            ),
          ],
        ),
      ),
    );
  }
}