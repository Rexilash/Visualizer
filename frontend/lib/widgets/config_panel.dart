import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'color_picker_section.dart';

class ConfigPanel extends StatefulWidget {
  final String selectedResolution;
  final List<String> resolutionOptions;
  final double barCount;
  final String title;
  final String artist;
  final String bgMode;
  final String? bgImagePath;
  final String audioSourceMode; // "file" or "url"
  final String audioUrl;
  final String? selectedFilePath;
  final bool isRendering;
  final double renderProgress;
  final Color primaryColor;
  final Color secondaryColor;
  final Color tertiaryColor;
  final Color bgColor;
  final String outputFileName;
  final String? selectedOutputPath;

  final ValueChanged<String?> onResolutionChanged;
  final ValueChanged<double> onBarCountChanged;
  final ValueChanged<String> onTitleChanged;
  final ValueChanged<String> onArtistChanged;
  final ValueChanged<String> onBgModeChanged;
  final ValueChanged<String?> onBgImageSelected;
  final ValueChanged<String> onAudioSourceModeChanged;
  final ValueChanged<String> onAudioUrlChanged;
  final Function(String, Color) onColorChanged;
  final ValueChanged<String?> onFileSelected;
  final VoidCallback onToggleRender;
  final ValueChanged<String> onOutputFileNameChanged;
  final VoidCallback onSelectOutputPath;

  const ConfigPanel({
    super.key,
    required this.selectedResolution,
    required this.resolutionOptions,
    required this.barCount,
    required this.title,
    required this.artist,
    required this.bgMode,
    required this.bgImagePath,
    required this.audioSourceMode,
    required this.audioUrl,
    required this.selectedFilePath,
    required this.isRendering,
    required this.renderProgress,
    required this.primaryColor,
    required this.secondaryColor,
    required this.tertiaryColor,
    required this.bgColor,
    required this.onResolutionChanged,
    required this.onBarCountChanged,
    required this.onTitleChanged,
    required this.onArtistChanged,
    required this.onBgModeChanged,
    required this.onBgImageSelected,
    required this.onAudioSourceModeChanged,
    required this.onAudioUrlChanged,
    required this.onColorChanged,
    required this.onFileSelected,
    required this.onToggleRender,
    required this.outputFileName,
    required this.onOutputFileNameChanged,
    required this.selectedOutputPath,
    required this.onSelectOutputPath,
  });

  @override
  State<ConfigPanel> createState() => _ConfigPanelState();
}

class _ConfigPanelState extends State<ConfigPanel> {
  final ScrollController _scrollController = ScrollController();
  bool _showTopShadow = false;
  bool  _showBottomShadow = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _updateShadows());
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _updateShadows() {
    if (!_scrollController.hasClients) return;
    final maxScroll = _scrollController.position.maxScrollExtent;
    final currentScroll = _scrollController.offset;

    setState(() {
      _showTopShadow = currentScroll > 5;
      _showBottomShadow = currentScroll < (maxScroll - 5) && maxScroll > 0;
    });
  }
  
  @override
  Widget build(BuildContext context) {
    bool hasValidSource = widget.audioSourceMode == 'file' 
        ? widget.selectedFilePath != null 
        : widget.audioUrl.trim().startsWith('http');

    final cardBgColor = Theme.of(context).cardTheme.color ?? const Color(0xFF1E1E24);

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Config', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const Divider(height: 20),
            Expanded(
              child: Stack(
                children: [
                  ScrollConfiguration(
                    behavior: ScrollConfiguration.of(context).copyWith(scrollbars: false), 
                    child: NotificationListener<ScrollNotification>(
                      onNotification: (notification) {
                        _updateShadows();
                        return false;
                      },
                      child: ListView(
                        controller: _scrollController,
                        padding: const EdgeInsets.only(bottom: 30.0),
                        children: [
                          // Track Metadata
                          const Text('Track Information', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          TextFormField(
                            initialValue: widget.title,
                            decoration: const InputDecoration(labelText: 'Song Title', border: OutlineInputBorder()),
                            onChanged: widget.onTitleChanged,
                          ),
                          const SizedBox(height: 10),
                          TextFormField(
                            initialValue: widget.artist,
                            decoration: const InputDecoration(labelText: 'Artist Name', border: OutlineInputBorder()),
                            onChanged: widget.onArtistChanged,
                          ),
                          const SizedBox(height: 20),

                          // Background Settings
                          const Text('Background Style', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          SegmentedButton<String>(
                            segments: const [
                              ButtonSegment(value: 'color', label: Text('Solid Color')),
                              ButtonSegment(value: 'image', label: Text('Custom Image')),
                            ],
                            selected: {widget.bgMode},
                            onSelectionChanged: (val) => widget.onBgModeChanged(val.first),
                          ),
                          const SizedBox(height: 10),
                          if (widget.bgMode == 'image') ...[
                            ElevatedButton.icon(
                              onPressed: () async {
                                FilePickerResult? res = await FilePicker.pickFiles(
                                  type: FileType.image,
                                );
                                if (res != null && res.files.single.path != null) {
                                  widget.onBgImageSelected(res.files.single.path);
                                }
                              },
                              icon: const Icon(Icons.image),
                              label: const Text('Select Background Image'),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              widget.bgImagePath != null && widget.bgImagePath!.isNotEmpty
                                  ? 'Image: ${widget.bgImagePath!.split('/').last}'
                                  : 'No image selected',
                              textAlign: TextAlign.center,
                              style: const TextStyle(fontSize: 11, color: Colors.grey),
                            ),
                            const SizedBox(height: 12),
                          ],

                          // Resolution & Bars
                          const Text('Resolution (16:9)', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          DropdownButtonFormField<String>(
                            value: widget.selectedResolution,
                            decoration: const InputDecoration(border: OutlineInputBorder(), contentPadding: EdgeInsets.symmetric(horizontal: 12)),
                            items: widget.resolutionOptions.map((res) => DropdownMenuItem(value: res, child: Text(res))).toList(),
                            onChanged: widget.onResolutionChanged,
                          ),
                          const SizedBox(height: 16),

                          Text('Audio Bars: ${widget.barCount.toInt()}', style: const TextStyle(fontWeight: FontWeight.w600)),
                          Slider(
                            value: widget.barCount,
                            min: 16,
                            max: 48,
                            divisions: 15,
                            onChanged: widget.onBarCountChanged,
                          ),
                          const SizedBox(height: 16),

                          // Color Scheming
                          const Text('Color Scheme', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          ColorPickerSection(
                            primaryColor: widget.primaryColor,
                            secondaryColor: widget.secondaryColor,
                            tertiaryColor: widget.tertiaryColor,
                            bgColor: widget.bgColor,
                            onColorChanged: widget.onColorChanged,
                          ),
                          const SizedBox(height: 20),

                          // Audio Input Source Selection
                          const Text('Audio Source', style: TextStyle(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 8),
                          SegmentedButton<String>(
                            segments: const [
                              ButtonSegment(value: 'file', label: Text('Local File')),
                              ButtonSegment(value: 'url', label: Text('Media Link')),
                            ],
                            selected: {widget.audioSourceMode},
                            onSelectionChanged: (val) => widget.onAudioSourceModeChanged(val.first),
                          ),
                          const SizedBox(height: 12),
                          if (widget.audioSourceMode == 'file') ...[
                            ElevatedButton.icon(
                              onPressed: () async {
                                FilePickerResult? result = await FilePicker.pickFiles(
                                  type: FileType.custom,
                                  allowedExtensions: ['mp3', 'wav', 'mp4', 'mkv', 'flac'],
                                );
                                if (result != null && result.files.single.path != null) {
                                  widget.onFileSelected(result.files.single.path);
                                }
                              },
                              icon: const Icon(Icons.folder_open),
                              label: const Text('Select Audio/Video File'),
                            ),
                            Text(
                              widget.selectedFilePath != null ? 'Loaded: ${widget.selectedFilePath!.split('/').last}' : 'No File Selected',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: widget.selectedFilePath != null ? Colors.greenAccent : Colors.grey, fontSize: 11),
                            ),
                          ] else ...[
                            TextFormField(
                              initialValue: widget.audioUrl,
                              decoration: const InputDecoration(
                                labelText: 'Media Link (YouTube, Direct WAV/MP3 URL)',
                                border: OutlineInputBorder(),
                                prefixIcon: Icon(Icons.link),
                              ),
                              onChanged: widget.onAudioUrlChanged,
                            ),
                          ],
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            onPressed: widget.onSelectOutputPath,
                            icon: const Icon(Icons.drive_file_move_outlined),
                            label: const Text('Set Save Destination'),
                          ),
                          Text(
                            widget.selectedOutputPath != null ? 'Save: ${widget.selectedOutputPath}' : 'Will prompt on render',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: widget.selectedOutputPath != null ? Colors.cyanAccent : Colors.grey, fontSize: 11),
                          ),
                        ],
                      ),
                    )
                  ),
                  if (_showTopShadow)
                    Positioned(
                      top: 0,
                      left: 0,
                      right: 0,
                      height: 100,
                      child: IgnorePointer(
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: [
                                cardBgColor,
                                cardBgColor.withOpacity(0.0),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),

                  if (_showBottomShadow)
                    Positioned(
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: 100,
                      child: IgnorePointer(
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                              colors: [
                                cardBgColor,
                                cardBgColor.withOpacity(0.0),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              )
            ),
            if (widget.isRendering) ...[
              LinearProgressIndicator(value: widget.renderProgress),
              const SizedBox(height: 12),
            ],
            ElevatedButton(
              onPressed: !hasValidSource ? null : widget.onToggleRender,
              style: ElevatedButton.styleFrom(
                backgroundColor: widget.isRendering ? Colors.redAccent : Theme.of(context).colorScheme.primary,
                foregroundColor: Colors.white,
                minimumSize: const Size.fromHeight(48),
              ),
              child: Text(widget.isRendering ? 'Cancel Rendering' : 'Generate Video'),
            ),
          ],
        ),
      ),
    );
  }
}