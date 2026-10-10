import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;

class CliService {
  static Process? _activeRenderProcess;

  static String get _backendPath {
    final exeDir = p.dirname(Platform.resolvedExecutable);
    
    // Production paths (bundled sibling folders)
    final prodPathOneDir = p.normalize(p.join(exeDir, '..', 'backend', 'visualizer_backend', 'visualizer_backend.exe'));
    if (File(prodPathOneDir).existsSync()) return prodPathOneDir;

    final prodPathStandalone = p.normalize(p.join(exeDir, '..', 'backend', 'visualizer_backend.exe'));
    if (File(prodPathStandalone).existsSync()) return prodPathStandalone;

    // Development fallbacks (running flutter run inside frontend/ or root)
    final devParentPath = p.normalize(p.join(Directory.current.path, '..', 'backend', 'dist', 'visualizer_backend', 'visualizer_backend.exe'));
    if (File(devParentPath).existsSync()) return devParentPath;

    return p.join(Directory.current.path, 'backend', 'dist', 'visualizer_backend', 'visualizer_backend.exe');
  }

  /// Generates a preview image frame on disk via CLI execution.
  static Future<bool> generatePreview({
    required String configJson,
    required String outputPath,
  }) async {
    try {
      final encodedConfig = base64Encode(utf8.encode(configJson));
      final result = await Process.run(_backendPath, [
        '--mode', 'preview',
        '--config', encodedConfig,
        '--output', outputPath,
      ]);
      return result.exitCode == 0;
    } catch (e) {
      return false;
    }
  }

  /// Spawns video rendering process and yields stdout progress updates.
  static Stream<Map<String, dynamic>> startRender({
    required String audioPath,
    required String configJson,
    required String outputPath,
  }) async* {
    try {
      final encodedConfig = base64Encode(utf8.encode(configJson));
      _activeRenderProcess = await Process.start(_backendPath, [
        '--mode', 'render',
        '--audio', audioPath,
        '--config', encodedConfig,
        '--output', outputPath,
      ]);

      final lines = _activeRenderProcess!.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter());

      await for (final line in lines) {
        if (line.startsWith('PROGRESS:')) {
          final parts = line.replaceFirst('PROGRESS:', '').split(':');
          if (parts.length == 2) {
            yield {
              'type': 'progress',
              'current': int.tryParse(parts[0]) ?? 0,
              'total': int.tryParse(parts[1]) ?? 1,
            };
          }
        } else if (line.startsWith('STATUS:')) {
          yield {
            'type': 'status',
            'message': line.replaceFirst('STATUS:', ''),
          };
        } else if (line.startsWith('RENDER_COMPLETE:')) {
          yield {
            'type': 'complete',
            'output_path': line.replaceFirst('RENDER_COMPLETE:', ''),
          };
        }
      }

      final exitCode = await _activeRenderProcess!.exitCode;
      if (exitCode != 0) {
        yield {'type': 'error', 'message': 'Process exited with code $exitCode'};
      }
    } catch (e) {
      yield {'type': 'error', 'message': e.toString()};
    } finally {
      _activeRenderProcess = null;
    }
  }

  static void cancelRender() {
    _activeRenderProcess?.kill();
    _activeRenderProcess = null;
  }
}