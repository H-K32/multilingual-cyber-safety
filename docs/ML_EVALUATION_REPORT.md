# Dagu: Risk Scoring Architecture, Dispute Reporting & ML Evaluation Report

## Executive Summary

This report documents the architecture, scoring formula, false-positive dispute workflow, data leakage safeguards, and empirical evaluation of the **Dagu Multilingual Scam and Phishing Detection Engine**. It covers both the heuristic cybersecurity rule engine and the natural language machine learning pipeline across Amharic, English, and code-switched communications.

---

## 1. Risk Scoring Engine Architecture & Breakdown

The Dagu risk scoring engine integrates three complementary analytical layers to evaluate suspicious digital messages:
1. **Deterministic Security Rules**: Regex-based detection of social engineering signals (urgency, intimidation, credential demands, fee requests).
2. **URL Intelligence**: Heuristics for domain masking, IP-address hostnames, lookalike domain spoofing, suspicious TLDs, and missing HTTPS.
3. **Machine Learning Classifier**: Word and character n-gram TF-IDF pipeline paired with a Linear Support Vector Classifier predicting communication intent (`BENIGN`, `PHISHING`, `SCAM`).

### Scoring Logic

```text
base_score = min(rule_score + url_score + sender_score + ml_score, 100)
```

- **Rule Score**: Sum of triggered message rule indicators (`INDICATOR_SCORES`), capped at 100.
- **URL Score**: Sum of triggered URL indicators, capped at 100.
- **Sender Verification Score**: +25 points if sender identity fails official organization whitelist verification.
- **ML Contribution**: `int(ml_prob * 40)` if the ML classifier predicts `PHISHING` or `SCAM`, where `ml_prob` is the model's confidence probability.
- **High-Severity Overrides**:
  - Direct credential harvesting vectors (e.g. `credential_request` + `lookalike_domain` or `ip_address_url`) enforce a minimum score of 85 (`HIGH_RISK`).
  - ML intent escalation: If ML predicts `PHISHING` or `SCAM` with high confidence, an otherwise `SAFE` message is elevated to `SUSPICIOUS` (minimum score of 45).
  - Sender mismatch escalation: Unverified sender identities claiming official status elevate `SAFE` to `SUSPICIOUS` (minimum score of 55).

### Risk Classification Thresholds

| Risk Score Range | Classification | User Guidance |
| :--- | :--- | :--- |
| **0 – 34** | `SAFE` | No critical threat indicators found; practice standard awareness. |
| **35 – 69** | `SUSPICIOUS` | Suspicious signals present; verify independently before trusting. |
| **70 – 100** | `HIGH_RISK` | High-confidence fraud or phishing vector; do not click or reply. |

### Heuristic Scoring vs. Calibrated Probabilities

> [!IMPORTANT]
> The `risk_score` (0–100) is a **deterministic heuristic threat index**, not a statistically calibrated empirical probability.
> 
> The system explicitly declares `"is_statistically_calibrated": False` in all API responses (`risk_breakdown`). It represents a cumulative threat weight calibrated against cybersecurity risk heuristics, rather than a Bayesian probability of fraud.

---

## 2. False-Positive & Dispute Reporting Architecture (Phase 4)

To prevent reputation poisoning, false positives, and abuse against recycled or legitimate numbers, Dagu provides a secure dispute workflow.

### Key Architectural Principles

1. **Non-Automatic Clearing Guarantee**: Submitting a dispute **never** erases community reports, resets report counts, or marks a number safe. It queues the dispute for administrative moderation review. Community threat visibility is preserved until human or cryptographic verification occurs.
2. **Strict Privacy & Data Isolation**: Personal contact information (email, callback phone) and dispute explanation text are stored exclusively in the isolated `phone_number_disputes` table. Public lookup endpoints (`/check-number`, `/reported-numbers`) query `phone_number_summary` only and never leak dispute PII or explanations.
3. **Anti-Abuse Rate Limiting**: The `POST /dispute` endpoint is protected by a sliding-window rate limiter per client IP:
   - Burst limit: 5 requests per 60 seconds
   - Hourly limit: 20 requests per 3600 seconds
   - Rejections return HTTP 429 with standard `Retry-After` headers.
4. **Discreet Flutter UI Action**: In the Flutter client, reported numbers feature a subtle *"Report inaccurate status"* (`Icons.flag_outlined`) button that presents an accessible modal sheet explaining the review process, gathering input, and providing clear user feedback.

### PostgreSQL Dispute Schema (`phone_number_disputes`)

```sql
CREATE TABLE IF NOT EXISTS phone_number_disputes (
    id                  SERIAL PRIMARY KEY,
    phone_e164          TEXT        NOT NULL,
    country_code        TEXT        NOT NULL,
    explanation         TEXT        NOT NULL,
    contact_info        TEXT,
    review_status       TEXT        NOT NULL DEFAULT 'pending'
                            CHECK (review_status IN ('pending', 'under_review', 'resolved', 'rejected')),
    reporter_hash       TEXT,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_disputes_phone ON phone_number_disputes (phone_e164);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON phone_number_disputes (review_status, submitted_at);
```

---

## 3. Dataset Expansion & Data Leakage Safeguards (Phase 5)

### Dataset Composition (`dataset/raw/messages.csv`)

The dataset was expanded from 257 rows (256 annotated) to **302 rows (301 annotated, 1 `NEEDS_REVIEW`)** through carefully authored examples addressing observed failure modes:

| Metric | Baseline Dataset | Expanded Dataset | Change |
| :--- | :---: | :---: | :---: |
| **Total Rows** | 257 | 302 | +45 |
| **Evaluation Rows** | 256 | 301 | +45 |
| **BENIGN Samples** | 83 (32.4%) | 110 (36.5%) | +27 |
| **PHISHING Samples** | 90 (35.2%) | 96 (31.9%) | +6 |
| **SCAM Samples** | 83 (32.4%) | 95 (31.6%) | +12 |
| **English Samples** | 85 (33.2%) | 100 (33.2%) | +15 |
| **Amharic Samples** | 94 (36.7%) | 109 (36.2%) | +15 |
| **Mixed Samples** | 77 (30.1%) | 92 (30.6%) | +15 |
| **Effective Template Groups** | 44 | 51 | +7 |

### Template Groups Added

1. **`security_education_tips` (BENIGN)**: Legitimate security reminders from CBE, telebirr, and cybersecurity advisors warning users never to share OTPs or PINs.
2. **`legitimate_banking_receipt` (BENIGN)**: Real-world debit, credit, and transfer receipts from Ethiopian commercial banks with reference codes.
3. **`telecom_service_notice` (BENIGN)**: Package renewal, expiry, and airtime recharge confirmations with standard USSD codes (*999#).
4. **`legitimate_recruitment_notice` (BENIGN)**: Legitimate job announcements explicitly stating no application fee or payment is required.
5. **`urgent_account_action` (PHISHING)**: Subtle credential extraction attempts simulating session expiration or wallet restrictions.
6. **`investment_opportunity_lure` (SCAM)**: Telegram trading channels and fake high-yield crypto schemes soliciting registration deposits.
7. **`lottery_advance_fee` (SCAM)**: National lottery and giveaway notifications demanding handling or stamp fees.

### Strict Data Leakage Prevention

In phishing and scam detection, multiple samples frequently share underlying sentence structures. Splitting data with standard random K-fold allows template variants to appear in both training and test folds, resulting in memorization rather than generalization.

Dagu strictly enforces **5-Fold Stratified Group Cross-Validation (`StratifiedGroupKFold`)**:
- All 301 samples are partitioned across **51 effective template groups**.
- Folds are strictly isolated by group:
  $$\text{Train Groups} \cap \text{Validation Groups} = \emptyset$$
- The evaluation harness programmatically verifies group boundaries before training each fold.

---

## 4. Empirical ML Evaluation Results

### Model Comparison Across 5-Fold Stratified Group CV

| Model Architecture | Accuracy | Macro-F1 | Weighted-F1 | Weighted Precision | Weighted Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Linear SVM (Retrained)** | **92.03%** | **0.9207** | **0.9202** | **0.9216** | **92.03%** |
| **Calibrated Linear SVM** | 90.70% | 0.9077 | 0.9067 | 0.9073 | 90.70% |
| **Logistic Regression** | 89.04% | 0.8909 | 0.8903 | 0.8924 | 89.04% |

### Baseline vs. Expanded Dataset Comparison (Linear SVM)

| Metric | Baseline (256 Eval Rows) | Expanded (301 Eval Rows) | Net Improvement |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | 90.62% | **92.03%** | **+1.41%** |
| **Macro-F1** | 0.9057 | **0.9207** | **+0.0150** |
| **Weighted-F1** | 0.9059 | **0.9202** | **+0.0143** |
| **BENIGN F1-Score** | 0.8861 | **0.9108** | **+0.0247** |
| **PHISHING F1-Score** | 0.9119 | **0.9146** | **+0.0027** |
| **SCAM F1-Score** | 0.9193 | **0.9368** | **+0.0175** |
| **English Macro-F1** | 0.9071 | **0.9228** | **+0.0157** |
| **Amharic Macro-F1** | 0.8916 | **0.8993** | **+0.0077** |
| **Mixed Macro-F1** | 0.9201 | **0.9411** | **+0.0210** |

### Per-Class Performance Breakdown (Expanded Linear SVM)

| Class | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **BENIGN** | 0.9417 | 0.8818 | 0.9108 | 110 |
| **PHISHING** | 0.8835 | 0.9479 | 0.9146 | 96 |
| **SCAM** | 0.9368 | 0.9368 | 0.9368 | 95 |

### Per-Language Performance Breakdown (Expanded Linear SVM)

| Language | Sample Count ($n$) | Accuracy | Macro-F1 | Weighted-F1 |
| :--- | :---: | :---: | :---: | :---: |
| **ENGLISH** | 100 | 92.00% | 0.9228 | 0.9199 |
| **AMHARIC** | 109 | 89.91% | 0.8993 | 0.8981 |
| **MIXED** (Code-switched) | 92 | 94.57% | 0.9411 | 0.9461 |

### Confusion Matrix (Out-of-Fold Predictions on 301 Samples)

Rows represent ground-truth labels; columns represent model predictions:

```text
                  Predicted BENIGN   Predicted PHISHING   Predicted SCAM
True BENIGN              97                  9                  4
True PHISHING             3                 91                  2
True SCAM                 3                  3                 89
```

---

## 5. Error Case Analysis & Insights

Across 301 out-of-fold cross-validation evaluations, exactly 24 errors occurred:

1. **Resolution of Security Advice False Positives**:
   - In the baseline model, 9 benign security advice messages were flagged as phishing because words like `"OTP"` and `"PIN"` had high unigram weights.
   - On the expanded model, the ML pipeline correctly learns that security reminders advising *against* credential disclosure are `BENIGN` (e.g., `"Security Alert from CBE: Never share your mobile banking PIN or OTP"` produces an ML prediction of `BENIGN` with 73.8% confidence).
2. **Linguistic Boundary: Keyword Heuristics vs. ML Intent**:
   - While the retrained ML pipeline correctly recognizes security advice as `BENIGN`, the static regex rule engine (`_CREDENTIAL_PATTERNS`) flags the literal presence of `"OTP"` or `"PIN"`. This highlights the architectural necessity of explainable hybrid scoring: users can see the exact rule breakdown and ML prediction side-by-side rather than a mysterious black-box score.
3. **Scam vs. Phishing Border Cases (5 samples)**:
   - Certain delivery fee scams requesting nominal payment via web links share syntactic features with credential collection forms (`delivery_fee` template).
4. **Subtle Conversational Scams (6 samples)**:
   - Low-urgency investment and loan offers in Amharic without explicit scam trigger words remain the most challenging category for bag-of-words/character n-grams.

---

## 6. Summary & Remaining Limitations

1. **Dataset Volume**: 302 samples provides a verified, leak-free evaluation benchmark. Future expansion should target 1,000+ real-world community submissions from the Dagu reporting pipeline.
2. **Transliterated Amharic (Latin Script)**: Amharic written using the Latin alphabet (e.g. *"telebirr accountih tasegwal"*) is detected as English script. Character n-grams (3-5 grams) provide partial signal, but dedicated phonetic Fidel-Latin normalization is recommended for Phase 6.
3. **Statistical Probability Calibration**: Scores are deterministic heuristic threat indices. In future releases with a multi-thousand sample validation corpus, Platt scaling or isotonic regression will map threat indices to calibrated empirical probabilities.
