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
    expect(find.text('ዳጉ'), findsOneWidget);
    expect(find.text('“ከማመንዎ በፊት ያረጋግጡ።”'), findsOneWidget);
  });

  testWidgets('Analyze button is present and enabled when not loading',
      (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    expect(find.text('Analyze Message'), findsOneWidget);
  });

  testWidgets('Dagu product identity and motto are prominently displayed',
      (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    expect(find.text('Dagu'), findsOneWidget);
    expect(find.text('“Check Before You Trust.”'), findsOneWidget);
    expect(find.text('Why Dagu?'), findsOneWidget);

    // Expand the "Why Dagu?" tile
    await tester.tap(find.text('Why Dagu?'));
    await tester.pumpAndSettle();
    expect(
      find.text(
        'Inspired by the Afar tradition of sharing and verifying information, Dagu represents our mission to help people recognize scams and phishing attempts before trusting or sharing suspicious information.',
      ),
      findsOneWidget,
    );
  });

  testWidgets('CheckNumberScreen renders search form and Reported Numbers section',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: CheckNumberScreen(language: AppLanguage.english),
      ),
    );
    await tester.pumpAndSettle();

    // Verify search section
    expect(find.text('Check a Phone Number'), findsWidgets);
    expect(find.text('Phone number (e.g. 0911234567 or +251911234567)'), findsOneWidget);
    expect(find.text('Check Number'), findsOneWidget);

    // Verify Reported Numbers section
    expect(find.text('Reported Numbers'), findsOneWidget);
    expect(find.text('Filter by number or category...'), findsOneWidget);
  });

  testWidgets('PhoneReputationCard shows dispute button on reported number and opens dispute sheet',
      (WidgetTester tester) async {
    final reportedEntry = {
      'status': 'reported',
      'phone_number': '+251 91 123 4567',
      'report_count': 3,
      'categories': ['scam', 'phishing'],
      'verification_status': 'unverified',
      'explanation': '3 local report(s) were found.',
    };

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PhoneReputationCard(
            entry: reportedEntry,
            language: AppLanguage.english,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Verify reported reputation card content
    expect(find.text('+251 91 123 4567'), findsOneWidget);
    expect(find.text('Suspicious'), findsOneWidget);
    expect(find.text('Report inaccurate status'), findsOneWidget);

    // Tap "Report inaccurate status"
    await tester.tap(find.text('Report inaccurate status'));
    await tester.pumpAndSettle();

    // Verify dispute modal sheet appears with disclaimer and fields
    expect(find.text('Dispute Phone Reputation'), findsOneWidget);
    expect(
      find.text(
        'Submitting a dispute queues this number for moderation review. It does not automatically delete existing reports or mark the number safe.',
      ),
      findsOneWidget,
    );
    expect(find.text('Why is this status inaccurate?'), findsOneWidget);
    expect(find.text('Contact information (optional)'), findsOneWidget);
    expect(find.text('Submit Dispute'), findsOneWidget);
  });

  testWidgets('PhoneReputationCard does not show dispute button on unlisted safe number',
      (WidgetTester tester) async {
    final unlistedEntry = {
      'status': 'no_reports_found',
      'phone_number': '+251 91 100 0000',
      'explanation': 'No matching reports were found in the local dataset.',
    };

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PhoneReputationCard(
            entry: unlistedEntry,
            language: AppLanguage.english,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Safe'), findsOneWidget);
    expect(find.text('Report inaccurate status'), findsNothing);
  });

  testWidgets('SecurityOperationsScreen renders authentication card when unauthenticated',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: SecurityOperationsScreen(language: AppLanguage.english),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Security Operations'), findsWidgets);
    expect(find.text('Threat signals feed for authorized security analysts.'), findsOneWidget);
    expect(find.text('Enter SOC Analyst API Token'), findsOneWidget);
    expect(find.text('Connect to SOC Feed'), findsOneWidget);
  });

  testWidgets('SecurityOperationsScreen renders feed, confidence banner, and event cards when authenticated',
      (WidgetTester tester) async {
    final mockEvents = [
      {
        'event_id': 'EVT-SPIKE-CBE01',
        'phone_number': '+251 91 123 4567',
        'phone_masked': '+251 91 ••• ••67',
        'event_type': 'reputation_spike',
        'priority': 'critical',
        'total_reports': 6,
        'reports_last_24h': 6,
        'categories': ['scam', 'phishing'],
        'reason': 'Sudden surge of 6 reports in the last 24 hours.',
        'evidence_summary': 'Multiple urgent Telegram fraud reports received.',
        'confidence_limitations': 'Heuristic community threat signal. Unverified.',
        'review_status': 'new',
        'analyst_notes': null,
        'last_updated': '2026-10-28T18:00:00Z',
        'created_at': '2026-10-28T18:00:00Z',
      },
    ];

    await tester.pumpWidget(
      MaterialApp(
        home: SecurityOperationsScreen(
          language: AppLanguage.english,
          initialEvents: mockEvents,
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Verify Disclaimer Banner
    expect(
      find.text(
        'Threat signals represent unverified community submissions and heuristic indicators. They do not constitute confirmed bank compromise.',
      ),
      findsOneWidget,
    );

    // Verify Filter Chips
    expect(find.text('All Signals'), findsOneWidget);
    expect(find.text('24h Spikes'), findsOneWidget);
    expect(find.text('High Volume'), findsOneWidget);
    expect(find.text('Disputed'), findsOneWidget);

    // Verify Event Details
    expect(find.text('CRITICAL'), findsOneWidget);
    expect(find.text('Reputation Spike (24h)'), findsOneWidget);
    expect(find.text('+251 91 123 4567'), findsOneWidget);
    expect(find.text('Masked: +251 91 ••• ••67'), findsOneWidget);
    expect(find.text('6 reports'), findsOneWidget);
    expect(find.text('+6 in 24h'), findsOneWidget);
    expect(find.text('Scam'), findsOneWidget);
    expect(find.text('Phishing'), findsOneWidget);
    expect(find.text('Acknowledge'), findsOneWidget);
    expect(find.text('Update Status'), findsOneWidget);

    // Scroll to and tap "Update Status" to verify sheet opens
    await tester.ensureVisible(find.text('Update Status'));
    await tester.tap(find.text('Update Status'));
    await tester.pumpAndSettle();

    expect(find.text('Update Status: +251 91 123 4567'), findsOneWidget);
    expect(find.text('Select review status:'), findsOneWidget);
    expect(find.text('Acknowledged'), findsOneWidget);
    expect(find.text('Under Review'), findsOneWidget);
    expect(find.text('Resolved'), findsOneWidget);
    expect(find.text('Dismissed'), findsOneWidget);
    expect(find.text('Save Status'), findsOneWidget);
  });

  testWidgets('HomeScreen provides discreet entry to Security Operations',
      (WidgetTester tester) async {
    await tester.pumpWidget(const CyberSafetyApp());
    expect(find.text('Security Operations'), findsWidgets);
    expect(find.byIcon(Icons.admin_panel_settings_outlined), findsOneWidget);
  });
}
