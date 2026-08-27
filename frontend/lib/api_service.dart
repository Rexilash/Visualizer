import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000';

  /// Cache-busted preview image URL for live streaming update
  static String getPreviewUrl() {
    return '$baseUrl/api/preview?t=${DateTime.now().millisecondsSinceEpoch}';
  }

  static Future<void> updateConfig({
    required String resKey,
    required int numBars,
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
          'rgb_primary': rgbPrimary,
          'rgb_secondary': rgbSecondary,
          'rgb_tertiary': rgbTertiary,
          'rgb_bg': rgbBg,
        }),
      );
    } catch (_) {}
  }

  static Future<bool> startRender(String audioPath) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/render/start'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'audio_path': audioPath}),
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

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