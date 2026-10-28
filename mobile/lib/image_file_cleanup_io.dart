import 'dart:io';

import 'package:flutter/foundation.dart';

Future<void> cleanupPickedImage(String path) async {
  if (defaultTargetPlatform != TargetPlatform.android &&
      defaultTargetPlatform != TargetPlatform.iOS) {
    return;
  }
  final file = File(path);
  if (await file.exists()) {
    await file.delete();
  }
}
