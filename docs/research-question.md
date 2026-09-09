# Multilingual AI Cyber-Safety Assistant — Research Question

## 1. Research Problem

Phishing, scams, and social-engineering attacks increasingly target users through digital communication channels such as SMS, email, and messaging applications.

Most existing detection approaches are primarily designed around English-language data and may perform poorly when users communicate in other languages or switch between languages within the same message.

In Ethiopia, digital communication frequently involves both Amharic and English, including code-switched messages.

For example:

```text
እንኳን ደስ አለዎት! You have won 50,000 ETB.
Click here to claim your prize.
```

Traditional security systems may focus heavily on English-language keywords or previously known malicious indicators. This creates a research opportunity to investigate whether multilingual and code-switch-aware analysis can improve detection of phishing and social-engineering attacks.

The project therefore proposes a multilingual AI-powered cyber-safety assistant that combines machine learning, cybersecurity rules, URL analysis, and explainable risk assessment.

---

## 2. Main Research Question

> **Can an AI-powered multilingual system effectively detect phishing and social-engineering attacks in English, Amharic, and Amharic-English code-switched digital communications?**

---

## 3. Secondary Research Questions

### RQ1 — Language Performance

How does phishing and scam detection performance differ between:

* English messages
* Amharic messages
* Amharic-English code-switched messages?

---

### RQ2 — Code-Switching

Does explicitly accounting for Amharic-English code-switching improve detection performance compared with an English-oriented baseline?

---

### RQ3 — Detection Architecture

Does combining machine-learning predictions with cybersecurity rules and URL analysis improve detection compared with using an ML model alone?

The comparison will consider:

```text
ML only
        vs.
ML + Security Rules
        vs.
ML + Security Rules + URL Analysis
```

---

### RQ4 — Explainability

Can the system provide useful and understandable explanations for suspicious classifications?

The explanation should identify security indicators such as:

* Suspicious URLs
* Urgency
* Credential requests
* Financial requests
* Impersonation
* Unexpected rewards
* Account verification requests

---

### RQ5 — Robustness

How robust is the system against common evasion techniques such as:

* Misspellings
* Character substitution
* Unicode manipulation
* Spacing manipulation
* URL shortening
* Language switching
* Social-engineering wording changes?

---

### RQ6 — Human Cyber Resilience

Can explainable warnings and educational feedback help users better recognize phishing and scam indicators?

This question may be evaluated through a small controlled user study if time, participants, and ethical approval requirements permit.

---

## 4. Research Objectives

### Primary Objective

Develop and evaluate a multilingual AI-powered cybersecurity assistant capable of detecting phishing, scams, and social-engineering attacks in English, Amharic, and Amharic-English code-switched digital communications.

### Specific Objectives

1. Develop a dataset containing benign and malicious digital messages in English, Amharic, and mixed-language formats.

2. Develop an initial multilingual text-processing pipeline.

3. Implement a machine-learning baseline for phishing and scam classification.

4. Develop cybersecurity rules for detecting common social-engineering indicators.

5. Develop a URL-analysis component for identifying suspicious links.

6. Develop a risk engine that combines multiple security signals.

7. Provide understandable explanations for suspicious classifications.

8. Develop a mobile-first prototype for practical message analysis.

9. Evaluate detection performance using standard machine-learning metrics.

10. Evaluate system robustness against selected adversarial variations.

11. Investigate whether the system can support human cyber resilience through educational feedback.

---

## 5. Research Hypotheses

### H1 — Multilingual Detection

A multilingual detection approach can effectively classify phishing and scam messages written in English, Amharic, and Amharic-English code-switched text.

---

### H2 — Code-Switching

A detection approach that explicitly accounts for code-switching will perform better on Amharic-English mixed messages than an English-oriented baseline.

---

### H3 — Layered Detection

Combining machine-learning predictions with security rules and URL analysis will provide better overall detection performance than relying on the machine-learning model alone.

---

### H4 — Explainability

Providing understandable security indicators and recommendations will improve users' ability to recognize why a message is suspicious.

H4 should only be claimed as supported if a properly designed user evaluation provides evidence.

---

## 6. Independent Variables

Potential independent variables include:

* Message language
* Code-switching status
* Detection architecture
* ML model
* Security-rule configuration
* URL-analysis availability
* Message obfuscation technique

Example language categories:

```text
English
Amharic
Amharic-English Mixed
```

Example architecture categories:

```text
ML only
ML + Rules
ML + Rules + URL Analysis
```

---

## 7. Dependent Variables

The primary evaluation metrics will include:

### Accuracy

Overall proportion of correctly classified messages.

### Precision

The proportion of messages classified as malicious that are actually malicious.

### Recall

The proportion of malicious messages correctly detected.

### F1-Score

The harmonic mean of precision and recall.

### Confusion Matrix

Used to understand errors between classes.

### False Positive Rate

The proportion of legitimate messages incorrectly classified as suspicious or malicious.

### False Negative Rate

The proportion of malicious messages incorrectly classified as safe.

For a security product, false negatives are particularly important because missed attacks may expose users to harm.

---

## 8. Evaluation Dataset

The dataset should contain multiple categories of messages.

### Benign

Examples of legitimate communication such as:

* Normal conversations
* Legitimate service notifications
* Genuine delivery notifications
* Normal employment communication
* Legitimate financial notifications

### Phishing

Examples involving:

* Credential theft
* Fake login pages
* Account verification
* Password requests
* OTP requests

### Scams

Examples involving:

* Financial scams
* Prize scams
* Fake jobs
* Investment scams
* Delivery scams

### Social Engineering

Examples involving:

* Impersonation
* Urgency
* Fear
* Authority
* Trust exploitation

The dataset should contain:

```text
English
Amharic
Amharic-English mixed
```

where possible.

---

## 9. Dataset Quality Requirements

The dataset should be carefully documented.

Each sample should contain metadata such as:

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

Example:

```text
id: 001
text: "እንኳን ደስ አለዎት! You won 50,000 ETB."
label: SCAM
language: MIXED
code_switched: true
threat_type: PRIZE_SCAM
indicators: financial_reward, call_to_action
source: SYNTHETIC
```

The project should distinguish between:

* Public datasets
* Publicly documented examples
* Synthetic examples
* Human-generated examples
* Other ethically obtained data

No private user conversations should be collected without appropriate consent and safeguards.

---

## 10. Experimental Design

The project will use controlled experiments to compare different detection approaches.

### Experiment 1 — Baseline

Train and evaluate a basic text-classification model.

```text
Message
   ↓
Preprocessing
   ↓
TF-IDF
   ↓
Logistic Regression / Linear SVM
   ↓
Classification
```

---

### Experiment 2 — Multilingual Evaluation

Evaluate performance separately on:

```text
English
Amharic
Amharic-English Mixed
```

This will determine whether performance differs significantly between language groups.

---

### Experiment 3 — Layered Detection

Compare:

```text
Model A:
ML only

Model B:
ML + Security Rules

Model C:
ML + Security Rules + URL Analysis
```

The goal is to determine whether additional cybersecurity signals improve detection.

---

### Experiment 4 — Robustness Testing

Generate controlled variations of malicious messages.

For example:

```text
Original:
Verify your account immediately.

Modified:
V3rify your acc0unt immediately.

Mixed:
አካውንትህን verify አድርግ immediately.
```

The system will be evaluated to determine whether its classification remains consistent.

---

### Experiment 5 — Explainability

Evaluate whether the system can correctly identify relevant indicators behind its classification.

The goal is to ensure that explanations are:

* Relevant
* Understandable
* Consistent with detected signals
* Actionable

---

## 11. Success Criteria

The project will not define arbitrary performance numbers before experiments are conducted.

Instead, success will be determined by measurable improvements over appropriate baselines.

The system should demonstrate:

1. Reliable classification of phishing/scam messages.
2. Measurable support for Amharic messages.
3. Measurable handling of code-switched messages.
4. Improvement from layered security analysis where supported by experiments.
5. Useful URL-analysis signals.
6. Explainable risk assessments.
7. Robustness testing against selected evasion techniques.
8. A functional mobile prototype demonstrating practical use.

The final performance numbers will be reported from actual experiments.

---

## 12. Research Contribution

The project aims to contribute in several areas.

### Multilingual Cybersecurity

Investigating cybersecurity detection for Amharic and mixed Amharic-English communication.

### Code-Switch-Aware Detection

Studying the effect of language switching on phishing and scam detection.

### Layered Detection

Combining:

```text
AI/NLP
+
Cybersecurity Rules
+
URL Intelligence
+
Risk Scoring
```

rather than relying solely on a text classifier.

### Human Cyber Resilience

Turning detection results into understandable warnings and educational guidance.

### Ethiopian Context

Developing and evaluating the system using communication patterns and threat scenarios relevant to Ethiopian digital users.

---

## 13. Research Limitations

The research may be limited by:

* Availability of high-quality Amharic cybersecurity datasets
* Limited labeled code-switched data
* Dataset size
* Synthetic data
* Changing attacker behavior
* Limited access to real-world malicious messages
* Model bias
* Limited user-study participants
* Computational resources

These limitations will be documented in the final research report.

---

## 14. Ethical Considerations

The project will prioritize user privacy and responsible cybersecurity research.

The team will:

* Avoid collecting private communications without consent.
* Avoid testing against systems without authorization.
* Use synthetic or ethically sourced malicious examples when appropriate.
* Avoid storing unnecessary personal information.
* Protect any research data containing sensitive information.
* Clearly communicate system limitations.
* Avoid presenting predictions as guaranteed security decisions.

Any user study involving human participants will follow the applicable university and research-ethics requirements.

---

## 15. Final Research Statement

The project investigates whether a multilingual, code-switch-aware, and layered cybersecurity architecture can improve the detection and explanation of phishing and social-engineering attacks in digital communications used by Ethiopian users.

The final system combines:

```text
Multilingual NLP
       +
Code-Switch Detection
       +
Machine Learning
       +
Cybersecurity Rules
       +
URL Analysis
       +
Risk Assessment
       +
Explainability
       +
Human Cyber Resilience
```

The ultimate goal is to determine, through measurable experimentation, whether this approach can provide practical and meaningful protection against modern social-engineering threats.
