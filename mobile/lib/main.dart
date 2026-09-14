import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const CyberSafetyApp());
}

class CyberSafetyApp extends StatelessWidget {
  const CyberSafetyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Multilingual Cyber-Safety Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.light,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _textController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;

  // Genymotion Emulator IP: 10.0.3.2
  final String _apiUrl = 'http://10.0.3.2:8000/analyze';

  Future<void> _analyzeMessage() async {
    final text = _textController.text.trim();

    if (text.isEmpty) {
      setState(() {
        _errorMessage = 'Please enter a message to analyze.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await http.post(
        Uri.parse(_apiUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'message': text}),
      );

      if (response.statusCode == 200) {
        final result = jsonDecode(response.body);
        if (!mounted) return;

        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResultScreen(result: result),
          ),
        );
      } else {
        final errorBody = jsonDecode(response.body);
        setState(() {
          _errorMessage = errorBody['detail'] ?? 'Analysis request failed.';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage =
            'Unable to connect to backend server. Make sure FastAPI is running.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cyber-Safety Assistant'),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(
              Icons.shield_outlined,
              size: 64,
              color: Colors.deepPurple,
            ),
            const SizedBox(height: 16),
            const Text(
              'Analyze Multilingual Messages',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Paste suspicious SMS, Telegram, or Telebirr messages in English, Amharic, or mixed language.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.black54),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _textController,
              maxLines: 5,
              decoration: InputDecoration(
                hintText:
                    'e.g., የእርስዎ telebirr ሂሳብ ታግዷል። PIN ቁጥርዎን በ http://cbe-verify.top/login ያስገቡ',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                errorText: _errorMessage,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _analyzeMessage,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              icon: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.search),
              label: Text(
                _isLoading ? 'Analyzing...' : 'Analyze Message',
                style: const TextStyle(fontSize: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> result;

  const ResultScreen({super.key, required this.result});

  Color _getRiskColor(String rawClassification) {
    if (rawClassification.contains('HIGH')) {
      return Colors.red;
    } else if (rawClassification.contains('MEDIUM')) {
      return Colors.orange;
    }
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    final rawClassification = result['classification'] as String? ?? 'LOW_RISK';
    final riskScore = result['risk_score'] ?? 0;
    final language = result['language'] ?? 'Unknown';
    final recommendation = result['recommendation'] ?? 'No detail provided.';
    final indicators = List<String>.from(result['indicators'] ?? []);
    final urls = List<String>.from(result['urls'] ?? []);

    final displayRiskLevel = rawClassification
        .replaceAll('_RISK', '')
        .replaceAll('_', ' ');

    final cardColor = _getRiskColor(rawClassification);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Results'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              color: cardColor.withValues(alpha: 0.1),
              shape: RoundedRectangleBorder(
                side: BorderSide(color: cardColor, width: 2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Expanded prevents long titles from causing text overflow
                        Expanded(
                          child: Text(
                            'Risk Level: $displayRiskLevel',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: cardColor,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Chip(
                          label: Text(
                            'Score: $riskScore / 100',
                            style:
                                const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          backgroundColor: cardColor.withValues(alpha: 0.2),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    Text(
                      'Language Detected: $language',
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Recommendation',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              recommendation,
              style: const TextStyle(fontSize: 15, height: 1.4),
            ),
            const SizedBox(height: 20),
            if (urls.isNotEmpty) ...[
              const Text(
                'Detected Links',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...urls.map(
                (url) => Padding(
                  padding: const EdgeInsets.only(bottom: 6.0),
                  child: Row(
                    children: [
                      const Icon(Icons.link, color: Colors.red, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          url,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.red,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
            if (indicators.isNotEmpty) ...[
              const Text(
                'Detected Risk Indicators',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...indicators.map(
                (indicator) => Padding(
                  padding: const EdgeInsets.only(bottom: 6.0),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded,
                          color: Colors.orange, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          indicator.replaceAll('_', ' ').toUpperCase(),
                          style: const TextStyle(fontSize: 14),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}