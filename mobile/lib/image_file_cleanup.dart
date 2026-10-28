import 'image_file_cleanup_stub.dart'
    if (dart.library.io) 'image_file_cleanup_io.dart' as platform;

class ImageCleanupException implements Exception {}

Future<void> cleanupPickedImage(String path) async {
  try {
    await platform.cleanupPickedImage(path);
  } on ImageCleanupException {
    rethrow;
  } catch (_) {
    throw ImageCleanupException();
  }
}
