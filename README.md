# Multilingual Cyber-Safety Assistant

## 🚀 Demo Video

Watch the full 5-case live screen recording demonstration here:
👉 [View Demo Video](https://youtu.be/eQ0F_omd05k)

## 📌 Project Overview

The Multilingual Cyber-Safety Assistant is an advanced threat-detection tool engineered to handle modern social engineering and phishing attacks. It provides native support for local script analysis (Amharic) and complex code-switched (Amharic-English mixed) text messages.

## 🗂️ Documentation & Research

For a comprehensive breakdown of the project design, please review the documentation files in the `docs/` directory:

- **[Research Question](./docs/research-question.md)** — Core objectives and the significance of bilingual threat detection.
- **[Architecture](./docs/architecture.md)** — High-level system design bridging the Flutter mobile frontend and FastAPI backend.
- **[Threat Model](./docs/threat-model.md)** — Security analysis covering social engineering vectors and lookalike domains.
- **[ML Evaluation Report](./docs/ML_EVALUATION_REPORT.md)** — Model performance metrics and testing validation.
- **[Roadmap](./docs/roadmap.md)** — Project development milestones.

## 🧪 Testing Summary (5-Case Demo Suite)

1. **Benign Message:** False positive prevention test (`SAFE`).
2. **Benign Code-Switched Chat:** Bilingual context validation (`SAFE`).
3. **Pure Local Scam Lure:** Native Amharic script financial reward fraud (`HIGH RISK`).
4. **Lookalike Domain Phishing:** TLD impersonation and urgency detection (`HIGH RISK`).
5. **The Ultimate Code-Switched Lure:** Core research showcase blending local script with global phishing infrastructure (`HIGH RISK`).
