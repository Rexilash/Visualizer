import 'dart:convert';
import 'package:http/http.dart' as http;

/// HTTP Service handling communication between Flutter UI and FastAPI backend.
class ApiService {
  static String baseUrl = const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://127.0.0.1:8000');

  /// Cache-busted preview image URL for live streaming update
  static String getPreviewUrl() {
    return '$baseUrl/api/preview?t=${DateTime.now().millisecondsSinceEpoch}';
  }

  /// Sends updated configuration parameters to backend.
  static Future<void> updateConfig({
    required String resKey,
    required int numBars,
    required String title,
    required String artist,
    required String bgMode,
    required String? bgImagePath,
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
          'title': title,
          'artist': artist,
          'bg_mode': bgMode,
          'bg_image_path': bgImagePath ?? '',
          'rgb_primary': rgbPrimary,
          'rgb_secondary': rgbSecondary,
          'rgb_tertiary': rgbTertiary,
          'rgb_bg': rgbBg,
        }),
      );
    } catch (_) {}
  }

  /// Triggers full background video rendering engine.
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

  /// Polls rendering progress status.
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