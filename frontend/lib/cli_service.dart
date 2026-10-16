import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;

class CliService {
  static Process? _activeRenderProcess;

  static List<String> _getCommand(List<String> args) {
    final exeDir = p.dirname(Platform.resolvedExecutable);
    
    if (Platform.isWindows) {
      final prodPathOneDir = p.normalize(p.join(exeDir, '..', 'backend', 'visualizer_backend', 'visualizer_backend.exe'));
      if (File(prodPathOneDir).existsSync()) return [prodPathOneDir, ...args];

      final prodPathStandalone = p.normalize(p.join(exeDir, '..', 'backend', 'visualizer_backend.exe'));
      if (File(prodPathStandalone).existsSync()) return [prodPathStandalone, ...args];
    } else {
      final prodPathUnix = p.normalize(p.join(exeDir, '..', 'backend', 'visualizer_backend', 'visualizer_backend'));
      if (File(prodPathUnix).existsSync()) return [prodPathUnix, ...args];
    }

    if (Platform.isWindows) {
      final devParentPath = p.normalize(p.join(Directory.current.path, '..', 'backend', 'dist', 'visualizer_backend', 'visualizer_backend.exe'));
      if (File(devParentPath).existsSync()) return [devParentPath, ...args];

      final devLocalPath = p.normalize(p.join(Directory.current.path, 'backend', 'dist', 'visualizer_backend', 'visualizer_backend.exe'));
      if (File(devLocalPath).existsSync()) return [devLocalPath, ...args];
    } else {
      final devParentPathUnix = p.normalize(p.join(Directory.current.path, '..', 'backend', 'dist', 'visualizer_backend', 'visualizer_backend'));
      if (File(devParentPathUnix).existsSync()) return [devParentPathUnix, ...args];
    }

    final possibleScriptPaths = [
      p.normalize(p.join(Directory.current.path, 'backend', 'cli.py')),
      p.normalize(p.join(Directory.current.path, '..', 'backend', 'cli.py')),
      p.normalize(p.join(exeDir, '..', '..', '..', 'backend', 'cli.py')),
      p.normalize(p.join(exeDir, '..', 'backend', 'cli.py')),
    ];

    String? scriptPath;
    for (final path in possibleScriptPaths) {
      if (File(path).existsSync()) {
        scriptPath = path;
        break;
      }
    }
    scriptPath ??= possibleScriptPaths.first;

    final String pythonCmd = Platform.isWindows ? 'py' : 'python3';
    return [pythonCmd, scriptPath, ...args];
  }

  static Future<bool> generatePreview({
    required String configJson,
    required String outputPath,
  }) async {
    try {
      final encodedConfig = base64Encode(utf8.encode(configJson));
      final cmd = _getCommand([
        '--mode', 'preview',
        '--config', encodedConfig,
        '--output', outputPath,
      ]);
      final result = await Process.run(cmd.first, cmd.sublist(1));
      if (result.exitCode != 0) {
        print('[Preview Error]: ${result.stderr}');
      }
      return result.exitCode == 0;
    } catch (e) {
      print('[Preview Exception]: $e');
      return false;
    }
  }

  static Stream<Map<String, dynamic>> startRender({
    required String audioPath,
    required String configJson,
    required String outputPath,
  }) {
    final controller = StreamController<Map<String, dynamic>>();
    final StringBuffer errorBuffer = StringBuffer();

    () async {
      try {
        final encodedConfig = base64Encode(utf8.encode(configJson));
        final cmd = _getCommand([
          '--mode', 'render',
          '--audio', audioPath,
          '--config', encodedConfig,
          '--output', outputPath,
        ]);

        final process = await Process.start(cmd.first, cmd.sublist(1));
        _activeRenderProcess = process;

        process.stdout
            .transform(const Utf8Decoder(allowMalformed: true))
            .transform(const LineSplitter())
            .listen((line) {
          print('[Backend Out]: $line'); // Echo to terminal
          if (line.startsWith('PROGRESS:')) {
            final parts = line.replaceFirst('PROGRESS:', '').split(':');
            if (parts.length == 2) {
              controller.add({
                'type': 'progress',
                'current': int.tryParse(parts[0]) ?? 0,
                'total': int.tryParse(parts[1]) ?? 1,
              });
            }
          } else if (line.startsWith('STATUS:')) {
            controller.add({
              'type': 'status',
              'message': line.replaceFirst('STATUS:', ''),
            });
          } else if (line.startsWith('RENDER_COMPLETE:')) {
            controller.add({
              'type': 'complete',
              'output_path': line.replaceFirst('RENDER_COMPLETE:', ''),
            });
          }
        });

        process.stderr
            .transform(const Utf8Decoder(allowMalformed: true))
            .transform(const LineSplitter())
            .listen((line) {
          if (line.trim().isNotEmpty) {
            print('[Backend Err]: $line'); // Echo to terminal
            errorBuffer.writeln(line);
          }
        });

        final exitCode = await process.exitCode;
        if (exitCode != 0 && !controller.isClosed) {
          controller.add({
            'type': 'error',
            'message': errorBuffer.isNotEmpty ? errorBuffer.toString() : 'Process exited with code $exitCode',
          });
        }
        if (!controller.isClosed) {
          controller.close();
        }
      } catch (e) {
        if (!controller.isClosed) {
          controller.add({'type': 'error', 'message': e.toString()});
          controller.close();
        }
      } finally {
        _activeRenderProcess = null;
      }
    }();

    return controller.stream;
  }

  static void cancelRender() {
    _activeRenderProcess?.kill();
    _activeRenderProcess = null;
  }
}