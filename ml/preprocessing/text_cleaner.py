# ml/preprocessing/text_cleaner.py

import re
import unicodedata
from typing import Dict, List, Any

ETHIOPIC_PATTERN = re.compile(r'[\u1200-\u137F]')
LATIN_PATTERN = re.compile(r'[a-zA-Z]')
URL_PATTERN = re.compile(r'https?://[^\s፡።]+|www\.[^\s፡።]+')
CURRENCY_PATTERN = re.compile(
    r'(\d+(?:,\d+)*(?:\.\d+)?\s*(?:ETB|USD|EUR|GBP|ብር))|(?:[$€£]\s*\d+(?:,\d+)*(?:\.\d+)?)', 
    re.IGNORECASE
)
NUMBER_PATTERN = re.compile(r'\b\d+\b')

def normalize_amharic_homophones(text: str) -> str:
    """Standardizes interchangeable Amharic characters (Fidels)."""
    text = re.sub(r'[ሐኀኻ፡ኃሐሓ]', 'ሀ', text)
    text = re.sub(r'[ሑኁዅ]', 'ሁ', text)
    text = re.sub(r'[ኂሒኺ]', 'ሂ', text)
    text = re.sub(r'[ኌሔዄ]', 'ሄ', text)
    text = re.sub(r'[ሕኅ]', 'ህ', text)
    text = re.sub(r'[ኆሖኾ]', 'ሆ', text)
    text = re.sub(r'[ሠ]', 'ሰ', text)
    text = re.sub(r'[ሡ]', 'ሱ', text)
    text = re.sub(r'[ሢ]', 'ሲ', text)
    text = re.sub(r'[ሣ]', 'ሳ', text)
    text = re.sub(r'[ሤ]', 'ሴ', text)
    text = re.sub(r'[ሥ]', 'ስ', text)
    text = re.sub(r'[ሦ]', 'ሶ', text)
    text = re.sub(r'[ዓዐኣ]', 'አ', text)
    text = re.sub(r'[ጸ]', 'ፀ', text)
    return text

def preprocess_message(raw_text: str) -> Dict[str, Any]:
    """Cleans text while preserving critical security indicators."""
    sanitized = unicodedata.normalize('NFC', raw_text)
    sanitized = re.sub(r'[\u200B-\u200D\uFEFF]', '', sanitized)
    
    urls = URL_PATTERN.findall(sanitized)
    normalized = normalize_amharic_homophones(sanitized)
    currencies = [m.group(0) for m in CURRENCY_PATTERN.finditer(normalized)]
    
    processed = URL_PATTERN.sub(' [URL] ', normalized)
    processed = CURRENCY_PATTERN.sub(' [CURRENCY] ', processed)
    processed = NUMBER_PATTERN.sub(' [NUMBER] ', processed)
    
    tokens = []
    for token in processed.split():
        if re.search(LATIN_PATTERN, token) and not token.startswith('['):
            tokens.append(token.lower())
        else:
            tokens.append(token)
            
    cleaned_text = " ".join(tokens)
    
    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "extracted_urls": urls,
        "has_currency": len(currencies) > 0,
        "currency_matches": currencies,
    }