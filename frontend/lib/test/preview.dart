import 'package:flutter/material.dart';

class PreviewPanel extends StatelessWidget {
  final Color bgColor;

  const PreviewPanel({
    super.key,
    required this.bgColor,
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
                      child: const Center(
                        child: Text(
                          'PREVIEW CANVAS\n(Waiting for Python Server stream)',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.white54),
                        ),
                      ),
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