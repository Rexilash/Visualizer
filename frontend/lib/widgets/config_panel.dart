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