# Multilingual AI Cyber-Safety Assistant — System Architecture

## 1. Overview

The Multilingual AI Cyber-Safety Assistant is a mobile-first cybersecurity system designed to help users identify phishing, scams, social engineering, impersonation, and other suspicious digital communications.

The system is designed specifically to handle:

* English messages
* Amharic messages
* Amharic-English code-switched messages
* Suspicious URLs
* Financial and credential-related scams
* Messages received through different digital communication channels

The core principle is:

**Detect → Explain → Educate → Protect**

The system should not simply tell the user that a message is dangerous. It should explain the indicators that caused the decision and provide a clear recommendation.

---

## 2. High-Level Architecture

```text
                    ┌─────────────────────────┐
                    │       User / Message    │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
        Message Input                         Screenshot
        / Share / SMS                            / OCR
              │                                     │
              └──────────────────┬──────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Text Preprocessing    │
                    │                         │
                    │ • Normalization          │
                    │ • URL extraction        │
                    │ • Language detection     │
                    │ • Code-switch detection │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
       ┌───────────────┐ ┌──────────────┐ ┌───────────────┐
       │ AI/NLP Engine │ │ Security     │ │ URL Analysis  │
       │               │ │ Rules Engine │ │ Engine        │
       │ • ML model    │ │              │ │               │
       │ • NLP         │ │ • Urgency    │ │ • Domain      │
       │ • Language    │ │ • Credentials│ │ • Structure   │
       │ • Social Eng. │ │ • Financial  │ │ • Shorteners  │
       └───────┬───────┘ └──────┬───────┘ └───────┬───────┘
               │                │                 │
               └────────────────┼─────────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │      Risk Engine        │
                    │                         │
                    │ Combines AI + security  │
                    │ indicators + URL signals│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Threat Classification  │
                    │                         │
                    │ SAFE                     │
                    │ SUSPICIOUS               │
                    │ HIGH RISK                │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Explanation & Response  │
                    │                         │
                    │ • Threat type            │
                    │ • Risk score             │
                    │ • Indicators             │
                    │ • Explanation            │
                    │ • Recommendation         │
                    │ • Education              │
                    └─────────────────────────┘
```

---

## 3. System Components

### 3.1 Mobile Application

The mobile application is the primary user interface.

The application will allow users to:

* Paste a suspicious message
* Share a message to the application from supported applications
* Analyze suspicious URLs
* Analyze screenshots using OCR
* View the security assessment
* Understand why a message was classified as suspicious
* Receive recommended actions
* Learn common social-engineering warning signs

The initial MVP will prioritize manual input and share-to-analyze functionality.

Direct access to third-party applications such as WhatsApp and Telegram will not be treated as a dependency because Android and application privacy restrictions may prevent unrestricted message interception.

---

## 4. Message Processing Pipeline

When a message is submitted, the system follows these steps.

### Step 1 — Input

The system receives:

* Text message
* Screenshot
* Shared message
* SMS content where supported

### Step 2 — Preprocessing

The message is normalized while preserving security-relevant information.

The preprocessing layer should preserve:

* URLs
* Numbers
* Currency values
* Amharic characters
* English characters
* Important punctuation
* Usernames and mentions
* Suspicious Unicode characters

### Step 3 — Language Detection

The system identifies whether the message is:

* English
* Amharic
* Amharic-English mixed
* Unknown/other

The system must specifically support code-switching because Ethiopian users may naturally combine Amharic and English in the same message.

Example:

```text
እንኳን ደስ አለዎት! You have won 50,000 ETB.
Click here to claim your prize.
```

This should be classified as:

```text
language: MIXED
code_switched: true
```

---

## 5. AI/NLP Detection Engine

The AI/NLP engine analyzes the linguistic and semantic characteristics of the message.

The initial baseline will use a traditional machine-learning approach such as:

* TF-IDF
* Logistic Regression or Linear SVM

The initial classification task will use:

```text
BENIGN
SUSPICIOUS
PHISHING
```

The model will later be evaluated against more advanced multilingual approaches.

Potential future models include multilingual transformer-based models and other models appropriate for Amharic NLP.

The AI layer will examine characteristics such as:

* Suspicious language
* Urgency
* Fear
* Reward claims
* Requests for credentials
* Financial requests
* Account verification requests
* Impersonation language
* Calls to action
* Social-engineering patterns

---

## 6. Security Rules Engine

The security rules engine provides deterministic cybersecurity signals that complement the AI model.

Examples include:

### Social Engineering

* Urgent requests
* Threats of account suspension
* Prize/reward claims
* Requests for money
* Requests for passwords
* Requests for OTPs
* Requests for banking information
* Requests to verify an account

### Impersonation

The system can look for messages pretending to represent:

* Banks
* Financial institutions
* Government organizations
* Delivery companies
* Employers
* Popular services

### URL Indicators

The system can identify:

* URL shorteners
* IP-address URLs
* Suspicious domains
* Excessive subdomains
* Unusual URL structures
* Lookalike domains
* Suspicious Unicode characters
* Punycode/homograph indicators
* Suspicious paths or parameters

The rules engine should produce explainable indicators rather than making the final decision by itself.

---

## 7. URL Analysis Engine

URLs are extracted from submitted messages and analyzed independently.

Example:

```text
Congratulations! You won 50,000 ETB.
Claim here:
http://example.com/verify-account
```

The URL analyzer evaluates the URL independently of the message text.

Potential signals include:

```text
domain reputation
URL structure
domain length
subdomain count
IP address usage
URL shortening
suspicious characters
lookalike domains
punycode
credential-related paths
redirects
```

Threat-intelligence services may be integrated later where appropriate.

---

## 8. Risk Engine

The risk engine combines signals from:

1. AI/NLP model
2. Security rules
3. URL analysis
4. Threat intelligence
5. Language/code-switch analysis

The final result should contain:

```text
classification
risk score
threat type
language
code-switch status
indicators
explanation
recommendation
```

Example:

```json
{
  "classification": "HIGH_RISK",
  "risk_score": 91,
  "threat_type": "PRIZE_SCAM",
  "language": "MIXED",
  "code_switched": true,
  "indicators": [
    "financial_reward",
    "urgency",
    "suspicious_url",
    "call_to_action"
  ],
  "recommendation": "Do not click the link or provide personal or financial information."
}
```

The numerical score is an internal risk representation and should be calibrated using evaluation data. Example scores must not be treated as validated results until experiments are performed.

---

## 9. Explainability Layer

A key feature of the system is that it should explain its decision.

Instead of:

```text
PHISHING
```

the system should provide:

```text
HIGH RISK — Likely phishing/scam

Why?

• The message promises an unexpected financial reward.
• It creates pressure to take immediate action.
• It contains a suspicious link.
• It asks the user to claim the reward.

What should you do?

Do not click the link.
Do not provide your password, OTP, banking information, or personal information.
Verify the claim through the organization's official application or website.
```

This makes the system useful for **human cyber resilience**, not only threat detection.

---

## 10. Backend Architecture

The backend will initially use Python and FastAPI.

Initial API:

```text
POST /analyze
```

Example request:

```json
{
  "message": "Congratulations! You won 50,000 ETB. Click here to claim!"
}
```

Example response:

```json
{
  "classification": "HIGH_RISK",
  "risk_score": 87,
  "threat_type": "PRIZE_SCAM",
  "language": "ENGLISH",
  "code_switched": false,
  "indicators": [
    "financial_reward",
    "call_to_action"
  ],
  "recommendation": "Do not click the link."
}
```

The backend should keep the detection components modular so that the ML model, URL analyzer, rules engine, and risk engine can be improved independently.

---

## 11. Privacy Architecture

Privacy is an important design requirement.

The system should avoid unnecessary collection or storage of personal messages.

The preferred architecture is:

```text
User
  │
  ▼
Local preprocessing
  │
  ├──► Local analysis where practical
  │
  └──► Backend analysis when required
            │
            ▼
       Minimal data
```

Future versions should prioritize:

* On-device processing where practical
* Minimal message retention
* Explicit user consent
* Secure communication
* Removal/redaction of unnecessary personal information
* No unnecessary storage of analyzed messages

---

## 12. Human Cyber-Resilience Layer

The system is not intended to be only a detection tool.

It should help users understand common attack techniques.

Future features may include:

* "Why is this suspicious?"
* "What is phishing?"
* "How to identify a fake link"
* "How scammers create urgency"
* "How impersonation attacks work"
* "Test yourself" scenarios
* Short interactive cybersecurity lessons

The objective is to improve the user's ability to recognize attacks independently.

---

## 13. Future Channel Architecture

The detection engine should remain channel-independent.

```text
                 ┌── SMS
                 ├── WhatsApp
                 ├── Telegram
                 ├── Email
                 ├── Screenshot
                 └── Other supported sources
                         │
                         ▼
                 Common Analysis Engine
                         │
                         ▼
                  Risk Assessment
```

Different channels should feed into the same core security engine rather than requiring separate detection systems.

---

## 14. Technology Stack

### Mobile

* Flutter
* Android
* Dart

### Backend

* Python
* FastAPI

### Machine Learning

* Python
* scikit-learn
* pandas
* NumPy
* Hugging Face Transformers (future/advanced models)

### Security

* Python URL parsing
* Custom security rules
* Domain/URL analysis
* Threat-intelligence integrations where appropriate

### Development

* Git
* GitHub
* VS Code
* Automated tests

---

## 15. Design Principles

The project will follow these principles:

1. **Multilingual-first** — Amharic and English are core requirements, not afterthoughts.
2. **Code-switch aware** — Mixed Amharic-English communication must be supported.
3. **Explainable** — Users should understand why something is suspicious.
4. **Security-first** — AI predictions should be combined with deterministic security signals.
5. **Privacy-conscious** — Avoid unnecessary collection and storage of user messages.
6. **Channel-independent** — The core detection engine should work regardless of message source.
7. **Human-centered** — The system should improve user security awareness, not only classify messages.
8. **Research-driven** — Detection performance must be measured experimentally.
9. **Modular** — Individual components should be replaceable and independently tested.
10. **Demonstrable** — The system must produce a practical, understandable cybersecurity demonstration.
