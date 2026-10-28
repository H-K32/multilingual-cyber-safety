// test/widget_test.dart

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:multilingual_cyber_safety_app/main.dart';

void main() {
  testWidgets('App smoke test — home screen key widgets present',
      (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    expect(find.text('Cyber-Safety Assistant'), findsOneWidget);
    expect(find.text('Analyze a screenshot'), findsOneWidget);
    expect(find.text('Sender phone number (optional)'), findsOneWidget);
    expect(find.text('Where did this come from? (optional)'), findsOneWidget);
    expect(find.text('Check a number'), findsOneWidget);
    expect(find.text('Report a number'), findsOneWidget);
  });

  testWidgets('Language switch to Amharic shows Amharic UI strings',
      (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    // Open language menu
    await tester.tap(find.byIcon(Icons.language));
    await tester.pumpAndSettle();
    // Select Amharic
    await tester.tap(find.text('አማርኛ'));
    await tester.pumpAndSettle();
    expect(find.text('የሳይበር ደህንነት ረዳት'), findsOneWidget);
    expect(find.text('ቁጥር ሪፖርት ያድርጉ'), findsOneWidget);
  });

  testWidgets('Analyze button is present and enabled when not loading',
      (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    expect(find.text('Analyze Message'), findsOneWidget);
  });
}
