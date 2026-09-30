import 'package:flutter/material.dart';
import 'package:frontend/visualizer_screen.dart';

void main() {
  runApp(const Visualizer());
}

/// Root Widget configuring dark theme and app scaffolding.
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