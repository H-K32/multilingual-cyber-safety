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
- **[Database Guide](./docs/database.md)** — Neon PostgreSQL schema, concurrency-safe upserts, migrations, and deployment.
- **[Threat Model](./docs/threat-model.md)** — Security analysis covering social engineering vectors and lookalike domains.
- **[ML Evaluation Report](./docs/ML_EVALUATION_REPORT.md)** — Model performance metrics and testing validation.
- **[Roadmap](./docs/roadmap.md)** — Project development milestones.

## 🧪 Testing Summary (5-Case Demo Suite)

1. **Benign Message:** False positive prevention test (`SAFE`).
2. **Benign Code-Switched Chat:** Bilingual context validation (`SAFE`).
3. **Pure Local Scam Lure:** Native Amharic script financial reward fraud (`HIGH RISK`).
4. **Lookalike Domain Phishing:** TLD impersonation and urgency detection (`HIGH RISK`).
5. **The Ultimate Code-Switched Lure:** Core research showcase blending local script with global phishing infrastructure (`HIGH RISK`).

## 🛠️ Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   python -m pip install -r backend/requirements.txt
   ```

3. Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) for screenshot analysis support.

4. Train the model if needed:

   ```bash
   python ml/train_pipeline.py
   ```

5. Configure database connection:

   Set the `DATABASE_URL` environment variable pointing to your Neon PostgreSQL instance:
   ```bash
   export DATABASE_URL="postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"
   ```
   *(Note: Automated tests run with an isolated in-memory mock and do not require a live database).*

6. Start the backend:

   ```bash
   uvicorn backend.app.main:app --reload
   ```

7. Send a request to the analysis endpoint:

   ```bash
   curl -X POST http://127.0.0.1:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"message":"Your account will be suspended. Verify now: http://bit.ly/verify"}'
   ```

## 🔍 Key Features

- **Screenshot OCR analysis** — Upload a PNG/JPEG screenshot; the backend extracts text via Tesseract, runs full risk analysis, and returns phone numbers found in the image with reputation lookups.
- **Phone number reputation** — Check any Ethiopian phone number against the PostgreSQL community-report dataset.
- **Report a number** — Submit suspicious numbers with categories and evidence notes, safely upserted into Neon PostgreSQL.
- **Sender identity verification** — Detects mismatches between the actual sender and a claimed official identity (e.g. a message claiming to be from Ethio Telecom shortcode 994 but arriving from a different number).
- **Multilingual support** — English, Amharic, and code-switched (Amharic-English) message analysis.

## Repository Structure

- `backend/` — FastAPI application, API schemas, OCR, database integration, and phone reputation modules
- `migrations/` — SQL migration scripts (`001_initial_schema.sql`)
- `detection/` — Security rules, URL analysis, and risk scoring engine
- `ml/` — Preprocessing, training, validation, and evaluation scripts
- `dataset/` — Raw and processed message datasets
- `mobile/` — Flutter demo app (Android/iOS/Web)
- `docs/` — Architecture, database guide, and project planning documents
