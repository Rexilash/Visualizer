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
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.white10),
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
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}