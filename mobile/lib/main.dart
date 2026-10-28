import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart';

import 'image_file_cleanup.dart';

const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

void main() => runApp(const CyberSafetyApp());

enum AppLanguage { english, amharic, oromoo }

const Map<AppLanguage, Map<String, String>> _strings = {
  AppLanguage.english: {
    'appTitle': 'Cyber-Safety Assistant',
    'pageTitle': 'Analyze Multilingual Messages',
    'subtitle':
        'Paste suspicious SMS, Telegram, or Telebirr messages in English, Amharic, or mixed language.',
    'hint':
        'e.g., የእርስዎ telebirr ሂሳብ ታግዷል። PIN ቁጥርዎን በ http://cbe-verify.top/login ያስገቡ',
    'analyzeBtn': 'Analyze Message',
    'analyzingBtn': 'Analyzing...',
    'emptyError': 'Please enter a message to analyze.',
    'connectError':
        'Unable to connect to the backend. Make sure FastAPI is running.',
    'resultsTitle': 'Analysis Results',
    'riskLevel': 'Risk Level',
    'score': 'Score',
    'languageDetected': 'Language Detected',
    'recommendation': 'Recommendation',
    'detectedLinks': 'Detected Links',
    'detectedIndicators': 'Detected Risk Indicators',
    'noDetail': 'No detail provided.',
    'comingSoon': 'Afaan Oromoo support is coming soon!',
    'messageSource': 'Where did this come from? (optional)',
    'senderPhone': 'Sender phone number (optional)',
    'claimedSender':
        'Claimed sender identity (e.g. 994, telebirr, CBE) (optional)',
    'claimedSenderHelp':
        'If the message claims to be from an official shortcode or service, enter it here to check for mismatches.',
    'senderIdentifier': 'Email address or sender identifier (optional)',
    'uploadImage': 'Analyze a screenshot',
    'imageHelp': 'PNG or JPEG, up to 5 MB. English OCR runs on the backend.',
    'imageUnavailable':
        'Image OCR is unavailable. Tesseract is not installed on the server.',
    'extractingText': 'Extracting text...',
    'whyResult': 'Analysis explanations',
    'messageExplanation': 'Message wording',
    'urlExplanation': 'URL analysis',
    'phoneReputation': 'Sender-number reputation',
    'numbersInMessage': 'Phone numbers found in message',
    'senderVerification': 'Sender identity check',
    'analysisLimits': 'Limitations',
    'analysisMethodRules':
        'Rule-based message and URL analysis; no ML model is active.',
    'analysisMethodMl': 'Rule-based analysis with an active ML model.',
    'reports': 'report(s)',
    'noPhoneReports':
        'No matching reports found. This does not mean the number is safe.',
    'sourceContext':
        'Message source is context only and does not affect the risk score.',
    'sms': 'SMS',
    'whatsapp': 'WhatsApp',
    'telegram': 'Telegram',
    'email': 'Email',
    'phoneCall': 'Phone call',
    'other': 'Other',
    'unknown': 'Unknown',
    'uploadTooLarge': 'Images must be 5 MB or smaller.',
    'uploadBadFormat': 'Only valid PNG and JPEG images are supported.',
    'uploadEmpty': 'The selected image is empty.',
    'noOcrText': 'No readable text was found in the image.',
    'inputMethodOcr': 'OCR text (editable)',
    'cleanupFailed':
        'Could not remove the temporary image. It was not uploaded.',
    'ocrResultTitle': 'Screenshot Analysis',
    'ocrExtractedText': 'Extracted text',
    'ocrEditHint': 'Review and edit the extracted text, then tap Analyze.',
    'ocrAnalyzeBtn': 'Analyze extracted text',
    'ocrNumbersFound': 'Phone numbers found in screenshot',
    'tesseractMissing':
        'Tesseract OCR is not installed on the server.\n\nTo enable screenshot analysis, install Tesseract:\n  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n  Linux: sudo apt install tesseract-ocr\n  macOS: brew install tesseract\n\nThen restart the backend.',
    'reportTitle': 'Report a Suspicious Number',
    'checkTitle': 'Check a Phone Number',
    'reportBtn': 'Report Number',
    'checkBtn': 'Check Number',
    'reportingBtn': 'Submitting...',
    'checkingBtn': 'Checking...',
    'phoneNumberField': 'Phone number (e.g. 0911234567 or +251911234567)',
    'phoneRequired': 'Please enter a phone number.',
    'categoriesLabel': 'Report categories (select at least one)',
    'categoryRequired': 'Please select at least one category.',
    'evidenceLabel': 'Message or reason (optional, max 500 characters)',
    'evidencePlaceholder':
        'Describe what you received, without including private details.',
    'reportSuccess':
        'Your report has been submitted as an unverified community report.',
    'reportUpdated': 'An existing record was updated with your report.',
    'checkResult': 'Lookup Result',
    'catScam': 'Scam',
    'catSpam': 'Spam calls',
    'catPhishing': 'Phishing',
    'catImpersonation': 'Impersonation',
    'catMarketing': 'Unwanted marketing',
    'catOther': 'Other',
    'reportNavBtn': 'Report a number',
    'checkNavBtn': 'Check a number',
    'reportDisclaimer':
        'Reports are stored locally as unverified community submissions. '
            'They do not confirm that a number is malicious. '
            'Do not include private message content or personal data.',
    'checkDisclaimer':
        'A result of "no reports found" does not mean the number is safe. '
            'This lookup only checks the local dataset.',
    'mismatchWarning': 'Sender identity mismatch detected',
    'matchConfirmed': 'Sender identity matches known legitimate identifier',
  },
  AppLanguage.amharic: {
    'appTitle': 'የሳይበር ደህንነት ረዳት',
    'pageTitle': 'የብዙ ቋንቋ መልዕክቶችን ይተንትኑ',
    'subtitle':
        'አጠራጣሪ SMS፣ Telegram ወይም Telebirr መልዕክቶችን በእንግሊዝኛ፣ አማርኛ ወይም ድብልቅ ቋንቋ ይለጥፉ።',
    'hint':
        'ለምሳሌ፦ የእርስዎ telebirr ሂሳብ ታግዷል። PIN ቁጥርዎን በ http://cbe-verify.top/login ያስገቡ',
    'analyzeBtn': 'መልዕክቱን ይተንትኑ',
    'analyzingBtn': 'በመተንተን ላይ...',
    'emptyError': 'እባክዎ ለመተንተን መልዕክት ያስገቡ።',
    'connectError':
        'ከ backend አገልጋይ ጋር መገናኘት አልተቻለም። FastAPI እየሄደ መሆኑን ያረጋግጡ።',
    'resultsTitle': 'የትንተና ውጤቶች',
    'riskLevel': 'የአደጋ ደረጃ',
    'score': 'ነጥብ',
    'languageDetected': 'የተገኘ ቋንቋ',
    'recommendation': 'ምክረ ሃሳብ',
    'detectedLinks': 'የተገኙ አገናኞች',
    'detectedIndicators': 'የተገኙ የአደጋ ምልክቶች',
    'noDetail': 'ምንም ዝርዝር አልቀረበም።',
    'comingSoon': 'የአፋን ኦሮሞ ድጋፍ በቅርቡ ይመጣል!',
    'messageSource': 'ይህ ከየት መጣ? (አማራጭ)',
    'senderPhone': 'የላኪ ስልክ ቁጥር (አማራጭ)',
    'claimedSender': 'የተጠቀሰ ላኪ (ለምሳሌ 994፣ telebirr፣ CBE) (አማራጭ)',
    'claimedSenderHelp':
        'መልዕክቱ ኦፊሴላዊ ቁጥር ወይም አገልግሎት ነኝ ካለ፣ ለማረጋገጥ እዚህ ያስገቡ።',
    'senderIdentifier': 'የኢሜይል አድራሻ ወይም የላኪ መለያ (አማራጭ)',
    'uploadImage': 'ስክሪንሾት ይተንትኑ',
    'imageHelp': 'PNG ወይም JPEG፣ እስከ 5 MB። የእንግሊዝኛ OCR በbackend ይሰራል።',
    'imageUnavailable': 'የምስል OCR አሁን አይገኝም። Tesseract አልተጫነም።',
    'extractingText': 'ጽሑፍ በማውጣት ላይ...',
    'whyResult': 'የትንተና ማብራሪያዎች',
    'messageExplanation': 'የመልዕክት ቃላት',
    'urlExplanation': 'የURL ትንተና',
    'phoneReputation': 'የላኪ ቁጥር ሪፖርት',
    'numbersInMessage': 'በመልዕክቱ ውስጥ የተገኙ ስልክ ቁጥሮች',
    'senderVerification': 'የላኪ ማንነት ማረጋገጫ',
    'analysisLimits': 'ገደቦች',
    'analysisMethodRules': 'በህጎች የመልዕክትና URL ትንተና፤ ML ሞዴል አልነቃም።',
    'analysisMethodMl': 'በህጎችና በንቁ ML ሞዴል ትንተና።',
    'reports': 'ሪፖርት(ዎች)',
    'noPhoneReports':
        'ተዛማጅ ሪፖርት አልተገኘም። ይህ ቁጥሩ ደህንነቱ የተጠበቀ ነው ማለት አይደለም።',
    'sourceContext': 'የመልዕክት ምንጭ እንደ አውድ ብቻ ይጠቀማል፤ የአደጋ ነጥቡን አይቀይርም።',
    'sms': 'SMS',
    'whatsapp': 'WhatsApp',
    'telegram': 'Telegram',
    'email': 'ኢሜይል',
    'phoneCall': 'የስልክ ጥሪ',
    'other': 'ሌላ',
    'unknown': 'ያልታወቀ',
    'uploadTooLarge': 'ምስሉ 5 MB ወይም ከዚያ በታች መሆን አለበት።',
    'uploadBadFormat': 'የPNG ወይም JPEG ምስል ብቻ ይደገፋል።',
    'uploadEmpty': 'የተመረጠው ምስል ባዶ ነው።',
    'noOcrText': 'በምስሉ ውስጥ ሊነበብ የሚችል ጽሑፍ አልተገኘም።',
    'inputMethodOcr': 'በOCR የወጣ ጽሑፍ (ማስተካከል ይቻላል)',
    'cleanupFailed': 'ጊዜያዊ ምስሉን ማጥፋት አልተቻለም። ምስሉ አልተላከም።',
    'ocrResultTitle': 'የስክሪንሾት ትንተና',
    'ocrExtractedText': 'የወጣ ጽሑፍ',
    'ocrEditHint': 'የወጣውን ጽሑፍ ይፈትሹ ወይም ያስተካክሉ፣ ከዚያ ይተንትኑ።',
    'ocrAnalyzeBtn': 'የወጣውን ጽሑፍ ይተንትኑ',
    'ocrNumbersFound': 'በስክሪንሾቱ ውስጥ የተገኙ ስልክ ቁጥሮች',
    'tesseractMissing':
        'Tesseract OCR በአገልጋዩ ላይ አልተጫነም። ለስክሪንሾት ትንተና Tesseract ይጫኑ።',
    'reportTitle': 'አጠራጣሪ ቁጥር ሪፖርት ያድርጉ',
    'checkTitle': 'ስልክ ቁጥር ይፈትሹ',
    'reportBtn': 'ቁጥሩን ሪፖርት ያድርጉ',
    'checkBtn': 'ቁጥሩን ይፈትሹ',
    'reportingBtn': 'በማስገባት ላይ...',
    'checkingBtn': 'በመፈተሽ ላይ...',
    'phoneNumberField': 'ስልክ ቁጥር (ለምሳሌ 0911234567 ወይም +251911234567)',
    'phoneRequired': 'እባክዎ ስልክ ቁጥር ያስገቡ።',
    'categoriesLabel': 'የሪፖርት ምድቦች (ቢያንስ አንድ ይምረጡ)',
    'categoryRequired': 'እባክዎ ቢያንስ አንድ ምድብ ይምረጡ።',
    'evidenceLabel': 'መልዕክት ወይም ምክንያት (አማራጭ፣ እስከ 500 ቁምፊ)',
    'evidencePlaceholder': 'የደረሰዎትን ይግለጹ፤ የግል መረጃ አያካትቱ።',
    'reportSuccess': 'ሪፖርትዎ እንደ ያልተረጋገጠ የማህበረሰብ ሪፖርት ተመዝግቧል።',
    'reportUpdated': 'ነባር መዝገብ በሪፖርትዎ ተዘምኗል።',
    'checkResult': 'የፍለጋ ውጤት',
    'catScam': 'ማጭበርበር',
    'catSpam': 'ስፓም ጥሪዎች',
    'catPhishing': 'ማስገር',
    'catImpersonation': 'ማንነት ማስመሰል',
    'catMarketing': 'ያልተፈለገ ማስታወቂያ',
    'catOther': 'ሌላ',
    'reportNavBtn': 'ቁጥር ሪፖርት ያድርጉ',
    'checkNavBtn': 'ቁጥር ይፈትሹ',
    'reportDisclaimer':
        'ሪፖርቶች እንደ ያልተረጋገጠ የማህበረሰብ ሪፖርት ይቀመጣሉ። '
            'ቁጥሩ ጎጂ ነው ብለው አያረጋግጡም። '
            'የግል መልዕክት ወይም ሌሎች ሚስጥራዊ መረጃዎችን አያካትቱ።',
    'checkDisclaimer':
        '"ሪፖርት አልተገኘም" ማለት ቁጥሩ ደህንነቱ የተጠበቀ ነው ማለት አይደለም። '
            'ይህ ፍለጋ የአካባቢ ዳታሴቱን ብቻ ይፈትሻል።',
    'mismatchWarning': 'የላኪ ማንነት አለመዛመድ ተገኝቷል',
    'matchConfirmed': 'የላኪ ማንነት ከታወቀ ኦፊሴላዊ መለያ ጋር ይዛመዳል',
  },
  AppLanguage.oromoo: {},
};

// ignore: unused_element
String _t(AppLanguage lang, String key) =>
    _strings[lang]?[key] ?? _strings[AppLanguage.english]![key]!;

// ── Indicator / classification translation maps ──────────────────────────────

const Map<String, String> _indicatorAm = {
  'urgency': 'አስቸኳይነት',
  'fear_or_threat': 'ፍርሃት ወይም ማስፈራሪያ',
  'reward_bait': 'የሽልማት ማታለያ',
  'financial_reward': 'የገንዘብ ሽልማት ማታለያ',
  'credential_request': 'የምስጢር ቁጥር ጥያቄ',
  'financial_request': 'የገንዘብ ጥያቄ',
  'possible_impersonation': 'የማንነት ማስመሰል',
  'account_verification_request': 'የመለያ ማረጋገጫ ጥያቄ',
  'job_scam_indicator': 'የስራ ማጭበርበር ምልክት',
  'delivery_scam_indicator': 'የዕቃ ማድረስ ማጭበርበር ምልክት',
  'investment_scam_indicator': 'የኢንቨስትመንት ማጭበርበር ምልክት',
  'suspicious_call_to_action': 'አጠራጣሪ የድርጊት ጥሪ',
  'fake_account_suspension_warning': 'የሐሰት መለያ ማገድ ማስጠንቀቂያ',
  'credential_theft_attempt': 'የምስጢር ቁጥር ስርቆት ሙከራ',
  'advance_fee_scam_indicator': 'የቅድሚያ ክፍያ ማጭበርበር ምልክት',
  'sender_identity_mismatch': 'የላኪ ማንነት አለመዛመድ',
  'url_shortener': 'አጭር URL አገናኝ',
  'ip_address_url': 'IP አድራሻ URL',
  'excessive_subdomains': 'ከመጠን ያለፈ ንዑስ ጎራዎች',
  'url_contains_at_symbol': 'URL @ ምልክት ይዟል',
  'no_https': 'HTTPS የለም',
  'malformed_url': 'የተበላሸ URL',
  'suspicious_tld': 'አጠራጣሪ የጎራ ቅጥያ',
  'credential_path': 'የምስጢር ቁጥር መንገድ',
  'lookalike_domain': 'ተመሳሳይ ጎራ ስም',
  'punycode_or_unicode': 'Punycode ወይም Unicode ማደናገሪያ',
  'otp_request': 'የOTP ኮድ ጥያቄ',
};

const Map<String, String> _classificationAm = {
  'HIGH_RISK': 'ከፍተኛ አደጋ',
  'SUSPICIOUS': 'አጠራጣሪ',
  'SAFE': 'ደህንነቱ የተጠበቀ',
};

const Map<String, String> _detectedLangAm = {
  'ENGLISH': 'እንግሊዝኛ',
  'AMHARIC': 'አማርኛ',
  'MIXED': 'ድብልቅ',
  'UNKNOWN': 'ያልታወቀ',
};

const Map<String, String> _recommendationAm = {
  'TELEBIRR_SCAM':
      'የ6 አሃዝ telebirr PIN ወይም OTP ኮድዎን ከማንም ጋር አይጋሩ። ኦፊሴላዊ telebirr ሰራተኞች ምስጢር ቁጥርዎን አይጠይቁም።',
  'BANK_PHISHING':
      'ምንም አገናኞችን አይክፈቱ ወይም የግል መረጃ አይስጡ። ባንክዎን በቀጥታ በኦፊሴላዊ ስልክ ቁጥር ያነጋግሩ።',
  'CREDENTIAL_PHISHING':
      'ያልተረጋገጡ ድረ-ገጾች ላይ የይለፍ ቃልዎን አያስገቡ። ካስገቡ ወዲያውኑ ይቀይሩ።',
  'PRIZE_SCAM':
      'ያልጠበቁት ሽልማት የሚናገሩ መልዕክቶችን ችላ ይበሉ። ህጋዊ ድርጅቶች ቅድሚያ ክፍያ አይጠይቁም።',
  'JOB_SCAM': 'ስራ ለማግኘት ገንዘብ አይክፈሉ። ቅናሾችን በኦፊሴላዊ ቻናሎች ያረጋግጡ።',
  'DELIVERY_SCAM':
      'ባልታመኑ አገናኞች በኩል የማድረሻ ክፍያ አይፈጽሙ። ሁኔታን በቀጥታ በአቅራቢው ድረ-ገጽ ያረጋግጡ።',
  'ACCOUNT_TAKEOVER_ALERT':
      'ረጋ ይበሉ። የመለያዎን ሁኔታ በቀጥታ በኦፊሴላዊ መተግበሪያ ያረጋግጡ።',
  'SUSPICIOUS_LINK': 'ባልታወቁ አገናኞች ላይ ጠቅ ማድረግ ያስወግዱ።',
  'SOCIAL_ENGINEERING': 'ጥንቃቄ ያድርጉ። ማንኛውንም እርምጃ ከመውሰድዎ በፊት ላኪውን ያረጋግጡ።',
  'FINANCIAL_SCAM':
      'ያልታወቁ ሰዎች ለሚጠይቁት ክፍያ ምላሽ አይስጡ። ሁሉንም የገንዘብ ጥያቄዎች ያረጋግጡ።',
  'INVESTMENT_SCAM':
      'ከፍተኛ ትርፍ የሚቃዘኑ ቅናሾችን ያስወግዱ። ከማንኛውም ኢንቨስትመንት በፊት ባለሙያ ያማክሩ።',
  'IMPERSONATION':
      'ላኪው ማንነቱን ያረጋግጡ። ኦፊሴላዊ ድርጅቶች SMS በኩል ምስጢር ቁጥር አይጠይቁም።',
  'BENIGN': 'ምንም ዋና የአደጋ ምልክቶች አልተገኙም። መደበኛ ጥንቃቄዎችን ይቀጥሉ።',
};

String _translateIndicator(AppLanguage lang, String indicator) {
  if (lang != AppLanguage.amharic) {
    return indicator.replaceAll('_', ' ').toUpperCase();
  }
  return _indicatorAm[indicator] ?? indicator.replaceAll('_', ' ').toUpperCase();
}

String _translateClassification(AppLanguage lang, String raw) {
  if (lang != AppLanguage.amharic) return raw.replaceAll('_', ' ');
  return _classificationAm[raw] ?? raw.replaceAll('_', ' ');
}

String _translateDetectedLang(AppLanguage lang, String dl) {
  if (lang != AppLanguage.amharic) return dl;
  return _detectedLangAm[dl] ?? dl;
}

String _translateRecommendation(AppLanguage lang, String threatType) {
  if (lang != AppLanguage.amharic) return '';
  return _recommendationAm[threatType] ?? '';
}

// ── App root ─────────────────────────────────────────────────────────────────

class CyberSafetyApp extends StatefulWidget {
  const CyberSafetyApp({super.key});
  @override
  State<CyberSafetyApp> createState() => _CyberSafetyAppState();
}

class _CyberSafetyAppState extends State<CyberSafetyApp> {
  AppLanguage _language = AppLanguage.english;
  void _setLanguage(AppLanguage lang) => setState(() => _language = lang);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Multilingual Cyber-Safety Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF5C35CC),
          brightness: Brightness.light,
        ),
      ),
      home: HomeScreen(language: _language, onLanguageChange: _setLanguage),
    );
  }
}

// ── Home screen ───────────────────────────────────────────────────────────────

class HomeScreen extends StatefulWidget {
  final AppLanguage language;
  final ValueChanged<AppLanguage> onLanguageChange;
  const HomeScreen({
    super.key,
    required this.language,
    required this.onLanguageChange,
  });
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _textController = TextEditingController();
  final _senderPhoneController = TextEditingController();
  final _claimedSenderController = TextEditingController();
  final _senderIdentifierController = TextEditingController();
  final _imagePicker = ImagePicker();

  bool _isLoading = false;
  bool _isExtractingImage = false;
  String? _errorMessage;
  String? _imageError;
  String? _messageSource;
  final String _inputMethod = 'text';

  static const int _maxImageBytes = 5 * 1024 * 1024;

  String _t(String key) => _strings[widget.language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  void dispose() {
    _textController.dispose();
    _senderPhoneController.dispose();
    _claimedSenderController.dispose();
    _senderIdentifierController.dispose();
    super.dispose();
  }

  void _showComingSoon() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(_t('comingSoon')),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  String _sourceLabel(String source) {
    final key = switch (source) {
      'SMS' => 'sms',
      'WhatsApp' => 'whatsapp',
      'Telegram' => 'telegram',
      'Email' => 'email',
      'Phone call' => 'phoneCall',
      'Other' => 'other',
      _ => 'unknown',
    };
    return _t(key);
  }

  Future<void> _pickAndAnalyzeImage() async {
    if (_isLoading || _isExtractingImage) return;
    setState(() => _imageError = null);
    try {
      final image = await _imagePicker.pickImage(source: ImageSource.gallery);
      if (!mounted) return;
      if (image == null) return;

      setState(() => _isExtractingImage = true);
      late final Uint8List bytes;
      try {
        bytes = await image.readAsBytes();
      } finally {
        await cleanupPickedImage(image.path);
      }

      final ext = image.name.toLowerCase().split('.').last;
      if (!{'png', 'jpg', 'jpeg'}.contains(ext)) {
        setState(() => _imageError = _t('uploadBadFormat'));
        return;
      }
      if (bytes.isEmpty) {
        setState(() => _imageError = _t('uploadEmpty'));
        return;
      }
      if (bytes.length > _maxImageBytes) {
        setState(() => _imageError = _t('uploadTooLarge'));
        return;
      }

      final isPng = bytes.length >= 8 &&
          bytes[0] == 0x89 && bytes[1] == 0x50 && bytes[2] == 0x4e &&
          bytes[3] == 0x47 && bytes[4] == 0x0d && bytes[5] == 0x0a &&
          bytes[6] == 0x1a && bytes[7] == 0x0a;
      final isJpeg = bytes.length >= 3 &&
          bytes[0] == 0xff && bytes[1] == 0xd8 && bytes[2] == 0xff;
      if (!isPng && !isJpeg) {
        setState(() => _imageError = _t('uploadBadFormat'));
        return;
      }

      final contentType =
          isPng ? MediaType('image', 'png') : MediaType('image', 'jpeg');
      final request =
          http.MultipartRequest('POST', Uri.parse('$apiBaseUrl/analyze/image'))
            ..files.add(http.MultipartFile.fromBytes(
              'file',
              bytes,
              filename: image.name,
              contentType: contentType,
            ));

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);

      if (!mounted) return;

      if (response.statusCode == 503) {
        // Tesseract not installed — show dedicated guidance dialog
        await showDialog<void>(
          context: context,
          builder: (_) => AlertDialog(
            title: const Icon(Icons.camera_alt_outlined,
                size: 40, color: Colors.orange),
            content: Text(_t('tesseractMissing')),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('OK'),
              ),
            ],
          ),
        );
        return;
      }

      if (response.statusCode != 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() =>
            _imageError = body['detail'] as String? ?? _t('imageUnavailable'));
        return;
      }

      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final extractedText = payload['extracted_text'] as String? ?? '';
      if (extractedText.trim().isEmpty) {
        setState(() => _imageError = _t('noOcrText'));
        return;
      }

      // Navigate to the dedicated OCR result screen
      if (!mounted) return;
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => OcrResultScreen(
            payload: payload,
            language: widget.language,
            imageName: image.name,
          ),
        ),
      );
    } on ImageCleanupException {
      if (mounted) setState(() => _imageError = _t('cleanupFailed'));
    } catch (_) {
      if (mounted) setState(() => _imageError = _t('imageUnavailable'));
    } finally {
      if (mounted) setState(() => _isExtractingImage = false);
    }
  }

  Future<void> _analyzeMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty) {
      setState(() => _errorMessage = _t('emptyError'));
      return;
    }
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });
    try {
      final body = <String, dynamic>{
        'message': text,
        if (_messageSource != null) 'message_source': _messageSource,
        if (_senderPhoneController.text.trim().isNotEmpty)
          'sender_phone': _senderPhoneController.text.trim(),
        if (_claimedSenderController.text.trim().isNotEmpty)
          'claimed_sender': _claimedSenderController.text.trim(),
        if (_messageSource == 'Email' &&
            _senderIdentifierController.text.trim().isNotEmpty)
          'sender_identifier': _senderIdentifierController.text.trim(),
        'input_method': _inputMethod,
      };
      final response = await http.post(
        Uri.parse('$apiBaseUrl/analyze'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );
      if (response.statusCode == 200) {
        final result = jsonDecode(response.body) as Map<String, dynamic>;
        if (!mounted) return;
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) =>
                ResultScreen(result: result, language: widget.language),
          ),
        );
      } else {
        final err = jsonDecode(response.body) as Map<String, dynamic>;
        setState(
            () => _errorMessage = err['detail'] as String? ?? _t('connectError'));
      }
    } catch (_) {
      setState(() => _errorMessage = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: Text(_t('appTitle')),
        centerTitle: true,
        actions: [
          PopupMenuButton<AppLanguage>(
            icon: const Icon(Icons.language),
            tooltip: 'Language',
            onSelected: (lang) {
              if (lang == AppLanguage.oromoo) {
                _showComingSoon();
              } else {
                widget.onLanguageChange(lang);
              }
            },
            itemBuilder: (_) => [
              _langItem(AppLanguage.english, 'English', widget.language),
              _langItem(AppLanguage.amharic, 'አማርኛ', widget.language),
              PopupMenuItem(
                value: AppLanguage.oromoo,
                child: Row(children: [
                  const SizedBox(width: 26),
                  const Text('Afaan Oromoo'),
                  const SizedBox(width: 6),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade300,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text('soon',
                        style:
                            TextStyle(fontSize: 10, color: Colors.black54)),
                  ),
                ]),
              ),
            ],
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Icon(Icons.shield_outlined, size: 56, color: cs.primary),
            const SizedBox(height: 12),
            Text(_t('pageTitle'),
                textAlign: TextAlign.center,
                style:
                    const TextStyle(fontSize: 21, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(_t('subtitle'),
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.black54, fontSize: 13)),
            const SizedBox(height: 20),
            TextField(
              controller: _textController,
              maxLines: 5,
              decoration: InputDecoration(
                hintText: _t('hint'),
                border:
                    OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                errorText: _errorMessage,
              ),
            ),
            const SizedBox(height: 10),
            // Screenshot button
            OutlinedButton.icon(
              onPressed:
                  _isExtractingImage ? null : _pickAndAnalyzeImage,
              icon: _isExtractingImage
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.image_search),
              label: Text(_isExtractingImage
                  ? _t('extractingText')
                  : _t('uploadImage')),
            ),
            if (_imageError != null) ...[
              const SizedBox(height: 4),
              Text(_imageError!,
                  style: TextStyle(color: cs.error, fontSize: 13)),
            ],
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              initialValue: _messageSource,
              decoration: InputDecoration(
                labelText: _t('messageSource'),
                border:
                    OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
              items: [
                'SMS', 'WhatsApp', 'Telegram', 'Email', 'Phone call',
                'Other', 'Unknown'
              ]
                  .map((s) => DropdownMenuItem(
                      value: s, child: Text(_sourceLabel(s))))
                  .toList(),
              onChanged: (s) => setState(() => _messageSource = s),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _senderPhoneController,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(
                labelText: _t('senderPhone'),
                border:
                    OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _claimedSenderController,
              decoration: InputDecoration(
                labelText: _t('claimedSender'),
                helperText: _t('claimedSenderHelp'),
                helperMaxLines: 2,
                border:
                    OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            if (_messageSource == 'Email') ...[
              const SizedBox(height: 10),
              TextField(
                controller: _senderIdentifierController,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(
                  labelText: _t('senderIdentifier'),
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
            const SizedBox(height: 18),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _analyzeMessage,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 15),
                backgroundColor: cs.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
              icon: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.search),
              label: Text(
                  _isLoading ? _t('analyzingBtn') : _t('analyzeBtn'),
                  style: const TextStyle(fontSize: 16)),
            ),
            const SizedBox(height: 14),
            Row(children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) =>
                            CheckNumberScreen(language: widget.language)),
                  ),
                  icon: const Icon(Icons.search, size: 18),
                  label: Text(_t('checkNavBtn')),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) =>
                            ReportNumberScreen(language: widget.language)),
                  ),
                  icon: const Icon(Icons.flag_outlined, size: 18),
                  label: Text(_t('reportNavBtn')),
                ),
              ),
            ]),
          ],
        ),
      ),
    );
  }
}

PopupMenuItem<AppLanguage> _langItem(
    AppLanguage value, String label, AppLanguage current) {
  return PopupMenuItem(
    value: value,
    child: Row(children: [
      current == value
          ? const Icon(Icons.check, size: 18, color: Color(0xFF5C35CC))
          : const SizedBox(width: 18),
      const SizedBox(width: 8),
      Text(label),
    ]),
  );
}

// ── OCR Result screen ─────────────────────────────────────────────────────────

class OcrResultScreen extends StatefulWidget {
  final Map<String, dynamic> payload;
  final AppLanguage language;
  final String imageName;

  const OcrResultScreen({
    super.key,
    required this.payload,
    required this.language,
    required this.imageName,
  });

  @override
  State<OcrResultScreen> createState() => _OcrResultScreenState();
}

class _OcrResultScreenState extends State<OcrResultScreen> {
  late final TextEditingController _editController;
  bool _isReanalyzing = false;
  String? _reanalyzeError;

  String _t(String key) => _strings[widget.language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  void initState() {
    super.initState();
    _editController = TextEditingController(
      text: widget.payload['extracted_text'] as String? ?? '',
    );
  }

  @override
  void dispose() {
    _editController.dispose();
    super.dispose();
  }

  Future<void> _reanalyze() async {
    final text = _editController.text.trim();
    if (text.isEmpty) return;
    setState(() {
      _isReanalyzing = true;
      _reanalyzeError = null;
    });
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/analyze'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': text, 'input_method': 'image_ocr'}),
      );
      if (!mounted) return;
      if (response.statusCode == 200) {
        final result = jsonDecode(response.body) as Map<String, dynamic>;
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) =>
                ResultScreen(result: result, language: widget.language),
          ),
        );
      } else {
        final err = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() =>
            _reanalyzeError = err['detail'] as String? ?? _t('connectError'));
      }
    } catch (_) {
      setState(() => _reanalyzeError = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isReanalyzing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final numbersInImage =
        (widget.payload['numbers_in_image'] as List<dynamic>? ?? [])
            .cast<Map<String, dynamic>>();
    final analysis = widget.payload['analysis'] as Map<String, dynamic>?;

    return Scaffold(
      appBar: AppBar(title: Text(_t('ocrResultTitle'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Extracted text editor
            Text(_t('ocrExtractedText'),
                style: const TextStyle(
                    fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 6),
            TextField(
              controller: _editController,
              maxLines: 6,
              decoration: InputDecoration(
                helperText: _t('ocrEditHint'),
                helperMaxLines: 2,
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 10),
            if (_reanalyzeError != null)
              Text(_reanalyzeError!,
                  style: TextStyle(color: cs.error, fontSize: 13)),
            ElevatedButton.icon(
              onPressed: _isReanalyzing ? null : _reanalyze,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 13),
                backgroundColor: cs.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
              icon: _isReanalyzing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.search),
              label: Text(_isReanalyzing
                  ? _t('analyzingBtn')
                  : _t('ocrAnalyzeBtn')),
            ),

            // Phone numbers found in the screenshot
            if (numbersInImage.isNotEmpty) ...[
              const SizedBox(height: 20),
              Text(_t('ocrNumbersFound'),
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 15)),
              const SizedBox(height: 8),
              ...numbersInImage.map((entry) =>
                  _PhoneReputationCard(entry: entry, language: widget.language)),
            ],

            // Inline analysis from the backend
            if (analysis != null) ...[
              const SizedBox(height: 20),
              _AnalysisSummaryCard(
                  result: analysis, language: widget.language),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Result screen ─────────────────────────────────────────────────────────────

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;
  final AppLanguage language;

  const ResultScreen(
      {super.key, required this.result, required this.language});

  String _t(String key) => _strings[language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  Color _riskColor(String raw) {
    if (raw.contains('HIGH')) return Colors.red;
    if (raw.contains('SUSPICIOUS')) return Colors.orange;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    final rawClass = result['classification'] as String? ?? 'SAFE';
    final riskScore = result['risk_score'] ?? 0;
    final detectedLang = result['language'] as String? ?? 'UNKNOWN';
    final threatType = result['threat_type'] as String? ?? 'BENIGN';
    final recommendation =
        result['recommendation'] as String? ?? _t('noDetail');
    final indicators = List<String>.from(result['indicators'] ?? []);
    final urls = List<String>.from(result['urls'] ?? []);
    final explanations =
        Map<String, dynamic>.from(result['explanations'] as Map? ?? {});
    final reputation = result['phone_reputation'] == null
        ? null
        : Map<String, dynamic>.from(result['phone_reputation'] as Map);
    final senderVerification = result['sender_verification'] == null
        ? null
        : Map<String, dynamic>.from(result['sender_verification'] as Map);
    final numbersInMessage =
        (result['numbers_in_message'] as List<dynamic>? ?? [])
            .cast<Map<String, dynamic>>();
    final analysisMethod =
        result['analysis_method'] as String? ?? 'rules_and_urls';
    final messageSource = result['message_source'] as String?;

    final displayClass = _translateClassification(language, rawClass);
    final displayLang = _translateDetectedLang(language, detectedLang);
    final amRec = _translateRecommendation(language, threatType);
    final displayRec = amRec.isNotEmpty ? amRec : recommendation;
    final cardColor = _riskColor(rawClass);

    return Scaffold(
      appBar: AppBar(title: Text(_t('resultsTitle'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Risk summary card
            Card(
              color: cardColor.withValues(alpha: 0.08),
              shape: RoundedRectangleBorder(
                side: BorderSide(color: cardColor, width: 2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Expanded prevents long titles from causing text overflow
                        Expanded(
                          child: Text(
                            '${_t('riskLevel')}: $displayClass',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: cardColor,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Chip(
                          label: Text('${_t('score')}: $riskScore / 100',
                              style: const TextStyle(
                                  fontWeight: FontWeight.bold)),
                          backgroundColor: cardColor.withValues(alpha: 0.18),
                        ),
                      ],
                    ),
                    const Divider(height: 20),
                    Text('${_t('languageDetected')}: $displayLang',
                        style: const TextStyle(fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Sender identity mismatch banner
            if (senderVerification != null &&
                senderVerification['status'] == 'mismatch')
              _WarningBanner(
                icon: Icons.warning_amber_rounded,
                color: Colors.deepOrange,
                text: '${_t('mismatchWarning')}: '
                    '${senderVerification['explanation'] ?? ''}',
              ),
            if (senderVerification != null &&
                senderVerification['status'] == 'match')
              _WarningBanner(
                icon: Icons.verified_outlined,
                color: Colors.green,
                text: '${_t('matchConfirmed')}: '
                    '${senderVerification['explanation'] ?? ''}',
              ),

            const SizedBox(height: 4),
            Text(_t('recommendation'),
                style: const TextStyle(
                    fontSize: 17, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(displayRec,
                style: const TextStyle(fontSize: 15, height: 1.4)),
            const SizedBox(height: 16),

            // Explanations card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_t('whyResult'),
                        style: const TextStyle(
                            fontSize: 17, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 10),
                    _ExplanationRow(
                      title: _t('messageExplanation'),
                      text: explanations['message'] as String? ??
                          _t('noDetail'),
                    ),
                    _ExplanationRow(
                      title: _t('urlExplanation'),
                      text: explanations['urls'] as String? ?? _t('noDetail'),
                    ),
                    if (senderVerification != null &&
                        (explanations['sender_verification'] as String? ?? '')
                            .isNotEmpty)
                      _ExplanationRow(
                        title: _t('senderVerification'),
                        text: explanations['sender_verification'] as String,
                      ),
                    if (messageSource != null)
                      _ExplanationRow(
                        title: _t('messageSource'),
                        text:
                            '$messageSource. ${explanations['context'] as String? ?? _t('sourceContext')}',
                      ),
                    if (result['input_method'] == 'image_ocr')
                      _ExplanationRow(
                        title: _t('extractingText'),
                        text: explanations['ocr'] as String? ?? '',
                      ),
                    _ExplanationRow(
                      title: _t('analysisLimits'),
                      text: explanations['limitations'] as String? ??
                          (analysisMethod == 'rules_and_urls'
                              ? _t('analysisMethodRules')
                              : _t('analysisMethodMl')),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Sender phone reputation
            if (reputation != null &&
                reputation['status'] != 'not_provided') ...[
              _PhoneReputationCard(
                  entry: reputation, language: language),
              const SizedBox(height: 12),
            ],

            // Numbers found inside the message body
            if (numbersInMessage.isNotEmpty) ...[
              Text(_t('numbersInMessage'),
                  style: const TextStyle(
                      fontSize: 17, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ...numbersInMessage.map((e) =>
                  _PhoneReputationCard(entry: e, language: language)),
              const SizedBox(height: 12),
            ],

            // URLs
            if (urls.isNotEmpty) ...[
              Text(_t('detectedLinks'),
                  style: const TextStyle(
                      fontSize: 17, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ...urls.map((url) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(children: [
                      const Icon(Icons.link, color: Colors.red, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                          child: Text(url,
                              style: const TextStyle(
                                  fontSize: 13,
                                  color: Colors.red,
                                  fontWeight: FontWeight.w500))),
                    ]),
                  )),
              const SizedBox(height: 16),
            ],

            // Indicators
            if (indicators.isNotEmpty) ...[
              Text(_t('detectedIndicators'),
                  style: const TextStyle(
                      fontSize: 17, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ...indicators.map((ind) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(children: [
                      const Icon(Icons.warning_amber_rounded,
                          color: Colors.orange, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                          child: Text(
                              _translateIndicator(language, ind),
                              style: const TextStyle(fontSize: 14))),
                    ]),
                  )),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Shared widgets ────────────────────────────────────────────────────────────

class _AnalysisSummaryCard extends StatelessWidget {
  final Map<String, dynamic> result;
  final AppLanguage language;

  const _AnalysisSummaryCard(
      {required this.result, required this.language});

  Color _riskColor(String raw) {
    if (raw.contains('HIGH')) return Colors.red;
    if (raw.contains('SUSPICIOUS')) return Colors.orange;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    final rawClass = result['classification'] as String? ?? 'SAFE';
    final riskScore = result['risk_score'] ?? 0;
    final indicators = List<String>.from(result['indicators'] ?? []);
    final cardColor = _riskColor(rawClass);
    final displayClass = _translateClassification(language, rawClass);

    return Card(
      color: cardColor.withValues(alpha: 0.08),
      shape: RoundedRectangleBorder(
        side: BorderSide(color: cardColor, width: 1.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(displayClass,
                    style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: cardColor,
                        fontSize: 16)),
                Text('$riskScore / 100',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, color: cardColor)),
              ],
            ),
            if (indicators.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: indicators
                    .map((ind) => Chip(
                          label: Text(
                              _translateIndicator(language, ind),
                              style: const TextStyle(fontSize: 11)),
                          padding: EdgeInsets.zero,
                          visualDensity: VisualDensity.compact,
                          backgroundColor:
                              cardColor.withValues(alpha: 0.12),
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _PhoneReputationCard extends StatelessWidget {
  final Map<String, dynamic> entry;
  final AppLanguage language;

  const _PhoneReputationCard(
      {required this.entry, required this.language});

  String _t(String key) => _strings[language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  Widget build(BuildContext context) {
    final status = entry['status'] as String? ?? '';
    final phone = entry['phone_number'] as String?;
    final explanation =
        entry['explanation'] as String? ?? _t('noPhoneReports');
    final isReported = status == 'reported';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(
                isReported ? Icons.report_problem : Icons.phone_outlined,
                color: isReported ? Colors.orange : Colors.grey,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(phone ?? _t('phoneReputation'),
                  style: const TextStyle(fontWeight: FontWeight.w600)),
            ]),
            const SizedBox(height: 6),
            Text(explanation,
                style: const TextStyle(fontSize: 13, height: 1.35)),
            if (isReported) ...[
              const SizedBox(height: 6),
              Text(
                '${entry['report_count']} ${_t('reports')} · '
                '${entry['categories'] is List ? (entry['categories'] as List).join(', ') : ''}',
                style: const TextStyle(fontSize: 13),
              ),
              if (entry['verification_status'] is String)
                Text('Verification: ${entry['verification_status']}',
                    style: const TextStyle(fontSize: 12, color: Colors.black54)),
              if (entry['first_reported'] != null ||
                  entry['last_reported'] != null)
                Text(
                  'Reported: ${entry['first_reported'] ?? '?'} – '
                  '${entry['last_reported'] ?? '?'}',
                  style:
                      const TextStyle(fontSize: 12, color: Colors.black54),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _WarningBanner extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String text;

  const _WarningBanner(
      {required this.icon, required this.color, required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        border: Border.all(color: color),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 10),
          Expanded(
              child: Text(text,
                  style: TextStyle(
                      color: color,
                      fontSize: 13,
                      fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }
}

class _ExplanationRow extends StatelessWidget {
  final String title;
  final String text;

  const _ExplanationRow({required this.title, required this.text});

  @override
  Widget build(BuildContext context) {
    if (text.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 3),
          Text(text, style: const TextStyle(height: 1.35, fontSize: 13)),
        ],
      ),
    );
  }
}

// ── Check a Phone Number screen ───────────────────────────────────────────────

class CheckNumberScreen extends StatefulWidget {
  final AppLanguage language;
  const CheckNumberScreen({super.key, required this.language});
  @override
  State<CheckNumberScreen> createState() => _CheckNumberScreenState();
}

class _CheckNumberScreenState extends State<CheckNumberScreen> {
  final _phoneController = TextEditingController();
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _result;

  String _t(String key) => _strings[widget.language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  Future<void> _check() async {
    final phone = _phoneController.text.trim();
    if (phone.isEmpty) {
      setState(() => _error = _t('phoneRequired'));
      return;
    }
    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/check-number'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'phone_number': phone}),
      );
      if (response.statusCode == 200) {
        setState(() =>
            _result = jsonDecode(response.body) as Map<String, dynamic>);
      } else {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        setState(
            () => _error = body['detail'] as String? ?? _t('connectError'));
      }
    } catch (_) {
      setState(() => _error = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final result = _result;
    return Scaffold(
      appBar: AppBar(title: Text(_t('checkTitle'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_t('checkDisclaimer'),
                style:
                    const TextStyle(color: Colors.black54, fontSize: 13)),
            const SizedBox(height: 16),
            TextField(
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(
                labelText: _t('phoneNumberField'),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
                errorText: _error,
              ),
            ),
            const SizedBox(height: 14),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _check,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                backgroundColor: cs.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
              icon: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.search),
              label: Text(
                  _isLoading ? _t('checkingBtn') : _t('checkBtn')),
            ),
            if (result != null) ...[
              const SizedBox(height: 20),
              _PhoneReputationCard(
                  entry: result, language: widget.language),
            ],
          ],
        ),
      ),
    );
  }
}

// ── Report a Phone Number screen ──────────────────────────────────────────────

const _reportCategories = [
  ('scam', 'catScam'),
  ('phishing', 'catPhishing'),
  ('spam_calls', 'catSpam'),
  ('impersonation', 'catImpersonation'),
  ('unwanted_marketing', 'catMarketing'),
  ('other', 'catOther'),
];

class ReportNumberScreen extends StatefulWidget {
  final AppLanguage language;
  const ReportNumberScreen({super.key, required this.language});
  @override
  State<ReportNumberScreen> createState() => _ReportNumberScreenState();
}

class _ReportNumberScreenState extends State<ReportNumberScreen> {
  final _phoneController = TextEditingController();
  final _evidenceController = TextEditingController();
  final Set<String> _selectedCategories = {};
  bool _isLoading = false;
  String? _phoneError;
  String? _categoryError;
  String? _successMessage;
  String? _generalError;

  String _t(String key) => _strings[widget.language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  void dispose() {
    _phoneController.dispose();
    _evidenceController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final phone = _phoneController.text.trim();
    setState(() {
      _phoneError = phone.isEmpty ? _t('phoneRequired') : null;
      _categoryError =
          _selectedCategories.isEmpty ? _t('categoryRequired') : null;
      _successMessage = null;
      _generalError = null;
    });
    if (phone.isEmpty || _selectedCategories.isEmpty) return;

    setState(() => _isLoading = true);
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/report'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'phone_number': phone,
          'categories': _selectedCategories.toList(),
          'evidence_note': _evidenceController.text.trim(),
        }),
      );
      if (response.statusCode == 200) {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        final status = body['status'] as String? ?? '';
        setState(() {
          _successMessage =
              status == 'updated' ? _t('reportUpdated') : _t('reportSuccess');
          _phoneController.clear();
          _evidenceController.clear();
          _selectedCategories.clear();
        });
      } else {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() =>
            _generalError = body['detail'] as String? ?? _t('connectError'));
      }
    } catch (_) {
      setState(() => _generalError = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: Text(_t('reportTitle'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_t('reportDisclaimer'),
                style:
                    const TextStyle(color: Colors.black54, fontSize: 13)),
            const SizedBox(height: 16),
            TextField(
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(
                labelText: _t('phoneNumberField'),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
                errorText: _phoneError,
              ),
            ),
            const SizedBox(height: 16),
            Text(_t('categoriesLabel'),
                style: const TextStyle(fontWeight: FontWeight.w600)),
            if (_categoryError != null)
              Text(_categoryError!,
                  style: TextStyle(color: cs.error, fontSize: 12)),
            const SizedBox(height: 6),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: _reportCategories.map((entry) {
                final (value, labelKey) = entry;
                final selected = _selectedCategories.contains(value);
                return FilterChip(
                  label: Text(_t(labelKey)),
                  selected: selected,
                  onSelected: (on) => setState(() {
                    if (on) {
                      _selectedCategories.add(value);
                    } else {
                      _selectedCategories.remove(value);
                    }
                  }),
                );
              }).toList(),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _evidenceController,
              maxLines: 4,
              maxLength: 500,
              decoration: InputDecoration(
                labelText: _t('evidenceLabel'),
                hintText: _t('evidencePlaceholder'),
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
            ),
            if (_successMessage != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(_successMessage!,
                    style: const TextStyle(
                        color: Colors.green,
                        fontWeight: FontWeight.w600)),
              ),
            if (_generalError != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(_generalError!,
                    style: TextStyle(color: cs.error)),
              ),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _submit,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                backgroundColor: cs.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
              ),
              icon: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.flag_outlined),
              label: Text(
                  _isLoading ? _t('reportingBtn') : _t('reportBtn')),
            ),
          ],
        ),
      ),
    );
  }
}
