# Multilingual AI Cyber-Safety Assistant — 5-Day MVP Roadmap

## 1. MVP Goal

The goal of the five-day MVP is to build a functional prototype of the Multilingual AI Cyber-Safety Assistant that can analyze a suspicious digital message and provide a meaningful cybersecurity assessment.

By the end of Day 5, the team should have a working demonstration consisting of:

```text
User
  ↓
Mobile Application
  ↓
Message Analysis API
  ↓
Text/NLP Analysis
  +
Security Rules
  +
URL Analysis
  ↓
Risk Engine
  ↓
Security Assessment
  ↓
Explanation + Recommendation
```

The MVP must demonstrate the project's core research and product concept rather than attempting to implement every planned feature.

---

# 2. MVP Definition

## 2.1 Input

The MVP should accept a suspicious message through:

* Manual text input
* Copy/paste
* Share-to-app where feasible
* Controlled SMS demonstration where technically supported

The MVP does **not** require unrestricted interception of WhatsApp, Telegram, or other third-party applications.

The core analysis engine must remain independent of the source of the message.

---

## 2.2 Supported Languages

The MVP will support:

* English
* Amharic
* Amharic-English code-switched messages

Example:

```text
እንኳን ደስ አለዎት! You have won 50,000 ETB.
Click here to claim your prize.
```

The system should identify this as:

```text
language: MIXED
code_switched: true
```

---

## 2.3 MVP Threat Categories

The initial system will focus on:

* Benign
* Suspicious
* Phishing
* Financial scam
* Prize/reward scam
* Credential phishing
* Impersonation
* Account verification scam
* Malicious/suspicious URL
* Other social engineering

The exact classification structure may be adjusted after inspecting the dataset and evaluating the baseline model.

---

# 3. MVP Architecture

```text
                    ┌───────────────────┐
                    │       User        │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Flutter App     │
                    │                   │
                    │ Enter / Share     │
                    │ suspicious text  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │    FastAPI        │
                    │    /analyze       │
                    └─────────┬─────────┘
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
          ┌────────────┐ ┌──────────┐ ┌─────────────┐
          │ NLP / ML   │ │ Security │ │ URL         │
          │            │ │ Rules    │ │ Analysis    │
          └─────┬──────┘ └────┬─────┘ └──────┬──────┘
                │             │              │
                └─────────────┼──────────────┘
                              ▼
                    ┌───────────────────┐
                    │    Risk Engine    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Security Result   │
                    │                   │
                    │ Risk Level        │
                    │ Risk Score        │
                    │ Threat Type       │
                    │ Indicators        │
                    │ Explanation       │
                    │ Recommendation    │
                    └───────────────────┘
```

---

# 4. Day 1 — Foundation and Detection Pipeline

## Objective

Build the project's foundation and create the first working message-analysis pipeline.

At the end of Day 1, a message should be able to enter the backend and produce a preliminary security assessment.

---

## Person 1 — Cybersecurity + Backend

### Task 1 — Repository Setup

Confirm the repository structure:

```text
multilingual-cyber-safety/
│
├── README.md
│
├── docs/
│   ├── architecture.md
│   ├── threat-model.md
│   ├── research-question.md
│   └── roadmap.md
│
├── dataset/
│   ├── raw/
│   ├── processed/
│   └── README.md
│
├── backend/
│   ├── app/
│   └── tests/
│
├── detection/
│   ├── rules/
│   ├── url_analysis/
│   └── risk_engine/
│
├── ml/
│   ├── preprocessing/
│   ├── training/
│   ├── evaluation/
│   └── models/
│
├── mobile/
│
└── research/
```

---

### Task 2 — Threat Taxonomy

Finalize the initial threat categories and indicators.

Define indicators such as:

```text
urgency
fear
financial_request
credential_request
otp_request
reward
impersonation
account_verification
call_to_action
suspicious_url
```

Document the definitions.

---

### Task 3 — Security Rules

Create the first deterministic rules.

Examples:

```text
IF message requests OTP
    → credential/financial indicator

IF message contains urgent account threat
    → urgency indicator

IF message promises unexpected money
    → financial_reward indicator

IF message contains suspicious URL
    → suspicious_url indicator
```

The rules should produce indicators rather than immediately making the final decision.

---

### Task 4 — URL Analyzer Foundation

Implement initial URL extraction and analysis.

Detect:

```text
URLs
IP-based URLs
URL shorteners
unusual domains
excessive subdomains
suspicious URL paths
```

The first version does not need sophisticated external threat intelligence.

---

### Task 5 — Risk Engine

Create the first risk-scoring framework.

Example concept:

```text
AI score
+
security-rule signals
+
URL signals
=
risk assessment
```

Initial output:

```json
{
  "classification": "HIGH_RISK",
  "risk_score": 87,
  "threat_type": "PRIZE_SCAM",
  "language": "ENGLISH",
  "code_switched": false,
  "indicators": [
    "financial_reward",
    "urgency",
    "suspicious_url"
  ],
  "recommendation": "Do not click the link or provide personal information."
}
```

The score is provisional and must be calibrated later using evaluation data.

---

### Task 6 — FastAPI Backend

Create:

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

FastAPI provides automatic interactive API documentation, so the endpoint can be tested through `/docs` during development.

---

## Person 2 — Data + AI/NLP

### Task 1 — Dataset v0.1

Create:

```text
dataset/raw/messages.csv
```

Columns:

```text
id
text
label
language
code_switched
threat_type
indicators
source
```

Create an initial balanced dataset containing:

```text
English benign
English phishing/scam

Amharic benign
Amharic phishing/scam

Mixed benign
Mixed phishing/scam
```

Do not worry about making the dataset huge on Day 1.

The priority is creating a clean structure that can be expanded.

---

### Task 2 — Data Quality

Check every sample for:

* Correct label
* Correct language
* Correct code-switch status
* Correct threat category
* Correct indicators
* Correct source

Clearly mark synthetic examples as synthetic.

---

### Task 3 — Preprocessing

Create basic preprocessing that preserves:

* Amharic Unicode
* English text
* Numbers
* URLs
* Currency values
* Important punctuation

Do not aggressively clean the data in a way that removes cybersecurity signals.

---

### Task 4 — Language Detection

Implement initial detection:

```text
ENGLISH
AMHARIC
MIXED
UNKNOWN
```

Test using both simple messages and code-switched examples.

---

### Task 5 — ML Pipeline Skeleton

Prepare:

```text
preprocessing
      ↓
train/test split
      ↓
TF-IDF
      ↓
Logistic Regression or Linear SVM
      ↓
evaluation
```

The actual model can be completed on Day 2.

---

## Together — End-of-Day 1

Both team members review:

* Architecture
* Threat categories
* Dataset format
* API format
* Risk engine design
* Research question
* MVP scope

### Day 1 Definition of Done

By the end of Day 1:

* [ ] GitHub repository works
* [ ] Project structure exists
* [ ] Documentation exists
* [ ] Threat taxonomy is defined
* [ ] Initial dataset exists
* [ ] English/Amharic/mixed detection exists
* [ ] Security rules exist
* [ ] URL extraction exists
* [ ] Risk engine skeleton exists
* [ ] FastAPI `/analyze` exists
* [ ] API returns structured JSON
* [ ] At least several test messages work

---

# 5. Day 2 — AI/NLP Detection Engine

## Objective

Build the first real machine-learning detection model and measure its performance.

---

## Person 1 — Backend + Security

### Task 1 — Integrate ML Model

Create a clean interface between the backend and ML model.

Concept:

```text
message
   ↓
preprocessing
   ↓
ML model
   ↓
prediction + confidence
```

The backend should not contain the training logic.

---

### Task 2 — Improve Security Rules

Expand the initial rules to cover:

* OTP requests
* Password requests
* Financial requests
* Urgency
* Fear
* Rewards
* Account verification
* Impersonation
* Suspicious links

---

### Task 3 — Risk Engine Integration

Combine the ML result with security indicators.

Example:

```text
ML prediction:
PHISHING

Security indicators:
OTP request
Urgency
Suspicious URL

Final:
HIGH_RISK
```

---

## Person 2 — ML/NLP

### Task 1 — Train Baseline

Train:

```text
TF-IDF
+
Logistic Regression
```

or:

```text
TF-IDF
+
Linear SVM
```

Compare the two if time permits.

---

### Task 2 — Dataset Split

Create:

```text
Training set
Validation set
Test set
```

Avoid data leakage between training and testing.

---

### Task 3 — Evaluation

Calculate:

* Accuracy
* Precision
* Recall
* F1-score
* Confusion matrix

Evaluate:

```text
Overall
English
Amharic
Mixed
```

---

### Task 4 — Error Analysis

Inspect incorrectly classified messages.

Create categories such as:

```text
False positive
False negative
Language error
Code-switch error
URL-related error
Ambiguous message
```

Document examples.

---

## Together — End-of-Day 2

The team should be able to demonstrate:

```text
Message
   ↓
ML model
   ↓
Prediction
   ↓
Risk engine
   ↓
Result
```

### Day 2 Definition of Done

* [ ] ML baseline trained
* [ ] Model saved
* [ ] Backend can load model
* [ ] Predictions work through API
* [ ] Metrics calculated
* [ ] English evaluated
* [ ] Amharic evaluated
* [ ] Mixed-language evaluated
* [ ] Initial error analysis completed
* [ ] Security rules integrated

---

# 6. Day 3 — Cybersecurity Intelligence Layer

## Objective

Make the system look and behave like a cybersecurity product rather than a generic text classifier.

---

## Person 1 — Cybersecurity Lead

### Task 1 — URL Analysis

Improve the URL analyzer.

Implement checks for:

```text
IP address URLs
URL shorteners
suspicious domains
excessive subdomains
long URLs
suspicious paths
credential-related paths
lookalike domains
suspicious Unicode
punycode
```

---

### Task 2 — Social-Engineering Detection

Implement indicators for:

```text
urgency
fear
reward
authority
financial pressure
credential requests
OTP requests
account verification
impersonation
```

---

### Task 3 — Threat Classification

Improve mapping between indicators and threat types.

Example:

```text
OTP request
+
bank impersonation
+
suspicious URL

→ CREDENTIAL_PHISHING
```

Example:

```text
unexpected reward
+
financial amount
+
claim link

→ PRIZE_SCAM
```

---

### Task 4 — Risk Scoring

Create a consistent scoring strategy.

Example conceptual model:

```text
ML signal
     +
Rule signals
     +
URL signals
     +
Threat intelligence signals
     ↓
Risk Engine
     ↓
0–100 risk score
```

Do not claim that the score is statistically calibrated until it has been evaluated.

---

## Person 2 — ML/NLP

### Task 1 — Improve Preprocessing

Test:

* Amharic text
* English text
* Mixed text
* Numbers
* URLs
* Misspellings
* Informal language

---

### Task 2 — Model Comparison

If time allows, compare:

```text
English-oriented baseline
vs.
multilingual dataset model
```

The objective is to establish a meaningful baseline for the research.

---

### Task 3 — Error Analysis

Find difficult examples.

Examples:

```text
Legitimate bank message
        vs.
Bank impersonation

Legitimate prize announcement
        vs.
Prize scam

Normal account notification
        vs.
Account phishing
```

---

## Together — End-of-Day 3

The API should now provide:

```text
Risk level
Risk score
Threat type
Language
Code-switch status
Indicators
Explanation
Recommendation
```

### Day 3 Definition of Done

* [ ] URL analyzer works
* [ ] Security rules expanded
* [ ] Risk engine combines multiple signals
* [ ] Threat types work
* [ ] Explanations generated
* [ ] Recommendations generated
* [ ] API returns complete security assessment
* [ ] Difficult examples tested
* [ ] False positives reviewed
* [ ] False negatives reviewed

---

# 7. Day 4 — Mobile Application

## Objective

Build a functional Android interface that connects to the backend.

---

## Person 1 — Backend

### Task 1 — Stabilize API

Ensure:

```text
POST /analyze
```

works reliably.

Validate:

* Empty messages
* Very long messages
* Unicode
* Amharic
* URLs
* Mixed-language messages
* Malformed requests

---

### Task 2 — API Response

Make sure the response is easy for the mobile application to consume.

Recommended structure:

```json
{
  "classification": "HIGH_RISK",
  "risk_score": 91,
  "threat_type": "FINANCIAL_SCAM",
  "language": "MIXED",
  "code_switched": true,
  "indicators": [
    "financial_request",
    "urgency",
    "suspicious_url"
  ],
  "explanation": "This message contains several indicators commonly associated with financial scams.",
  "recommendation": "Do not click the link or provide financial information."
}
```

---

## Person 2 — Mobile

### Task 1 — Flutter Application

Create the basic Android application.

The MVP should contain:

```text
Home Screen
      ↓
Message Input
      ↓
Analyze Button
      ↓
Loading
      ↓
Result Screen
```

Flutter will be used for the mobile prototype. The official Flutter documentation supports Windows development and provides setup guidance for Flutter tooling on Windows.

---

### Task 2 — Home Screen

The home screen should have:

```text
Multilingual AI
Cyber-Safety Assistant

"Check a suspicious message before you act."

[ Paste or type message ]

[ Analyze Message ]
```

Keep the interface simple.

---

### Task 3 — Result Screen

Display:

```text
HIGH RISK
91/100

Financial Scam

Why?

• Suspicious URL
• Financial request
• Urgency
• Possible impersonation

What should you do?

Do not click the link.
Do not provide OTPs or financial information.
Verify through the organization's official channel.
```

Use clear visual hierarchy.

---

### Task 4 — Share-to-Analyze

If technically feasible within the time available, implement Android sharing so a user can share text from another application to the Cyber-Safety Assistant.

Priority:

```text
Manual input
      ↓
Share-to-analyze
```

Do not spend the entire day trying to achieve unrestricted WhatsApp/Telegram message interception.

---

## Together — End-of-Day 4

The team should be able to physically demonstrate:

```text
Open Android app
      ↓
Paste suspicious message
      ↓
Tap Analyze
      ↓
Backend analyzes message
      ↓
Result appears
```

### Day 4 Definition of Done

* [ ] Flutter app runs
* [ ] Home screen works
* [ ] Message input works
* [ ] API connection works
* [ ] Loading state works
* [ ] Result screen works
* [ ] Risk level displayed
* [ ] Threat type displayed
* [ ] Indicators displayed
* [ ] Explanation displayed
* [ ] Recommendation displayed
* [ ] Amharic text renders correctly
* [ ] Mixed-language text renders correctly
* [ ] Share-to-analyze attempted if feasible

---

# 8. Day 5 — Integration, Testing, Demo, and EOI Preparation

## Objective

Turn the separate components into a stable, presentable MVP.

**Day 5 is not for adding major new features.**

The priority is:

```text
STABILIZE
TEST
DOCUMENT
DEMONSTRATE
```

---

## Morning — Integration

### Task 1 — Full System Test

Test the complete pipeline:

```text
Mobile
  ↓
FastAPI
  ↓
Preprocessing
  ↓
ML
  ↓
Security Rules
  ↓
URL Analysis
  ↓
Risk Engine
  ↓
Result
```

---

### Task 2 — Test Messages

Prepare at least:

#### Benign English

```text
Hey, are we still meeting at 5pm today?
```

Expected:

```text
SAFE
```

#### Benign Amharic

```text
ሰላም፣ ዛሬ ከሰዓት 5 ሰዓት ላይ እንገናኝ?
```

Expected:

```text
SAFE
```

#### English Phishing

```text
Your account will be suspended today. Verify your account immediately.
```

Expected:

```text
HIGH_RISK / PHISHING
```

#### Amharic Scam

```text
እንኳን ደስ አለዎት! 50,000 ብር አሸንፈዋል።
```

Expected:

```text
HIGH_RISK / SCAM
```

#### Mixed Scam

```text
እንኳን ደስ አለዎት! You won 50,000 ETB.
Click here to claim your prize.
```

Expected:

```text
HIGH_RISK / PRIZE_SCAM
```

---

# 9. Day 5 — Security and Reliability Testing

Test:

### Empty Input

```text
""
```

The application should display a useful validation message.

### Long Input

Test unusually long messages.

### Unicode

Test:

```text
Amharic
English
Mixed
Unicode URLs
```

### URL Variations

Test:

```text
Normal URL
Suspicious URL
Shortened URL
IP URL
Lookalike domain
```

### False Positives

Test legitimate messages that contain:

```text
bank
account
payment
verification
```

The system should not automatically classify them as malicious merely because these words appear.

---

# 10. Day 5 — Presentation Preparation

Create a simple demonstration flow.

## Demo Scenario

### Step 1

Show a simulated suspicious message:

```text
እንኳን ደስ አለዎት!

You have won 50,000 ETB.

Click the link below to claim your prize.
```

### Step 2

Submit it to the application.

### Step 3

Show:

```text
HIGH RISK
```

### Step 4

Show why:

```text
• Unexpected financial reward
• Urgency / call to action
• Suspicious link
• Amharic-English code switching
```

### Step 5

Show the recommendation:

```text
Do not click the link.
Do not provide financial or personal information.
Verify the claim through an official channel.
```

### Step 6

Show a benign message.

Demonstrate that the system does not simply classify everything as dangerous.

### Step 7

Show an Amharic-English code-switched example.

This demonstrates the project's main research differentiator.

---

# 11. Day 5 — Research Evidence

Prepare a small results summary.

Example structure:

```text
Dataset
-------
Total samples: [actual number]

English: [actual number]
Amharic: [actual number]
Mixed: [actual number]

Model
-----
TF-IDF + Logistic Regression

Results
-------
Accuracy: [measured value]
Precision: [measured value]
Recall: [measured value]
F1: [measured value]
```

Do not invent performance numbers.

Only report measurements produced by actual experiments.

---

# 12. Day 5 — Documentation

Update:

```text
README.md
docs/architecture.md
docs/threat-model.md
docs/research-question.md
docs/roadmap.md
```

The README should explain:

1. What the project is
2. Why it matters
3. Main features
4. Architecture
5. Supported languages
6. How to run it
7. Research question
8. Current MVP limitations
9. Future work

---

# 13. Day 5 — GitHub Cleanup

Before the final commit:

```text
Remove:
- Temporary files
- Debug output
- Secrets
- API keys
- Personal information
- Unnecessary generated files
```

Add a `.gitignore`.

Never commit:

```text
.env
API keys
passwords
private credentials
personal datasets
private messages
```

Then:

```text
git status
git add .
git commit -m "Complete five-day MVP"
git push origin main
```

---

# 14. Final MVP Definition of Done

The five-day MVP is considered complete when all critical requirements below work.

## Core Detection

* [ ] English messages can be analyzed
* [ ] Amharic messages can be analyzed
* [ ] Amharic-English mixed messages can be analyzed
* [ ] Benign messages can be analyzed
* [ ] Phishing/scam messages can be analyzed
* [ ] Suspicious URLs can be analyzed

## AI/NLP

* [ ] Dataset exists
* [ ] Preprocessing works
* [ ] Language detection works
* [ ] Code-switch detection works
* [ ] ML baseline works
* [ ] Evaluation metrics are recorded

## Cybersecurity

* [ ] Security rules work
* [ ] URL extraction works
* [ ] URL analysis works
* [ ] Risk engine works
* [ ] Threat categories work
* [ ] Indicators are returned

## User Experience

* [ ] Android application works
* [ ] Message input works
* [ ] Analysis request works
* [ ] Result screen works
* [ ] Explanation is displayed
* [ ] Recommendation is displayed

## Research

* [ ] Research question defined
* [ ] Dataset documented
* [ ] Evaluation methodology documented
* [ ] Baseline results recorded
* [ ] Limitations documented

## Demonstration

* [ ] Benign example works
* [ ] English phishing example works
* [ ] Amharic example works
* [ ] Code-switched example works
* [ ] Suspicious URL example works
* [ ] Full mobile-to-backend-to-result flow works

---

# 15. Five-Day Final Schedule

| Day       | Main Goal                  | Person 1                                    | Person 2                                             |
| --------- | -------------------------- | ------------------------------------------- | ---------------------------------------------------- |
| **Day 1** | Foundation                 | Backend, rules, URL foundation, risk engine | Dataset, preprocessing, language detection, ML setup |
| **Day 2** | AI/NLP                     | Backend integration, rules                  | ML training, evaluation, error analysis              |
| **Day 3** | Cybersecurity intelligence | URL analysis, threat logic, risk engine     | NLP improvement, model/error analysis                |
| **Day 4** | Mobile                     | API stabilization                           | Flutter application + integration                    |
| **Day 5** | Final MVP                  | Integration, testing, security review       | UI testing, demo, documentation                      |

---

# 16. Priority Rule

If the team runs out of time, features should be prioritized in this order:

### P0 — Must Work

```text
Message input
      ↓
API
      ↓
Detection
      ↓
Risk assessment
      ↓
Explanation
```

### P1 — Important

```text
English
Amharic
Code-switching
Security rules
URL analysis
Mobile interface
```

### P2 — Nice to Have

```text
Share-to-analyze
Screenshot/OCR
External threat intelligence
Advanced ML models
Automatic SMS monitoring
```

P2 features must never delay the completion of the core MVP.

---

# 17. Five-Day Deliverable

At the end of the five days, the team should have:

```text
                 MULTILINGUAL AI
                CYBER-SAFETY ASSISTANT

                         │
                         ▼

              ┌─────────────────────┐
              │    Android App      │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   FastAPI Backend   │
              └──────────┬──────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
          AI/NLP       Rules        URL
            │            │            │
            └────────────┼────────────┘
                         ▼
                   Risk Engine
                         │
                         ▼
              ┌─────────────────────┐
              │   Security Result   │
              │                     │
              │ SAFE                │
              │ SUSPICIOUS          │
              │ HIGH RISK           │
              │                     │
              │ Why?                │
              │ What should I do?   │
              └─────────────────────┘
```

The five-day objective is **not** to build the final product.

The objective is to prove that the central idea works:

> **A user can submit an English, Amharic, or Amharic-English digital message and receive a meaningful, explainable cybersecurity assessment from a working mobile prototype.**
