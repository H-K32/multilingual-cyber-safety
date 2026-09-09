# Dataset Quality Report

## 1. Dataset Overview

The current dataset contains 30 synthetic messages for the multilingual
cyber-safety detection project.

The dataset contains three main labels:

- BENIGN
- PHISHING
- SCAM

It also contains English, Amharic, and mixed-language messages.

## 2. Dataset Structure

The dataset contains the following columns:

- id
- text
- label
- language
- code_switched
- threat_type
- indicators
- source

All required columns are present.

## 3. Validation Results

The dataset was validated using `ml/validate_dataset.py`.

Results:

- Total rows: 30
- Total columns: 8
- Duplicate IDs: 0
- Duplicate messages: 0
- Missing text values: 0
- Missing label values: 0
- Missing language values: 0
- Missing threat type values: 0

The `indicators` field contains 15 empty values. These correspond to
benign messages and are acceptable because benign messages do not
necessarily contain threat indicators.

## 4. Label Distribution

| Label    | Number |
| -------- | -----: |
| BENIGN   |     15 |
| SCAM     |      9 |
| PHISHING |      6 |
| Total    |     30 |

## 5. Language Distribution

| Language | Number |
| -------- | -----: |
| ENGLISH  |     10 |
| AMHARIC  |     10 |
| MIXED    |     10 |
| Total    |     30 |

## 6. Threat Type Distribution

| Threat Type         | Number |
| ------------------- | -----: |
| NONE                |     15 |
| CREDENTIAL_PHISHING |      6 |
| PRIZE_SCAM          |      3 |
| JOB_SCAM            |      3 |
| DELIVERY_SCAM       |      3 |

## 7. Source

All 30 messages are currently marked as:

`SYNTHETIC`

This dataset is therefore suitable for developing and testing the initial
pipeline, but it is not large or diverse enough to make reliable claims
about real-world model performance.

## 8. Limitations

The current dataset is small and synthetic. A larger dataset should be
created before final model evaluation.

Future data should include:

- More English messages
- More Amharic messages
- More mixed-language messages
- Benign messages
- Phishing messages
- Scam messages
- Messages with and without URLs
- Messages with and without monetary amounts
- Messages requesting OTPs or credentials
- Formal and informal messages
- Spelling variations
- Code-switched messages
- Transliterated Amharic

## 9. Conclusion

The current dataset passed the basic structural and quality checks.
It can now be used to develop the preprocessing, language detection,
and initial machine-learning pipeline.
