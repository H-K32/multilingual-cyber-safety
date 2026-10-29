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
    'daguBrand': 'Dagu',
    'daguMotto': 'Check Before You Trust.',
    'whyDaguTitle': 'Why Dagu?',
    'whyDaguBody':
        'Inspired by the Afar tradition of sharing and verifying information, Dagu represents our mission to help people recognize scams and phishing attempts before trusting or sharing suspicious information.',
    'whyDaguAfarNote': 'Afar Tradition of Information Sharing',
    'reportedNumbersTitle': 'Reported Numbers',
    'reportedNumbersSubtitle':
        'Community-reported suspicious phone numbers sorted by frequency.',
    'reportedTimes': 'Reported {count} times',
    'reportedOnce': 'Reported 1 time',
    'statusHighRisk': 'High Risk',
    'statusSuspicious': 'Suspicious',
    'statusReported': 'Reported',
    'statusSafe': 'Safe',
    'filterHint': 'Filter reported numbers...',
    'noReportedNumbersTitle': 'No numbers reported yet',
    'noReportedNumbersMsg':
        'Help protect the community by reporting suspicious numbers you receive.',
    'noMatchingNumbers': 'No reported numbers match your search.',
    'loadMore': 'Load more',
    'loadingMore': 'Loading more...',
    'refresh': 'Refresh',
    'retry': 'Retry',
    'reportNumberPrompt': 'Report a suspicious number',
    'communityReports': 'Community Reports',
    'searchReportedPlaceholder': 'Filter by number or category...',
    'checkThisNumber': 'Check this number',
    'totalReports': 'Total reported numbers',
    'statusLabel': 'Status',
    'lastReported': 'Last reported',
    'lookupPrompt': 'Check if a phone number has been reported as suspicious.',
    'disputeNumber': 'Dispute this number',
    'disputeAction': 'Report inaccurate status',
    'disputeTitle': 'Dispute Phone Reputation',
    'disputeDisclaimer':
        'Submitting a dispute queues this number for moderation review. It does not automatically delete existing reports or mark the number safe.',
    'disputeExplanation': 'Why is this status inaccurate?',
    'disputeExplanationHint':
        'Explain why this number is legitimate (e.g., official organization number, recent SIM reassignment) (min 10 characters).',
    'disputeContact': 'Contact information (optional)',
    'disputeContactHint':
        'Email or phone number if review updates are needed',
    'submitDispute': 'Submit Dispute',
    'submittingDispute': 'Submitting dispute...',
    'disputeSuccess': 'Dispute submitted successfully and queued for review.',
    'disputeFailed': 'Failed to submit dispute. Please try again.',
    'cancel': 'Cancel',
    'secOpsTitle': 'Security Operations',
    'secOpsSubtitle': 'Threat signals feed for authorized security analysts.',
    'socTokenPrompt': 'Enter SOC Analyst API Token',
    'connectSoc': 'Connect to SOC Feed',
    'disconnectSoc': 'Disconnect',
    'socDisclaimer':
        'Threat signals represent unverified community submissions and heuristic indicators. They do not constitute confirmed bank compromise.',
    'filterAll': 'All Signals',
    'filterSpike': '24h Spikes',
    'filterVolume': 'High Volume',
    'filterDisputed': 'Disputed',
    'filterCross': 'Cross-Category',
    'ackAlert': 'Acknowledge',
    'updateReview': 'Update Status',
    'noSecAlerts': 'No security alerts match the selected criteria.',
    'accessDenied': 'Invalid or expired analyst credentials. Access denied.',
    'orgRoleBadge': 'SOC Analyst',
    'statusNew': 'New',
    'statusAcknowledged': 'Acknowledged',
    'statusUnderReview': 'Under Review',
    'statusResolved': 'Resolved',
    'statusDismissed': 'Dismissed',
    'priorityCritical': 'CRITICAL',
    'priorityHigh': 'HIGH',
    'priorityMedium': 'MEDIUM',
    'priorityLow': 'LOW',
    'confidenceNotice': 'Heuristic community threat signal. Unverified.',
    'reviewStatusUpdated': 'Alert status updated successfully.',
    'analystNotesLabel': 'Analyst notes (optional)',
    'analystNotesHint': 'Add SOC investigation context or incident reference...',
    'saveStatus': 'Save Status',
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
    'daguBrand': 'ዳጉ',
    'daguMotto': 'ከማመንዎ በፊት ያረጋግጡ።',
    'whyDaguTitle': 'ለምን ዳጉ?',
    'whyDaguBody':
        'በአፋር መረጃ የመለዋወጥ እና የማረጋገጥ ባህል የተነሳሳው ዳጉ፣ ሰዎች አጠራጣሪ መረጃዎችን ከማመናቸው ወይም ከማጋራታቸው በፊት ማጭበርበሮችን እና ማስገር ሙከራዎችን እንዲለዩ የመርዳት ተልዕኳችንን ይወክላል።',
    'whyDaguAfarNote': 'የአፋር መረጃ የመለዋወጥ ባህል',
    'reportedNumbersTitle': 'የተዘገቡ ስልክ ቁጥሮች',
    'reportedNumbersSubtitle':
        'በማህበረሰቡ የተዘገቡ አጠራጣሪ ቁጥሮች፣ በብዛት ቅደም ተከተል የተቀመጡ።',
    'reportedTimes': '{count} ጊዜ ተዘግቧል',
    'reportedOnce': '1 ጊዜ ተዘግቧል',
    'statusHighRisk': 'ከፍተኛ አደጋ',
    'statusSuspicious': 'አጠራጣሪ',
    'statusReported': 'ተዘግቧል',
    'statusSafe': 'ደህንነቱ የተጠበቀ',
    'filterHint': 'የተዘገቡ ቁጥሮችን ይፈልጉ...',
    'noReportedNumbersTitle': 'እስካሁን የተዘገበ ቁጥር የለም',
    'noReportedNumbersMsg':
        'የሚደርስዎትን አጠራጣሪ ቁጥሮች ሪፖርት በማድረግ ማህበረሰቡን ይጠብቁ።',
    'noMatchingNumbers': 'ከፍለጋዎ ጋር የሚዛመድ የተዘገበ ቁጥር አልተገኘም።',
    'loadMore': 'ተጨማሪ አሳይ',
    'loadingMore': 'በመጫን ላይ...',
    'refresh': 'አድስ',
    'retry': 'እንደገና ሞክር',
    'reportNumberPrompt': 'አጠራጣሪ ቁጥር ሪፖርት ያድርጉ',
    'communityReports': 'የማህበረሰብ ሪፖርቶች',
    'searchReportedPlaceholder': 'በቁጥር ወይም በምድብ ፈልግ...',
    'checkThisNumber': 'ይህን ቁጥር ፈትሽ',
    'totalReports': 'ጠቅላላ የተዘገቡ ቁጥሮች',
    'statusLabel': 'ሁኔታ',
    'lastReported': 'ለመጨረሻ ጊዜ የተዘገበው',
    'lookupPrompt': 'ስልክ ቁጥሩ በማህበረሰቡ መዘገቡን ለማረጋገጥ እዚህ ያስገቡ።',
    'disputeNumber': 'ስለዚህ ቁጥር አቤቱታ ያቅርቡ',
    'disputeAction': 'ትክክል ያልሆነ ሁኔታን ሪፖርት አድርግ',
    'disputeTitle': 'የስልክ ቁጥር አቤቱታ',
    'disputeDisclaimer':
        'አቤቱታ ማቅረብ ቁጥሩን ለግምገማ ያቀርባል፤ ሪፖርቶችን ወዲያውኑ አያጠፋም ወይም ቁጥሩን ደህንነቱ የተጠበቀ አያደርገውም።',
    'disputeExplanation': 'ይህ ሁኔታ ለምን ትክክል አይደለም?',
    'disputeExplanationHint':
        'ይህ ቁጥር ለምን ትክክለኛ እንደሆነ ያብራሩ (ለምሳሌ የኦፊሴላዊ ድርጅት ቁጥር፣ አዲስ የተሰጠ ሲም) (ቢያንስ 10 ፊደላት)።',
    'disputeContact': 'የመገናኛ መረጃ (አማራጭ)',
    'disputeContactHint': 'ለግምገማ ክትትል የኢሜይል ወይም ስልክ ቁጥር',
    'submitDispute': 'አቤቱታውን አስገባ',
    'submittingDispute': 'አቤቱታ በማስገባት ላይ...',
    'disputeSuccess': 'አቤቱታዎ በተሳካ ሁኔታ ገብቷል እና ለግምገማ ተልኳል።',
    'disputeFailed': 'አቤቱታውን ማስገባት አልተቻለም። እባክዎ እንደገና ይሞክሩ።',
    'cancel': 'ሰርዝ',
    'secOpsTitle': 'የደህንነት ክትትል',
    'secOpsSubtitle': 'ለተፈቀደላቸው የደህንነት ተንታኞች የተዘጋጀ የአደጋ ምልክቶች ማዕከል',
    'socTokenPrompt': 'የደህንነት ተንታኝ መለያ ኮድ ያስገቡ',
    'connectSoc': 'ከደህንነት ማዕከል ጋር ተገናኝ',
    'disconnectSoc': 'ግንኙነት አቋርጥ',
    'socDisclaimer':
        'የቀረቡት መረጃዎች ያልተረጋገጡ የማህበረሰብ ሪፖርቶች እና የአደጋ ምልክቶች ናቸው፤ የተረጋገጠ የባንክ ማጭበርበር አይደሉም።',
    'filterAll': 'ሁሉም ምልክቶች',
    'filterSpike': 'የ24 ሰዓት ጭማሪዎች',
    'filterVolume': 'ከፍተኛ ሪፖርት',
    'filterDisputed': 'አቤቱታ የቀረበባቸው',
    'filterCross': 'የተለያዩ ምድቦች',
    'ackAlert': 'እውቅና ስጥ',
    'updateReview': 'ሁኔታውን ቀይር',
    'noSecAlerts': 'ምንም አዲስ የአደጋ ምልክት አልተገኘም።',
    'accessDenied': 'ትክክል ያልሆነ ወይም ጊዜው ያለፈበት መለያ። መግባት አልተፈቀደም።',
    'orgRoleBadge': 'የደህንነት ተንታኝ',
    'statusNew': 'አዲስ',
    'statusAcknowledged': 'እውቅና የተሰጠው',
    'statusUnderReview': 'በግምገማ ላይ',
    'statusResolved': 'የተፈታ',
    'statusDismissed': 'ውድቅ የተደረገ',
    'priorityCritical': 'እጅግ ከፍተኛ',
    'priorityHigh': 'ከፍተኛ',
    'priorityMedium': 'መካከለኛ',
    'priorityLow': 'ዝቅተኛ',
    'confidenceNotice': 'ያልተረጋገጠ የማህበረሰብ የአደጋ ምልክት።',
    'reviewStatusUpdated': 'የማስጠንቀቂያው ሁኔታ በተሳካ ሁኔታ ተዘምኗል።',
    'analystNotesLabel': 'የተንታኝ ማስታወሻ (አማራጭ)',
    'analystNotesHint': 'የምርመራ ማስታወሻ ወይም የማጣቀሻ ቁጥር ያክሉ...',
    'saveStatus': 'ሁኔታውን መዝግብ',
  },
  AppLanguage.oromoo: {
    'appTitle': 'Gargaaraa Nageenya Saayibarii',
    'pageTitle': 'Ergaawwan Afaan Hedduu Xiinxali',
    'subtitle':
        'Ergaawwan SMS, Telegram, ykn Telebirr shakkisiisoo afaan Ingiliffaa, Amaariffaa ykn makamaadhaan jiran asitti galchaa.',
    'hint':
        'fkn: Herregni keessan cufameera. Lakkoofsa PIN keessan http://cbe-verify.top/login irratti galchaa',
    'analyzeBtn': 'Ergaa Xiinxali',
    'analyzingBtn': 'Xiinxalamaa jira...',
    'emptyError': 'Maaloo ergaa xiinxalamu galchaa.',
    'connectError':
        'Gara sarvaritti walqunnamsiisuun hin danda\'amne. FastAPI hojjechaa jiraachuu mirkaneeffadhaa.',
    'resultsTitle': 'Bu\'aa Xiinxalaa',
    'riskLevel': 'Sadarkaa Balaa',
    'score': 'Qabxii',
    'languageDetected': 'Afaan Argame',
    'recommendation': 'Gorsa',
    'detectedLinks': 'Liinkiiwwan Argaman',
    'detectedIndicators': 'Mallattoolee Balaa Argaman',
    'noDetail': 'Ibsi hin kennamne.',
    'comingSoon': 'Deeggarsi Afaan Oromoo dhiyootti ni dhufa!',
    'messageSource': 'Kun eessaa dhufe? (filannoo)',
    'senderPhone': 'Lakkoofsa bilbilaa ergaa ergee (filannoo)',
    'claimedSender':
        'Eenyummaa ergaa kan jedhame (fkn: 994, telebirr, CBE) (filannoo)',
    'claimedSenderHelp':
        'Ergaan kun lakkoofsa mootummaa ykn tajaajila beekamaa irraati jedhee yoo dubbate, asitti galchaa.',
    'senderIdentifier': 'Teessoo Imeelii ykn beeksisaa ergaa (filannoo)',
    'uploadImage': 'Fakkii iskiriinii xiinxali',
    'imageHelp': 'PNG ykn JPEG, hanga 5 MB. OCR Ingiliffaa sarvarii irratti hojjeta.',
    'imageUnavailable':
        'Fakkii OCR fayyadamuun hin danda\'amne. Tesseract hin fe\'amne.',
    'extractingText': 'Barruu baasaa jira...',
    'whyResult': 'Ibsa xiinxalaa',
    'messageExplanation': 'Jecha ergaa',
    'urlExplanation': 'Xiinxala URL',
    'phoneReputation': 'Gabaasa lakkoofsa ergaa ergee',
    'numbersInMessage': 'Lakkoofsa bilbilaa ergaa keessatti argame',
    'senderVerification': 'Mirkaneessa eenyummaa ergaa',
    'analysisLimits': 'Daangaa',
    'analysisMethodRules': 'Seera irratti hundaa\'e; moodelli ML hin hojjetu.',
    'analysisMethodMl': 'Seeraa fi moodela ML irratti hundaa\'e.',
    'reports': 'gabaasa(wwan)',
    'noPhoneReports':
        'Gabaasni walgitu hin argamne. Kun lakkoofsi nagaadha jechuu miti.',
    'sourceContext': 'Maddi ergaa qabxii balaa hin jijjiiru.',
    'sms': 'SMS',
    'whatsapp': 'WhatsApp',
    'telegram': 'Telegram',
    'email': 'Imeelii',
    'phoneCall': 'Waamicha bilbilaa',
    'other': 'Kan biraa',
    'unknown': 'Hin beekamu',
    'uploadTooLarge': 'Fakkiin 5 MB gadi ta\'uu qaba.',
    'uploadBadFormat': 'Fakkii PNG fi JPEG qofatu deeggarama.',
    'uploadEmpty': 'Fakkiin filatame duwwaadha.',
    'noOcrText': 'Barruun dubbifamu fakkii keessatti hin argamne.',
    'inputMethodOcr': 'Barruu OCR (sirreeffamuu danda\'u)',
    'cleanupFailed': 'Fakkii yeroof qabame balleessuun hin danda\'amne.',
    'ocrResultTitle': 'Xiinxala Fakkii Iskiriinii',
    'ocrExtractedText': 'Barruu baafame',
    'ocrEditHint': 'Barruu baafame ilaalaa ykn sirreessaa, sana booda xiinxalaa.',
    'ocrAnalyzeBtn': 'Barruu baafame xiinxali',
    'ocrNumbersFound': 'Lakkoofsota fakkii keessatti argaman',
    'tesseractMissing': 'Tesseract OCR sarvarii irratti hin fe\'amne.',
    'reportTitle': 'Lakkoofsa Shakkisiisaa Gabaasi',
    'checkTitle': 'Lakkoofsa Bilbilaa Sakatta\'i',
    'reportBtn': 'Lakkoofsa Gabaasi',
    'checkBtn': 'Lakkoofsa Sakatta\'i',
    'reportingBtn': 'Galchaa jira...',
    'checkingBtn': 'Sakatta\'aa jira...',
    'phoneNumberField': 'Lakkoofsa bilbilaa (fkn: 0911234567 ykn +251911234567)',
    'phoneRequired': 'Maaloo lakkoofsa bilbilaa galchaa.',
    'categoriesLabel': 'Gareewwan gabaasaa (yoo xiqqaate tokko filadhaa)',
    'categoryRequired': 'Maaloo yoo xiqqaate garee tokko filadhaa.',
    'evidenceLabel': 'Ergaa ykn sababa (filannoo, hanga qubee 500)',
    'evidencePlaceholder':
        'Wanta isin qaqqabe ibsaa; odeeffannoo dhuunfaa hin dabalin.',
    'reportSuccess': 'Gabaasni keessan akka gabaasa hawaasaatti galmaa\'eera.',
    'reportUpdated': 'Galmeen duraanii gabaasa keessaniin haaromfameera.',
    'checkResult': 'Bu\'aa Sakatta\'iinsaa',
    'catScam': 'Gowwoomsaa',
    'catSpam': 'Waamicha Faayidaa Hin Qabne',
    'catPhishing': 'Manni Saamichaa (Phishing)',
    'catImpersonation': 'Eenyummaa Fakkeessuu',
    'catMarketing': 'Beeksisa Hin Barbaachisne',
    'catOther': 'Kan Biraa',
    'reportNavBtn': 'Lakkoofsa gabaasi',
    'checkNavBtn': 'Lakkoofsa sakatta\'i',
    'reportDisclaimer':
        'Gabaasawwan akka gabaasa hawaasaatti qabamu. Lakkoofsi sun balaa qabaachuu isaa hin mirkaneessan. Odeeffannoo dhuunfaa hin dabalin.',
    'checkDisclaimer':
        '"Gabaasni hin argamne" jechuun lakkoofsi sun nagaadha jechuu miti. Sakatta\'iinsi kun daataa jiru qofa sakatta\'a.',
    'mismatchWarning': 'Wal-dhabdeen eenyummaa ergaa argameera',
    'matchConfirmed': 'Eenyummaan ergaa beekamaa wajjin wal simata',
    'daguBrand': 'Dagu',
    'daguMotto': 'Osoo Hin Amanin Dura Mirkaneeffadhu.',
    'whyDaguTitle': 'Maaliif Dagu?',
    'whyDaguBody':
        'Aadaa Afaar kan odeeffannoo waljijjiiruu fi mirkaneessuu irraa kan kaka\'e, Daguun ergaa fi gowwoomsaa shakkisiisoo osoo hin amanin ykn hin qoodin dura akka adda baafatan gargaaruuf kan qophaa\'edha.',
    'whyDaguAfarNote': 'Aadaa Afaar Odeeffannoo Waljijjiiruu',
    'reportedNumbersTitle': 'Lakkoofsota Gabaafaman',
    'reportedNumbersSubtitle':
        'Lakkoofsota bilbilaa shakkisiisoo hawaasaan gabaafaman kan baay\'inaan tarreeffaman.',
    'reportedTimes': 'Yeroo {count} gabaafame',
    'reportedOnce': 'Yeroo 1 gabaafame',
    'statusHighRisk': 'Balaa Ol\'aanaa',
    'statusSuspicious': 'Shakkisiisaa',
    'statusReported': 'Gabaafameera',
    'statusSafe': 'Nagaadha',
    'filterHint': 'Lakkoofsota gabaafaman barbaadi...',
    'noReportedNumbersTitle': 'Lakkoofsi gabaafame hin jiru',
    'noReportedNumbersMsg':
        'Lakkoofsota shakkisiisoo gabaasuun hawaasa eegaa.',
    'noMatchingNumbers': 'Lakkoofsi barbaadame hin argamne.',
    'loadMore': 'Dabalata fidi',
    'loadingMore': 'Fidamaa jira...',
    'refresh': 'Haaromsi',
    'retry': 'Irra deebi\'ii yaali',
    'reportNumberPrompt': 'Lakkoofsa shakkisiisaa gabaasi',
    'communityReports': 'Gabaasa Hawaasaa',
    'searchReportedPlaceholder': 'Lakkoofsaan ykn gareen barbaadi...',
    'checkThisNumber': 'Lakkoofsa kana sakatta\'i',
    'totalReports': 'Ida\'ama lakkoofsota gabaafamanii',
    'statusLabel': 'Haala',
    'lastReported': 'Gabaasa dhihoo',
    'lookupPrompt': 'Lakkoofsi bilbilaa gabaafamuu isaa sakatta\'aa.',
    'disputeNumber': 'Lakkoofsa kana irratti mormii dhiyeessi',
    'disputeAction': 'Haala dogoggoraa gabaasi',
    'disputeTitle': 'Mormii Gabaasa Bilbilaa',
    'disputeDisclaimer':
        'Mormii dhiyeessuun lakkoofsa kana qorannoof dhiyeessa; gabaasawwan battalatti hin balleessu ykn nagaa hin taasisu.',
    'disputeExplanation': 'Haalli kun maaliif dogoggora ta\'e?',
    'disputeExplanationHint':
        'Maaliif lakkoofsi kun sirrii akka ta\'e ibsaa (fkn lakkoofsa dhaabbata mootummaa, simii haarawa) (yoo xiqqaate qubee 10).',
    'disputeContact': 'Odeeffannoo walqunnamtii (filannoo)',
    'disputeContactHint': 'Imeelii ykn lakkoofsa bilbilaa (filannoo)',
    'submitDispute': 'Mormii Galchi',
    'submittingDispute': 'Mormii galchaa jira...',
    'disputeSuccess': 'Mormiin keessan milkaa\'inaan galmaa\'eera.',
    'disputeFailed': 'Mormii galchuun hin danda\'amne. Maaloo irra deebi\'aa yaalaa.',
    'cancel': 'Dhiisi',
    'secOpsTitle': 'Hojii Nageenyaa',
    'secOpsSubtitle': 'Ergaawwan balaa ogeessota nageenyaa hayyamamaniif qophaa\'e.',
    'socTokenPrompt': 'Koodii Mallattoo Ogeessaa Galchaa',
    'connectSoc': 'Gara SOCtti Qunnamaa',
    'disconnectSoc': 'Addaan Kuti',
    'socDisclaimer':
        'Mallattooleen kun gabaasa hawaasaa hin mirkanoofnee fi agarsiistuu balaati. Hanqina ykn miidhaa baankii mirkanaa\'e hin agarsiisan.',
    'filterAll': 'Mallattoolee Hundaa',
    'filterSpike': 'Gabaasa Yeroo Gabaabaa (24h)',
    'filterVolume': 'Baay\'ina Ol\'aanaa',
    'filterDisputed': 'Kan Mormame',
    'filterCross': 'Gareewwan Adda Addaa',
    'ackAlert': 'Beekamtii Kenni',
    'updateReview': 'Haala Jijjiiri',
    'noSecAlerts': 'Balaan filatame wajjin wal simu hin argamne.',
    'accessDenied': 'Koodiin sirrii miti ykn yeroon isaa darbeera.',
    'orgRoleBadge': 'Ogeessa Nageenyaa (SOC)',
    'statusNew': 'Haaraa',
    'statusAcknowledged': 'Beekamtii Kan Argate',
    'statusUnderReview': 'Qorannoo Irra Kan Jiru',
    'statusResolved': 'Kan Furame',
    'statusDismissed': 'Kan Dhiifame',
    'priorityCritical': 'Balaa Cimaa',
    'priorityHigh': 'Balaa Ol\'aanaa',
    'priorityMedium': 'Giddu-galeessa',
    'priorityLow': 'Gadi-aanaa',
    'confidenceNotice': 'Agarsiistuu balaa hawaasaa hin mirkanoofne.',
    'reviewStatusUpdated': 'Haalli balaa milkaa\'inaan haaromfameera.',
    'analystNotesLabel': 'Yaada ogeessaa (filannoo)',
    'analystNotesHint': 'Yaada qorannoo dabalataa galchaa...',
    'saveStatus': 'Haala Galmeessi',
  },
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

String _translateCategory(AppLanguage lang, String cat) {
  final key = switch (cat.toLowerCase().trim()) {
    'scam' => 'catScam',
    'phishing' => 'catPhishing',
    'spam' || 'spam_calls' => 'catSpam',
    'impersonation' => 'catImpersonation',
    'marketing' || 'unwanted_marketing' => 'catMarketing',
    _ => 'catOther',
  };
  return _strings[lang]?[key] ?? _strings[AppLanguage.english]?[key] ?? cat;
}

String _translateRiskStatus(AppLanguage lang, String rawStatus) {
  final normalized = rawStatus.toUpperCase().replaceAll(' ', '_');
  if (lang == AppLanguage.amharic) {
    return switch (normalized) {
      'HIGH_RISK' => _strings[AppLanguage.amharic]!['statusHighRisk']!,
      'SUSPICIOUS' => _strings[AppLanguage.amharic]!['statusSuspicious']!,
      'REPORTED' => _strings[AppLanguage.amharic]!['statusReported']!,
      'SAFE' => _strings[AppLanguage.amharic]!['statusSafe']!,
      _ => rawStatus,
    };
  }
  return switch (normalized) {
    'HIGH_RISK' => 'High Risk',
    'SUSPICIOUS' => 'Suspicious',
    'REPORTED' => 'Reported',
    'SAFE' => 'Safe',
    _ => rawStatus,
  };
}

String _formatDate(String? isoString) {
  if (isoString == null || isoString.isEmpty) return '';
  try {
    final dt = DateTime.parse(isoString);
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
  } catch (_) {
    return isoString.split('T').first;
  }
}

// ── Responsive Layout Container ──────────────────────────────────────────────

class ResponsiveContainer extends StatelessWidget {
  final Widget child;
  final double maxWidth;

  const ResponsiveContainer({
    super.key,
    required this.child,
    this.maxWidth = 720,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: child,
      ),
    );
  }
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
      title: 'Dagu — Multilingual Cyber-Safety',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1E40AF),
          primary: const Color(0xFF1E40AF),
          secondary: const Color(0xFF0D9488),
          surface: Colors.white,
          brightness: Brightness.light,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
            side: BorderSide(color: Colors.grey.shade200, width: 1),
          ),
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
          IconButton(
            icon: const Icon(Icons.admin_panel_settings_outlined),
            tooltip: _t('secOpsTitle'),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) =>
                    SecurityOperationsScreen(language: widget.language),
              ),
            ),
          ),
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
      body: ResponsiveContainer(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _DaguHeroCard(language: widget.language),
              Icon(Icons.shield_outlined, size: 48, color: cs.primary),
              const SizedBox(height: 10),
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
            const SizedBox(height: 12),
            Center(
              child: TextButton.icon(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        SecurityOperationsScreen(language: widget.language),
                  ),
                ),
                icon: const Icon(Icons.shield_outlined, size: 16),
                label: Text(
                  _t('secOpsTitle'),
                  style: const TextStyle(fontSize: 13),
                ),
              ),
            ),
          ],
        ),
      ),
      ),
    );
  }
}

class _DaguHeroCard extends StatelessWidget {
  final AppLanguage language;
  const _DaguHeroCard({required this.language});

  String _t(String key) =>
      _strings[language]?[key] ?? _strings[AppLanguage.english]![key]!;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFF1E40AF).withValues(alpha: 0.08),
            const Color(0xFF3B82F6).withValues(alpha: 0.03),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2563EB).withValues(alpha: 0.2)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E40AF),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.shield, color: Colors.white, size: 22),
              ),
              const SizedBox(width: 10),
              Text(
                _t('daguBrand'),
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.1,
                  color: Color(0xFF1E3A8A),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '“${_t('daguMotto')}”',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              fontStyle: FontStyle.italic,
              color: Color(0xFF2563EB),
            ),
          ),
          const SizedBox(height: 8),
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: EdgeInsets.zero,
              leading: const Icon(Icons.info_outline,
                  size: 20, color: Color(0xFF2563EB)),
              title: Text(
                _t('whyDaguTitle'),
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1E3A8A),
                ),
              ),
              children: [
                Padding(
                  padding: const EdgeInsets.only(top: 4, bottom: 6),
                  child: Text(
                    _t('whyDaguBody'),
                    style: const TextStyle(
                      fontSize: 13,
                      height: 1.45,
                      color: Colors.black87,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
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
      body: ResponsiveContainer(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
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

            if (analysis != null) ...[
              const SizedBox(height: 20),
              _AnalysisSummaryCard(
                  result: analysis, language: widget.language),
            ],
          ],
        ),
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
      body: ResponsiveContainer(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
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

class PhoneReputationCard extends StatelessWidget {
  final Map<String, dynamic> entry;
  final AppLanguage language;

  const PhoneReputationCard(
      {super.key, required this.entry, required this.language});

  String _t(String key) => _strings[language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  Widget build(BuildContext context) {
    final status = entry['status'] as String? ?? '';
    final phone = entry['phone_number'] as String?;
    final explanation =
        entry['explanation'] as String? ?? _t('noPhoneReports');
    final isReported = status == 'reported';
    final reportCount = entry['report_count'] as int? ?? (isReported ? 1 : 0);
    final categories = entry['categories'] is List
        ? List<String>.from(entry['categories'])
        : <String>[];
    final verification = entry['verification_status'] as String?;

    final (cardColor, riskTitle) = isReported
        ? (reportCount >= 5
            ? (Colors.red, _t('statusHighRisk'))
            : (Colors.orange, _t('statusSuspicious')))
        : (Colors.green, _t('statusSafe'));

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: cardColor.withValues(alpha: 0.4), width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isReported ? Icons.warning_amber_rounded : Icons.verified_user_outlined,
                  color: cardColor,
                  size: 24,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    phone ?? _t('phoneReputation'),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: cardColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: cardColor.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    riskTitle,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: cardColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(explanation,
                style: const TextStyle(fontSize: 13.5, height: 1.4)),
            if (isReported) ...[
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: cardColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      reportCount == 1
                          ? _t('reportedOnce')
                          : _t('reportedTimes').replaceAll('{count}', '$reportCount'),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: cardColor,
                      ),
                    ),
                  ),
                  ...categories.map((c) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.grey.shade300),
                        ),
                        child: Text(
                          _translateCategory(language, c),
                          style: TextStyle(
                            fontSize: 11.5,
                            color: Colors.grey.shade800,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      )),
                ],
              ),
              if (verification != null && verification.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text('Verification: $verification',
                    style: const TextStyle(fontSize: 12, color: Colors.black54)),
              ],
              if (entry['first_reported'] != null ||
                  entry['last_reported'] != null) ...[
                const SizedBox(height: 4),
                Text(
                  'Reported: ${_formatDate(entry['first_reported'] as String?)} – '
                  '${_formatDate(entry['last_reported'] as String?)}',
                  style: const TextStyle(fontSize: 12, color: Colors.black54),
                ),
              ],
              const SizedBox(height: 10),
              const Divider(height: 1),
              const SizedBox(height: 6),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: () => _openDisputeModal(
                    context,
                    phone ?? entry['phone_e164'] as String? ?? '',
                  ),
                  icon: const Icon(Icons.flag_outlined, size: 16),
                  label: Text(
                    _t('disputeAction'),
                    style: const TextStyle(fontSize: 12),
                  ),
                  style: TextButton.styleFrom(
                    foregroundColor: Colors.grey.shade700,
                    visualDensity: VisualDensity.compact,
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _openDisputeModal(BuildContext context, String rawPhone) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _DisputeModalSheet(
        phoneNumber: rawPhone,
        language: language,
      ),
    );
  }
}

typedef _PhoneReputationCard = PhoneReputationCard;

class _DisputeModalSheet extends StatefulWidget {
  final String phoneNumber;
  final AppLanguage language;

  const _DisputeModalSheet({
    required this.phoneNumber,
    required this.language,
  });

  @override
  State<_DisputeModalSheet> createState() => _DisputeModalSheetState();
}

class _DisputeModalSheetState extends State<_DisputeModalSheet> {
  final _formKey = GlobalKey<FormState>();
  final _explanationController = TextEditingController();
  final _contactController = TextEditingController();

  bool _isSubmitting = false;
  String? _errorMessage;
  bool _submittedSuccess = false;

  String _t(String key) =>
      _strings[widget.language]?[key] ?? _strings[AppLanguage.english]![key]!;

  @override
  void dispose() {
    _explanationController.dispose();
    _contactController.dispose();
    super.dispose();
  }

  Future<void> _submitDispute() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
      _errorMessage = null;
    });

    final body = {
      'phone_number': widget.phoneNumber,
      'explanation': _explanationController.text.trim(),
      if (_contactController.text.trim().isNotEmpty)
        'contact_info': _contactController.text.trim(),
    };

    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/dispute'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(body),
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        setState(() {
          _isSubmitting = false;
          _submittedSuccess = true;
        });
      } else {
        String err = _t('disputeFailed');
        try {
          final resData = jsonDecode(response.body);
          if (resData is Map && resData['detail'] != null) {
            err = resData['detail'].toString();
          }
        } catch (_) {}
        setState(() {
          _isSubmitting = false;
          _errorMessage = err;
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isSubmitting = false;
        _errorMessage = _t('disputeFailed');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + bottomInset),
      child: SingleChildScrollView(
        child: _submittedSuccess
            ? Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const SizedBox(height: 10),
                  const Icon(Icons.check_circle_outline,
                      color: Colors.green, size: 56),
                  const SizedBox(height: 12),
                  Text(
                    _t('disputeSuccess'),
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _t('disputeDisclaimer'),
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('OK'),
                  ),
                ],
              )
            : Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.flag_outlined,
                            color: Colors.amber, size: 24),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            _t('disputeTitle'),
                            style: const TextStyle(
                                fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: () => Navigator.of(context).pop(),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      widget.phoneNumber,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey.shade800,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.amber.shade300),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.info_outline,
                              color: Colors.amber.shade900, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _t('disputeDisclaimer'),
                              style: TextStyle(
                                fontSize: 12.5,
                                color: Colors.amber.shade900,
                                height: 1.35,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (_errorMessage != null) ...[
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Text(
                          _errorMessage!,
                          style: TextStyle(
                              color: Colors.red.shade800, fontSize: 12.5),
                        ),
                      ),
                    ],
                    const SizedBox(height: 14),
                    Text(
                      _t('disputeExplanation'),
                      style: const TextStyle(
                          fontSize: 13.5, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _explanationController,
                      minLines: 3,
                      maxLines: 5,
                      maxLength: 1000,
                      decoration: InputDecoration(
                        hintText: _t('disputeExplanationHint'),
                        hintStyle: TextStyle(
                            fontSize: 12.5, color: Colors.grey.shade500),
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8)),
                      ),
                      validator: (val) {
                        final trimmed = val?.trim() ?? '';
                        if (trimmed.length < 10) {
                          return 'Please provide at least 10 characters.';
                        }
                        if (trimmed.length > 1000) {
                          return 'Explanation cannot exceed 1000 characters.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 10),
                    Text(
                      _t('disputeContact'),
                      style: const TextStyle(
                          fontSize: 13.5, fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _contactController,
                      maxLength: 254,
                      decoration: InputDecoration(
                        hintText: _t('disputeContactHint'),
                        hintStyle: TextStyle(
                            fontSize: 12.5, color: Colors.grey.shade500),
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: _isSubmitting
                              ? null
                              : () => Navigator.of(context).pop(),
                          child: Text(_t('cancel')),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: _isSubmitting ? null : _submitDispute,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.deepOrange,
                            foregroundColor: Colors.white,
                          ),
                          child: _isSubmitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : Text(_t('submitDispute')),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
      ),
    );
  }
}


class _ReportedNumberCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final AppLanguage language;
  final VoidCallback? onTap;

  const _ReportedNumberCard({
    required this.item,
    required this.language,
    this.onTap,
  });

  String _t(String key) =>
      _strings[language]?[key] ?? _strings[AppLanguage.english]![key]!;

  @override
  Widget build(BuildContext context) {
    final maskedPhone = item['masked_phone'] as String? ?? 'Unknown';
    final reportCount = item['report_count'] as int? ?? 1;
    final riskLevel = (item['risk_level'] as String? ?? 'REPORTED').toUpperCase();
    final riskStatus = item['risk_status'] as String? ?? 'Reported';
    final categories = List<String>.from(item['categories'] ?? []);
    final lastReported = item['last_reported'] as String?;

    final (statusColor, statusBg, statusIcon) = switch (riskLevel) {
      'HIGH_RISK' => (
        const Color(0xFFDC2626),
        const Color(0xFFFEF2F2),
        Icons.gpp_bad_rounded,
      ),
      'SUSPICIOUS' => (
        const Color(0xFFD97706),
        const Color(0xFFFFFBEB),
        Icons.warning_amber_rounded,
      ),
      _ => (
        const Color(0xFF2563EB),
        const Color(0xFFEFF6FF),
        Icons.info_outline_rounded,
      ),
    };

    final translatedStatus = _translateRiskStatus(language, riskStatus);
    final countText = reportCount == 1
        ? _t('reportedOnce')
        : _t('reportedTimes').replaceAll('{count}', '$reportCount');

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: statusColor.withValues(alpha: 0.25), width: 1.2),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Row: Masked phone number + Status badge
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Icon(Icons.phone_android, size: 20, color: statusColor),
                      const SizedBox(width: 8),
                      Text(
                        maskedPhone,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusBg,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: statusColor.withValues(alpha: 0.5)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(statusIcon, size: 14, color: statusColor),
                        const SizedBox(width: 4),
                        Text(
                          translatedStatus,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: statusColor,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              // Middle Row: Visual indicator of report count
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.report_problem, size: 14, color: statusColor),
                        const SizedBox(width: 5),
                        Text(
                          countText,
                          style: TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w700,
                            color: statusColor,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (lastReported != null) ...[
                    const Spacer(),
                    Text(
                      '${_t('lastReported')}: ${_formatDate(lastReported)}',
                      style: TextStyle(fontSize: 11.5, color: Colors.grey.shade600),
                    ),
                  ],
                ],
              ),
              // Bottom Row: Category Chips
              if (categories.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: categories.map((cat) {
                    final translatedCat = _translateCategory(language, cat);
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Text(
                        translatedCat,
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.grey.shade800,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ],
          ),
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
  final _filterController = TextEditingController();

  bool _isChecking = false;
  String? _checkError;
  Map<String, dynamic>? _checkResult;

  // Reported Numbers state
  final List<Map<String, dynamic>> _reportedList = [];
  bool _isLoadingReported = false;
  bool _isLoadingMore = false;
  String? _reportedError;
  int _totalReported = 0;
  bool _hasMoreReported = false;
  String _activeFilter = '';

  String _t(String key) => _strings[widget.language]?[key] ??
      _strings[AppLanguage.english]![key]!;

  @override
  void initState() {
    super.initState();
    _loadReportedNumbers(refresh: true);
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _filterController.dispose();
    super.dispose();
  }

  Future<void> _check([String? overridePhone]) async {
    final phone = (overridePhone ?? _phoneController.text).trim();
    if (phone.isEmpty) {
      setState(() => _checkError = _t('phoneRequired'));
      return;
    }
    if (overridePhone != null) {
      _phoneController.text = overridePhone;
    }
    setState(() {
      _isChecking = true;
      _checkError = null;
      _checkResult = null;
    });
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/check-number'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'phone_number': phone}),
      );
      if (!mounted) return;
      if (response.statusCode == 200) {
        setState(() =>
            _checkResult = jsonDecode(response.body) as Map<String, dynamic>);
      } else {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        setState(
            () => _checkError = body['detail'] as String? ?? _t('connectError'));
      }
    } catch (_) {
      if (mounted) setState(() => _checkError = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isChecking = false);
    }
  }

  Future<void> _loadReportedNumbers({bool refresh = false, String? search}) async {
    if (refresh) {
      setState(() {
        _isLoadingReported = true;
        _reportedError = null;
      });
    } else {
      if (_isLoadingMore || !_hasMoreReported) return;
      setState(() => _isLoadingMore = true);
    }

    final offset = refresh ? 0 : _reportedList.length;
    final query = search ?? _activeFilter;
    final uri = Uri.parse('$apiBaseUrl/reported-numbers').replace(
      queryParameters: {
        'limit': '10',
        'offset': '$offset',
        if (query.isNotEmpty) 'search': query,
      },
    );

    try {
      final response = await http.get(uri);
      if (!mounted) return;
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final items = (data['items'] as List<dynamic>? ?? [])
            .cast<Map<String, dynamic>>();
        setState(() {
          _totalReported = data['total'] as int? ?? 0;
          _hasMoreReported = data['has_more'] as bool? ?? false;
          if (refresh) {
            _reportedList
              ..clear()
              ..addAll(items);
          } else {
            _reportedList.addAll(items);
          }
        });
      } else {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        setState(() =>
            _reportedError = body['detail'] as String? ?? _t('connectError'));
      }
    } catch (_) {
      if (mounted) setState(() => _reportedError = _t('connectError'));
    } finally {
      if (mounted) {
        setState(() {
          _isLoadingReported = false;
          _isLoadingMore = false;
        });
      }
    }
  }

  Future<void> _openReportScreen() async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ReportNumberScreen(language: widget.language),
      ),
    );
    if (mounted) {
      _loadReportedNumbers(refresh: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final checkResult = _checkResult;

    return Scaffold(
      appBar: AppBar(
        title: Text(_t('checkTitle')),
        actions: [
          IconButton(
            icon: const Icon(Icons.flag_outlined),
            tooltip: _t('reportNavBtn'),
            onPressed: _openReportScreen,
          ),
        ],
      ),
      body: ResponsiveContainer(
        child: RefreshIndicator(
          onRefresh: () => _loadReportedNumbers(refresh: true),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Top Search / Check Section
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade50,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: Colors.grey.shade200),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.search, size: 20, color: cs.primary),
                          const SizedBox(width: 8),
                          Text(
                            _t('checkTitle'),
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _t('checkDisclaimer'),
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 12.5),
                      ),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        decoration: InputDecoration(
                          labelText: _t('phoneNumberField'),
                          prefixIcon: const Icon(Icons.phone_outlined),
                          suffixIcon: _phoneController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear, size: 18),
                                  onPressed: () {
                                    _phoneController.clear();
                                    setState(() => _checkResult = null);
                                  },
                                )
                              : null,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          errorText: _checkError,
                        ),
                        onChanged: (_) => setState(() {}),
                        onSubmitted: (_) => _check(),
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton.icon(
                        onPressed: _isChecking ? null : () => _check(),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 13),
                          backgroundColor: cs.primary,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                        icon: _isChecking
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.search),
                        label: Text(
                          _isChecking ? _t('checkingBtn') : _t('checkBtn'),
                          style: const TextStyle(fontSize: 15),
                        ),
                      ),
                    ],
                  ),
                ),

                // Search result card
                if (checkResult != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    _t('checkResult'),
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  _PhoneReputationCard(
                    entry: checkResult,
                    language: widget.language,
                  ),
                ],

                const SizedBox(height: 24),
                const Divider(),
                const SizedBox(height: 8),

                // Reported Numbers Section Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                _t('reportedNumbersTitle'),
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              if (_totalReported > 0) ...[
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF2563EB).withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    '$_totalReported',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFF1E40AF),
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _t('reportedNumbersSubtitle'),
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.refresh),
                      tooltip: _t('refresh'),
                      onPressed: () => _loadReportedNumbers(refresh: true),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Search / Filter Input for Reported Numbers
                TextField(
                  controller: _filterController,
                  decoration: InputDecoration(
                    hintText: _t('searchReportedPlaceholder'),
                    prefixIcon: const Icon(Icons.filter_list_rounded, size: 20),
                    suffixIcon: _activeFilter.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _filterController.clear();
                              setState(() => _activeFilter = '');
                              _loadReportedNumbers(refresh: true, search: '');
                            },
                          )
                        : null,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 10,
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  onSubmitted: (val) {
                    setState(() => _activeFilter = val.trim());
                    _loadReportedNumbers(refresh: true, search: _activeFilter);
                  },
                ),
                const SizedBox(height: 16),

                // Reported Numbers Content (Loading / Error / Empty / List)
                if (_isLoadingReported) ...[
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 36),
                    child: Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 12),
                          Text('Loading reported numbers...'),
                        ],
                      ),
                    ),
                  ),
                ] else if (_reportedError != null) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.red.shade200),
                    ),
                    child: Column(
                      children: [
                        Icon(Icons.cloud_off, size: 36, color: Colors.red.shade700),
                        const SizedBox(height: 8),
                        Text(
                          _reportedError!,
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.red.shade800, fontSize: 13),
                        ),
                        const SizedBox(height: 10),
                        OutlinedButton.icon(
                          onPressed: () => _loadReportedNumbers(refresh: true),
                          icon: const Icon(Icons.refresh, size: 16),
                          label: Text(_t('retry')),
                        ),
                      ],
                    ),
                  ),
                ] else if (_reportedList.isEmpty) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 32, horizontal: 20),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade50,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: Colors.grey.shade200),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          _activeFilter.isNotEmpty
                              ? Icons.search_off
                              : Icons.shield_outlined,
                          size: 48,
                          color: _activeFilter.isNotEmpty
                              ? Colors.grey
                              : const Color(0xFF2563EB),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _activeFilter.isNotEmpty
                              ? _t('noMatchingNumbers')
                              : _t('noReportedNumbersTitle'),
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          _activeFilter.isNotEmpty
                              ? 'Try searching with a different number or category.'
                              : _t('noReportedNumbersMsg'),
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey.shade600,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        if (_activeFilter.isEmpty) ...[
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            onPressed: _openReportScreen,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: cs.primary,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            icon: const Icon(Icons.flag_outlined, size: 18),
                            label: Text(_t('reportNumberPrompt')),
                          ),
                        ] else ...[
                          const SizedBox(height: 10),
                          TextButton(
                            onPressed: () {
                              _filterController.clear();
                              setState(() => _activeFilter = '');
                              _loadReportedNumbers(refresh: true, search: '');
                            },
                            child: const Text('Clear search'),
                          ),
                        ],
                      ],
                    ),
                  ),
                ] else ...[
                  ..._reportedList.map((item) {
                    return _ReportedNumberCard(
                      item: item,
                      language: widget.language,
                      onTap: () {
                        // User can tap to inspect or run check
                      },
                    );
                  }),
                  if (_hasMoreReported) ...[
                    const SizedBox(height: 8),
                    Center(
                      child: OutlinedButton.icon(
                        onPressed: _isLoadingMore
                            ? null
                            : () => _loadReportedNumbers(refresh: false),
                        icon: _isLoadingMore
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.expand_more, size: 18),
                        label: Text(_isLoadingMore ? _t('loadingMore') : _t('loadMore')),
                      ),
                    ),
                  ],
                ],
                const SizedBox(height: 24),
              ],
            ),
          ),
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
      body: ResponsiveContainer(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline, size: 20, color: Colors.blue.shade800),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _t('reportDisclaimer'),
                        style: TextStyle(
                          color: Colors.blue.shade900,
                          fontSize: 12.5,
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(
                  labelText: _t('phoneNumberField'),
                  prefixIcon: const Icon(Icons.phone_outlined),
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
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.green.shade300),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_outline, color: Colors.green),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _successMessage!,
                          style: const TextStyle(
                            color: Colors.green,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
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
      ),
    );
  }
}

// ── Bank Security Operations Feed (SOC Portal) ──────────────────────────────

class SecurityOperationsScreen extends StatefulWidget {
  final AppLanguage language;
  final String? initialToken;
  final List<Map<String, dynamic>>? initialEvents;

  const SecurityOperationsScreen({
    super.key,
    required this.language,
    this.initialToken,
    this.initialEvents,
  });

  @override
  State<SecurityOperationsScreen> createState() =>
      _SecurityOperationsScreenState();
}

class _SecurityOperationsScreenState extends State<SecurityOperationsScreen> {
  late final TextEditingController _tokenController;
  bool _isAuthenticated = false;
  bool _isConnecting = false;
  bool _isLoading = false;
  String? _authError;
  String? _feedError;

  String? _activeToken;
  String _analystOrg = 'Commercial Bank of Ethiopia';
  String _analystRole = 'analyst';
  String _activeFilter = 'all';

  final List<Map<String, dynamic>> _events = [];

  String _t(String key) =>
      _strings[widget.language]?[key] ?? _strings[AppLanguage.english]![key]!;

  @override
  void initState() {
    super.initState();
    _tokenController = TextEditingController(text: widget.initialToken ?? '');
    if (widget.initialEvents != null) {
      _isAuthenticated = true;
      _activeToken = widget.initialToken ?? 'TEST-MOCK-TOKEN';
      _events.addAll(widget.initialEvents!);
    } else if (widget.initialToken != null && widget.initialToken!.isNotEmpty) {
      _connect(widget.initialToken!);
    }
  }

  @override
  void dispose() {
    _tokenController.dispose();
    super.dispose();
  }

  Future<void> _connect(String token) async {
    final trimmed = token.trim();
    if (trimmed.isEmpty) {
      setState(() => _authError = _t('socTokenPrompt'));
      return;
    }
    setState(() {
      _isConnecting = true;
      _authError = null;
    });

    try {
      final response = await http.get(
        Uri.parse('$apiBaseUrl/security-feed?limit=50'),
        headers: {
          'Authorization': 'Bearer $trimmed',
          'Accept': 'application/json',
        },
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final items = (data['items'] as List<dynamic>? ?? [])
            .cast<Map<String, dynamic>>();
        setState(() {
          _activeToken = trimmed;
          _isAuthenticated = true;
          _analystOrg = (data['organization'] ?? data['analyst_org']) as String? ?? 'Authorized Bank';
          _analystRole = (data['caller_role'] ?? data['analyst_role']) as String? ?? 'analyst';
          _events
            ..clear()
            ..addAll(items);
        });
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        setState(() => _authError = _t('accessDenied'));
      } else if (response.statusCode == 503) {
        setState(() => _authError =
            'Security feed service unavailable (API keys not configured).');
      } else {
        setState(() => _authError = _t('connectError'));
      }
    } catch (_) {
      if (mounted) setState(() => _authError = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isConnecting = false);
    }
  }

  Future<void> _fetchFeed({String? filter}) async {
    final token = _activeToken;
    if (token == null) return;

    final targetFilter = filter ?? _activeFilter;
    setState(() {
      _isLoading = true;
      _feedError = null;
      _activeFilter = targetFilter;
    });

    final queryParams = <String, String>{'limit': '50'};
    if (targetFilter != 'all') {
      queryParams['event_type'] = targetFilter;
    }

    try {
      final uri =
          Uri.parse('$apiBaseUrl/security-feed').replace(queryParameters: queryParams);
      final response = await http.get(
        uri,
        headers: {
          'Authorization': 'Bearer $token',
          'Accept': 'application/json',
        },
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final items = (data['items'] as List<dynamic>? ?? [])
            .cast<Map<String, dynamic>>();
        setState(() {
          _events
            ..clear()
            ..addAll(items);
        });
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        setState(() {
          _isAuthenticated = false;
          _authError = _t('accessDenied');
        });
      } else {
        setState(() => _feedError = _t('connectError'));
      }
    } catch (_) {
      if (mounted) setState(() => _feedError = _t('connectError'));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _updateReviewStatus(
    String eventId,
    String newStatus, {
    String? notes,
  }) async {
    final token = _activeToken;
    if (token == null) return;

    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/security-feed/$eventId/acknowledge'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'status': newStatus,
          if (notes != null && notes.isNotEmpty) 'analyst_notes': notes,
        }),
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        final idx = _events.indexWhere((e) => e['event_id'] == eventId);
        if (idx != -1) {
          setState(() {
            _events[idx] = {
              ..._events[idx],
              'review_status': newStatus,
              if (notes != null && notes.isNotEmpty) 'analyst_notes': notes,
            };
          });
        }
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_t('reviewStatusUpdated')),
            backgroundColor: Colors.green.shade800,
            duration: const Duration(seconds: 3),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_t('connectError')),
            backgroundColor: Colors.red.shade800,
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(_t('connectError')),
            backgroundColor: Colors.red.shade800,
          ),
        );
      }
    }
  }

  void _showAcknowledgeSheet(Map<String, dynamic> item) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _AcknowledgeModalSheet(
        item: item,
        language: widget.language,
        onSubmit: (status, notes) {
          Navigator.pop(context);
          _updateReviewStatus(item['event_id'] as String, status, notes: notes);
        },
      ),
    );
  }

  void _disconnect() {
    setState(() {
      _isAuthenticated = false;
      _activeToken = null;
      _tokenController.clear();
      _events.clear();
      _authError = null;
      _feedError = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(_t('secOpsTitle')),
        actions: [
          if (_isAuthenticated) ...[
            IconButton(
              icon: const Icon(Icons.refresh),
              tooltip: _t('refresh'),
              onPressed: _isLoading ? null : () => _fetchFeed(),
            ),
            IconButton(
              icon: const Icon(Icons.logout),
              tooltip: _t('disconnectSoc'),
              onPressed: _disconnect,
            ),
          ],
        ],
      ),
      body: ResponsiveContainer(
        maxWidth: 820,
        child: _isAuthenticated ? _buildFeedView(cs) : _buildAuthView(cs),
      ),
    );
  }

  Widget _buildAuthView(ColorScheme cs) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        child: Container(
          padding: const EdgeInsets.all(28),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.grey.shade200),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.04),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              CircleAvatar(
                radius: 32,
                backgroundColor: cs.primary.withValues(alpha: 0.1),
                child: Icon(Icons.admin_panel_settings_outlined,
                    size: 36, color: cs.primary),
              ),
              const SizedBox(height: 18),
              Text(
                _t('secOpsTitle'),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                _t('secOpsSubtitle'),
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13.5, color: Colors.grey.shade600),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _tokenController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: _t('socTokenPrompt'),
                  hintText: 'Enter analyst Bearer token',
                  prefixIcon: const Icon(Icons.vpn_key_outlined),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onSubmitted: (val) => _connect(val),
              ),
              if (_authError != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.red.shade200),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.error_outline,
                          size: 18, color: Colors.red.shade700),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _authError!,
                          style: TextStyle(
                              color: Colors.red.shade800, fontSize: 13),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed:
                    _isConnecting ? null : () => _connect(_tokenController.text),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  backgroundColor: cs.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                icon: _isConnecting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.lock_open, size: 18),
                label: Text(
                  _isConnecting ? 'Connecting...' : _t('connectSoc'),
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeedView(ColorScheme cs) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Organization & Role Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey.shade50,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Row(
              children: [
                Icon(Icons.account_balance, color: cs.primary, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _analystOrg,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14.5,
                        ),
                      ),
                      Text(
                        'Role: ${_analystRole.toUpperCase()} • Authenticated SOC Feed',
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.green.shade50,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.green.shade300),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 7,
                        height: 7,
                        decoration: BoxDecoration(
                          color: Colors.green.shade700,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        'Active',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.green.shade800,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Confidence & Limitation Disclaimer Banner
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFFFFBEB),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFFDE68A)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.warning_amber_rounded,
                    color: Color(0xFFB45309), size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _t('socDisclaimer'),
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF92400E),
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Confidence Note: Data reflects unverified community submissions and pattern heuristics, not confirmed bank compromise.',
                        style: TextStyle(
                          fontSize: 11.5,
                          color: Colors.brown.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Signal Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip('all', _t('filterAll')),
                const SizedBox(width: 8),
                _buildFilterChip('reputation_spike', _t('filterSpike')),
                const SizedBox(width: 8),
                _buildFilterChip('high_report_volume', _t('filterVolume')),
                const SizedBox(width: 8),
                _buildFilterChip('disputed_threat', _t('filterDisputed')),
                const SizedBox(width: 8),
                _buildFilterChip('cross_category_threat', _t('filterCross')),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Feed Content
          if (_isLoading) ...[
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 40),
              child: Center(
                child: Column(
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text('Refreshing security operations feed...'),
                  ],
                ),
              ),
            ),
          ] else if (_feedError != null) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.red.shade200),
              ),
              child: Column(
                children: [
                  Text(_feedError!,
                      style: TextStyle(color: Colors.red.shade800)),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: () => _fetchFeed(),
                    icon: const Icon(Icons.refresh, size: 16),
                    label: Text(_t('retry')),
                  ),
                ],
              ),
            ),
          ] else if (_events.isEmpty) ...[
            Container(
              padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.shield_outlined,
                      size: 46, color: Colors.blue.shade700),
                  const SizedBox(height: 12),
                  Text(
                    _t('noSecAlerts'),
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ] else ...[
            ..._events.map((event) {
              return _SecurityEventCard(
                item: event,
                language: widget.language,
                onAcknowledge: () => _updateReviewStatus(
                  event['event_id'] as String,
                  'acknowledged',
                ),
                onUpdateStatus: () => _showAcknowledgeSheet(event),
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildFilterChip(String filterKey, String label) {
    final isSelected = _activeFilter == filterKey;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => _fetchFeed(filter: filterKey),
      selectedColor: const Color(0xFF1E40AF).withValues(alpha: 0.12),
      labelStyle: TextStyle(
        fontSize: 12.5,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        color: isSelected ? const Color(0xFF1E40AF) : Colors.black87,
      ),
    );
  }
}

// ── Security Event Card ──────────────────────────────────────────────────────

class _SecurityEventCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final AppLanguage language;
  final VoidCallback onAcknowledge;
  final VoidCallback onUpdateStatus;

  const _SecurityEventCard({
    required this.item,
    required this.language,
    required this.onAcknowledge,
    required this.onUpdateStatus,
  });

  String _t(String key) =>
      _strings[language]?[key] ?? _strings[AppLanguage.english]![key]!;

  Color _priorityColor(String priority) {
    return switch (priority.toLowerCase()) {
      'critical' => Colors.red.shade700,
      'high' => Colors.deepOrange.shade700,
      'medium' => Colors.amber.shade900,
      _ => Colors.blue.shade700,
    };
  }

  Color _statusColor(String status) {
    return switch (status.toLowerCase()) {
      'new' => Colors.blue.shade700,
      'acknowledged' => Colors.purple.shade700,
      'under_review' => Colors.orange.shade800,
      'resolved' => Colors.green.shade700,
      _ => Colors.grey.shade700,
    };
  }

  String _eventTypeLabel(String eventType) {
    return switch (eventType.toLowerCase()) {
      'reputation_spike' => 'Reputation Spike (24h)',
      'high_report_volume' => 'High Report Volume',
      'disputed_threat' => 'Disputed Threat',
      'cross_category_threat' => 'Cross-Category Threat',
      _ => eventType.replaceAll('_', ' ').toUpperCase(),
    };
  }

  @override
  Widget build(BuildContext context) {
    final phone = item['phone_number'] as String? ?? '';
    final phoneMasked = item['phone_masked'] as String? ?? '';
    final priority = item['priority'] as String? ?? 'medium';
    final eventType = item['event_type'] as String? ?? '';
    final reviewStatus = item['review_status'] as String? ?? 'new';
    final totalReports = item['total_reports'] as int? ?? 0;
    final spike24h = item['reports_last_24h'] as int? ?? 0;
    final categories =
        (item['categories'] as List<dynamic>? ?? []).cast<String>();
    final reason = item['reason'] as String? ?? '';
    final evidence = item['evidence_summary'] as String? ?? '';
    final confidenceNotice = item['confidence_limitations'] as String? ?? '';
    final analystNotes = item['analyst_notes'] as String?;
    final lastUpdated = item['last_updated'] as String? ?? '';

    final priColor = _priorityColor(priority);
    final statColor = _statusColor(reviewStatus);

    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Top Badge Row: Priority + Event Type + Review Status
            Row(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: priColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: priColor.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    priority.toUpperCase(),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: priColor,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _eventTypeLabel(eventType),
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: statColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    reviewStatus.toUpperCase(),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: statColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Phone Numbers (Full & Masked)
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        phone,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Masked: $phoneMasked',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
                // Report Metric Badges
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '$totalReports reports',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (spike24h > 0)
                      Text(
                        '+$spike24h in 24h',
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w600,
                          color: Colors.red.shade700,
                        ),
                      ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Category Chips
            if (categories.isNotEmpty) ...[
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: categories.map((cat) {
                  return Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 2.5),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Text(
                      _translateCategory(language, cat),
                      style: TextStyle(
                        fontSize: 11,
                        color: Colors.grey.shade800,
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 10),
            ],

            // Reason & Limitations Box
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.grey.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    reason,
                    style: const TextStyle(fontSize: 12.5),
                  ),
                  if (evidence.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Evidence: $evidence',
                      style: TextStyle(
                        fontSize: 11.5,
                        color: Colors.grey.shade700,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(Icons.info_outline,
                          size: 13, color: Colors.blueGrey.shade600),
                      const SizedBox(width: 5),
                      Expanded(
                        child: Text(
                          confidenceNotice.isNotEmpty
                              ? confidenceNotice
                              : _t('confidenceNotice'),
                          style: TextStyle(
                            fontSize: 11,
                            color: Colors.blueGrey.shade700,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            // Analyst notes if present
            if (analystNotes != null && analystNotes.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.blue.shade200),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.notes, size: 15, color: Colors.blue.shade800),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Analyst Note: $analystNotes',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.blue.shade900,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 10),

            // Footer: Timestamp & Action Buttons
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Updated: ${lastUpdated.contains("T") ? lastUpdated.split("T").first : lastUpdated}',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.grey.shade500,
                    ),
                  ),
                ),
                if (reviewStatus == 'new') ...[
                  OutlinedButton.icon(
                    onPressed: onAcknowledge,
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    icon: const Icon(Icons.check, size: 14),
                    label: Text(_t('ackAlert'),
                        style: const TextStyle(fontSize: 12)),
                  ),
                  const SizedBox(width: 8),
                ],
                ElevatedButton.icon(
                  onPressed: onUpdateStatus,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 6),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    backgroundColor: const Color(0xFF1E40AF),
                    foregroundColor: Colors.white,
                  ),
                  icon: const Icon(Icons.edit_outlined, size: 14),
                  label: Text(_t('updateReview'),
                      style: const TextStyle(fontSize: 12)),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ── SOC Analyst Acknowledge & Status Update Sheet ─────────────────────────────

class _AcknowledgeModalSheet extends StatefulWidget {
  final Map<String, dynamic> item;
  final AppLanguage language;
  final void Function(String status, String? notes) onSubmit;

  const _AcknowledgeModalSheet({
    required this.item,
    required this.language,
    required this.onSubmit,
  });

  @override
  State<_AcknowledgeModalSheet> createState() => _AcknowledgeModalSheetState();
}

class _AcknowledgeModalSheetState extends State<_AcknowledgeModalSheet> {
  late String _status;
  final _notesController = TextEditingController();

  String _t(String key) =>
      _strings[widget.language]?[key] ?? _strings[AppLanguage.english]![key]!;

  @override
  void initState() {
    super.initState();
    _status = widget.item['review_status'] as String? ?? 'acknowledged';
    if (_status == 'new') _status = 'acknowledged';
    _notesController.text = widget.item['analyst_notes'] as String? ?? '';
  }

  @override
  void dispose() {
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final phone = widget.item['phone_number'] as String? ?? '';

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.shield, color: Color(0xFF1E40AF)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Update Status: $phone',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Text(
            'Select review status:',
            style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              _statusChip('acknowledged', _t('statusAcknowledged')),
              _statusChip('under_review', _t('statusUnderReview')),
              _statusChip('resolved', _t('statusResolved')),
              _statusChip('dismissed', _t('statusDismissed')),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _notesController,
            maxLines: 2,
            decoration: InputDecoration(
              labelText: _t('analystNotesLabel'),
              hintText: _t('analystNotesHint'),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
          ),
          const SizedBox(height: 18),
          ElevatedButton(
            onPressed: () => widget.onSubmit(
              _status,
              _notesController.text.trim().isEmpty
                  ? null
                  : _notesController.text.trim(),
            ),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 13),
              backgroundColor: const Color(0xFF1E40AF),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: Text(
              _t('saveStatus'),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statusChip(String value, String label) {
    final selected = _status == value;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => setState(() => _status = value),
      selectedColor: const Color(0xFF1E40AF).withValues(alpha: 0.15),
      labelStyle: TextStyle(
        fontSize: 12,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
        color: selected ? const Color(0xFF1E40AF) : Colors.black87,
      ),
    );
  }
}
