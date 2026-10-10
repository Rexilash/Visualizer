import 'dart:io';
import 'package:flutter/material.dart';

class PreviewPanel extends StatelessWidget {
  final Color bgColor;
  final File? previewFile;

  const PreviewPanel({
    super.key,
    required this.bgColor,
    required this.previewFile,
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
                      child: previewFile != null && previewFile!.existsSync()
                          ? Image.file(
                              previewFile!,
                              key: ValueKey(previewFile!.lastModifiedSync().millisecondsSinceEpoch),
                              gaplessPlayback: true,
                              fit: BoxFit.contain,
                            )
                          : const Center(
                              child: Text(
                                "Generating Preview...",
                                style: TextStyle(color: Colors.white54),
                              ),
                            ),
                    ),
                  ),
                ),
              ),
            )
          ],
        ),
      ),
    );
  }
}