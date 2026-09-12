// test/widget_test.dart

import 'package:flutter_test/flutter_test.dart';
import 'package:multilingual_cyber_safety_app/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    expect(find.text('Cyber-Safety Assistant'), findsOneWidget);
  });
}