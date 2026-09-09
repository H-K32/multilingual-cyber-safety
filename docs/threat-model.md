# Multilingual AI Cyber-Safety Assistant — Threat Model

## 1. Purpose

This document defines the threats the Multilingual AI Cyber-Safety Assistant is designed to identify, the indicators used to identify them, the expected users and attackers, and the limitations of the system.

The primary focus is detecting **phishing, scams, social engineering, impersonation, malicious links, and related cyber threats delivered through digital communication**.

The system is designed to improve both:

* Automated threat detection
* Human cyber resilience

---

## 2. Threat Model Scope

The system focuses on threats delivered through messages and other user-provided digital content.

### In Scope

* SMS phishing
* Email phishing
* Messaging-app scams
* Financial scams
* Credential phishing
* Account verification scams
* Prize and reward scams
* Fake job scams
* Delivery/package scams
* Investment scams
* Impersonation attacks
* Malicious or suspicious URLs
* Social-engineering attacks
* Amharic phishing/scam messages
* English phishing/scam messages
* Amharic-English code-switched attacks
* Obfuscated or intentionally modified messages
* Suspicious screenshots containing text or URLs

### Out of Scope for the Initial Version

The system will not attempt to:

* Perform penetration testing
* Exploit websites or applications
* Automatically hack user accounts
* Intercept encrypted communications
* Bypass Android application security
* Bypass WhatsApp or Telegram security controls
* Perform unrestricted network monitoring
* Guarantee that every message is malicious or safe
* Replace professional security analysts

The system is a **cyber-safety and threat-detection assistant**, not an automated penetration-testing platform.

---

## 3. Assets to Protect

The primary assets are the user's:

### Personal Information

* Names
* Addresses
* Phone numbers
* Identity-related information
* Personal conversations

### Authentication Information

* Passwords
* One-time passwords (OTPs)
* Verification codes
* Authentication tokens
* Account credentials

### Financial Information

* Bank account information
* Mobile-money information
* Payment information
* Financial transaction details

### Accounts

* Email accounts
* Social-media accounts
* Messaging accounts
* Banking accounts
* Other online services

### Device Security

The system should help prevent users from:

* Visiting malicious websites
* Installing malicious applications
* Giving attackers credentials
* Sending money to scammers
* Revealing sensitive information

---

## 4. Threat Actors

The system considers several types of attackers.

### 4.1 Cybercriminals

Attackers attempting to:

* Steal credentials
* Steal money
* Obtain personal information
* Distribute malicious links
* Compromise accounts

### 4.2 Scammers

Attackers using social engineering to convince victims to:

* Send money
* Reveal OTPs
* Provide personal information
* Click links
* Contact fraudulent numbers

### 4.3 Impersonators

Attackers pretending to be trusted entities such as:

* Banks
* Government organizations
* Employers
* Delivery companies
* Financial services
* Popular technology companies
* Friends or family members

### 4.4 Opportunistic Attackers

Attackers sending large volumes of generic phishing or scam messages without specifically targeting an individual.

---

## 5. Primary Threat Categories

## 5.1 Credential Phishing

The attacker attempts to obtain:

* Passwords
* Usernames
* OTPs
* Verification codes
* Authentication information

Example:

```text
Your account will be suspended today.
Verify your account immediately:
https://example.com/verify
```

Important indicators:

* Account threat
* Urgency
* Login/verification request
* Suspicious URL
* Credential request

---

## 5.2 Financial Scam

The attacker attempts to convince the victim to provide money or financial information.

Example:

```text
Your bank account requires immediate verification.
Send your OTP to complete the process.
```

Indicators:

* Financial terminology
* Payment request
* Banking references
* OTP requests
* Urgency
* Requests for sensitive information

---

## 5.3 Prize and Reward Scam

The attacker claims that the victim has won money, a prize, or another reward.

Example:

```text
እንኳን ደስ አለዎት!
You have won 50,000 ETB.
Click the link to claim your prize.
```

Indicators:

* Unexpected reward
* Large financial amount
* Call to action
* Suspicious URL
* Urgency

---

## 5.4 Impersonation

The attacker pretends to represent a trusted person or organization.

Possible targets include:

* Banks
* Government agencies
* Employers
* Delivery companies
* Financial institutions
* Technology companies
* Friends or family

Indicators may include:

* Organization names
* Authority language
* Requests for sensitive information
* Suspicious domains
* Urgency

The system should avoid treating the mere mention of a legitimate organization's name as proof of malicious activity.

---

## 5.5 Account Verification Scam

The attacker claims that an account must be verified, updated, unlocked, or restored.

Example:

```text
Your account has unusual activity.
Confirm your identity within 30 minutes.
```

Indicators:

* Account security claims
* Verification requests
* Login links
* Urgency
* Credential requests

---

## 5.6 Fake Job Scam

The attacker uses fake employment opportunities to obtain money or personal information.

Example:

```text
Congratulations! You have been selected for a remote job.
Pay 500 ETB registration fee to continue.
```

Indicators:

* Unexpected job offer
* Payment request
* Requests for personal information
* Unrealistic compensation
* Urgency

---

## 5.7 Delivery Scam

The attacker claims that a package or delivery requires payment or verification.

Example:

```text
Your package could not be delivered.
Pay the delivery fee using the link below.
```

Indicators:

* Delivery claims
* Unexpected package
* Payment request
* Suspicious URL
* Urgency

---

## 5.8 Investment Scam

The attacker promises unrealistic financial returns or investment opportunities.

Indicators:

* Guaranteed profits
* Unrealistic returns
* Urgency
* Requests for payment
* Referral incentives
* Suspicious links

---

## 5.9 Malicious or Suspicious URLs

A message may contain a suspicious link even when the text itself appears relatively normal.

The URL analyzer should inspect signals such as:

* IP address instead of domain name
* URL shortening
* Excessive subdomains
* Unusual domain structure
* Suspicious paths
* Suspicious query parameters
* Lookalike domains
* Unicode/homograph characters
* Punycode
* Credential-related paths
* Known malicious indicators where threat intelligence is available

---

## 6. Social-Engineering Indicators

The system will identify common psychological techniques used by attackers.

### Urgency

Examples:

```text
Act now.
Your account will be closed today.
You have 10 minutes to respond.
```

### Fear

Examples:

```text
Your account has been compromised.
Failure to respond will result in suspension.
```

### Reward

Examples:

```text
You have won a cash prize.
Congratulations! You were selected.
```

### Authority

Examples:

```text
This is an official security notification.
```

### Financial Pressure

Examples:

```text
Send payment immediately.
Pay the required fee to receive your money.
```

### Curiosity

Examples:

```text
Look what I found about you.
Open this photo immediately.
```

### Trust Exploitation

Examples:

* Pretending to be a friend
* Pretending to be a family member
* Pretending to be a bank employee
* Pretending to be an organization representative

---

## 7. Multilingual Threats

A major research focus is the detection of threats written in:

* English
* Amharic
* Amharic-English code-switched language

Example:

```text
Your account ተዘግቷል።
Please verify your account immediately.
```

The system should not assume that English-only security indicators are sufficient.

Threats may use:

* Amharic terminology
* English terminology
* Mixed terminology
* Transliteration
* Numbers
* URLs
* Unicode characters
* Informal language

The system must therefore evaluate both language and cybersecurity characteristics.

---

## 8. Adversarial and Evasion Techniques

Attackers may intentionally modify messages to avoid detection.

The research will evaluate robustness against techniques such as:

### Character Substitution

Replacing characters with visually similar characters.

### Unicode Obfuscation

Using unusual Unicode characters to disguise domains or words.

### Spacing

Example:

```text
V e r i f y   y o u r   a c c o u n t
```

### Punctuation Manipulation

Example:

```text
C.l.i.c.k   h.e.r.e
```

### URL Shortening

Using shortened URLs to hide the destination.

### Language Switching

Changing between Amharic and English within the same message.

### Misspellings

Example:

```text
Your acount has been suspennded.
```

### Social-Engineering Variation

Changing wording while preserving the same underlying attack strategy.

Robustness against these techniques will be evaluated experimentally rather than assumed.

---

## 9. Risk Levels

The system will use three primary user-facing risk levels.

### SAFE

The available evidence does not indicate significant malicious or suspicious behavior.

This does **not** mean the message is guaranteed to be safe.

### SUSPICIOUS

The message contains one or more concerning indicators, but there is insufficient evidence to classify it as highly dangerous.

### HIGH RISK

Multiple strong indicators suggest phishing, fraud, malicious links, or another social-engineering attack.

Example:

```text
HIGH RISK

Threat: Financial Phishing

Indicators:
• Suspicious URL
• OTP request
• Urgency
• Bank impersonation
```

Risk thresholds will be calibrated using evaluation data.

---

## 10. False Positives and False Negatives

The system must explicitly consider both types of errors.

### False Positive

A legitimate message is incorrectly classified as suspicious or malicious.

Example:

```text
Your bank appointment is confirmed.
```

The system should avoid classifying legitimate financial communication as malicious simply because it contains banking terminology.

### False Negative

A malicious message is incorrectly classified as safe.

False negatives are particularly important because failing to identify a real attack can expose users to harm.

The evaluation will therefore prioritize:

* Recall
* Precision
* F1-score
* Confusion matrix
* False-positive rate
* False-negative rate

The appropriate balance between precision and recall will depend on the final system's intended use.

---

## 11. Threat Detection Strategy

The system will use multiple detection layers rather than relying entirely on a single AI model.

```text
Message
   │
   ├── AI/NLP Analysis
   │
   ├── Security Rules
   │
   ├── URL Analysis
   │
   ├── Language Analysis
   │
   └── Threat Intelligence
             │
             ▼
        Risk Engine
             │
             ▼
     Final Assessment
```

This layered approach is intended to reduce dependence on a single detection technique.

---

## 12. Explainability Requirements

Every high-risk or suspicious classification should provide understandable reasons.

The system should identify relevant indicators such as:

```text
• Suspicious URL
• Urgency
• Credential request
• Financial request
• Impersonation
• Unexpected reward
```

The system should then explain these indicators in language understandable to non-security users.

The objective is not only:

```text
"Phishing detected."
```

but:

```text
"This message appears suspicious because it asks for an OTP,
creates urgency, and directs you to an unusual website."
```

---

## 13. Privacy Threats

Because users may submit private communications, the system itself introduces privacy considerations.

Potential risks include:

* Exposure of message contents
* Unnecessary server-side storage
* Logging sensitive information
* Transmission of personal information
* Third-party API exposure

Mitigations include:

* Minimal data collection
* Explicit consent
* Secure communication
* Limited logging
* Data retention controls
* Redaction where appropriate
* Local processing where practical

Privacy will be treated as a core security requirement rather than an optional feature.

---

## 14. System Limitations

The system cannot guarantee perfect detection.

Potential limitations include:

* Previously unseen attack techniques
* Poor-quality messages
* Very short messages with insufficient context
* Ambiguous legitimate messages
* Languages outside the supported language set
* Advanced obfuscation
* New malicious domains
* Lack of threat-intelligence information
* Context that exists outside the analyzed message

The system should therefore communicate uncertainty when appropriate.

---

## 15. Security Objective

The primary security objective is:

> **Reduce the likelihood that users fall victim to phishing, scams, and social-engineering attacks by detecting suspicious digital communications and clearly explaining the risks before the user takes action.**

The secondary objective is:

> **Improve human cyber resilience by teaching users how to recognize common attack indicators themselves.**

---

## 16. Research Objective

The project will investigate whether multilingual and code-switch-aware analysis can improve the detection of phishing and social-engineering attacks in Ethiopian digital communications.

The research will compare different approaches and measure their effectiveness using real evaluation metrics.

The system should ultimately answer:

```text
Can an AI-powered multilingual system effectively detect
phishing and social-engineering attacks in English, Amharic,
and Amharic-English code-switched digital communications?
```
