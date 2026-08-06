import 'package:flutter/material.dart';
import 'package:flutter/widget_previews.dart';
import '../widgets/config_panel.dart';
import '../test/preview.dart';

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
  }

  void _toggleRender() {
    setState(() {
      if (isRendering) {
        isRendering = false;
        renderProgress = 0.0;
      } else {
        isRendering = true;
      }
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
                  if (val != null) setState(() => selectedResolution = val);
                },
                onBarCountChanged: (val) => setState(() => barCount = val),
                onColorChanged: _handleColorChange,
                onFileSelected: (path) => setState(() => selectedFilePath = path),
                onToggleRender: _toggleRender,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: PreviewPanel(bgColor: bgColor),
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