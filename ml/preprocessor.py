import re
import pandas as pd


class MessagePreprocessor:
    """Handles dual-text preprocessing and security metadata extraction for Amharic/English messages."""

    # Regex patterns for token replacements
    URL_PATTERN = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    MENTION_PATTERN = re.compile(r"@[A-Za-z0-9_]+")

    # Matches currency symbols, ETB, Birr, birr, and Ethiopic ብር alongside numbers or standalones
    CURRENCY_PATTERN = re.compile(
        r"(\$|£|€|ETB|Birr|birr|BIRR|ብር)\s?\d+(?:,\d{3})*(?:\.\d+)?|\b\d+(?:,\d{3})*(?:\.\d+)?\s?(ETB|Birr|birr|BIRR|ብር|\$|£|€)\b",
        re.IGNORECASE,
    )

    NUMBER_PATTERN = re.compile(r"\b\d+\b")

    # Regex patterns for feature extraction
    ALL_CAPS_PATTERN = re.compile(r"\b[A-Z]{2,}\b")

    def __init__(self):
        pass

    def extract_features(self, text: str) -> dict:
        """Extracts structured cybersecurity metadata from raw text."""

        # 1. Check URLs
        urls = self.URL_PATTERN.findall(text)
        has_url = len(urls) > 0

        # 2. Check Mentions (@user)
        mentions = self.MENTION_PATTERN.findall(text)
        has_mention = len(mentions) > 0

        # 3. Check Currency Mentions
        currencies = self.CURRENCY_PATTERN.findall(text)
        has_currency = len(currencies) > 0

        # 4. Check ALL-CAPS Words (Shouting / Urgency indicator)
        all_caps_words = self.ALL_CAPS_PATTERN.findall(text)
        is_shouting = len(all_caps_words) > 0

        # 5. Check Suspicious / Special Unicode (e.g., zero-width spaces, non-standard control chars)
        # Ethiopic Unicode range: U+1200 to U+137F, Supplement: U+1380 to U+139F, Extended: U+2D80 to U+2DDF
        # Basic Latin & Latin-1 Supplement: U+0000 to U+00FF
        suspicious_unicode_count = sum(
            1
            for char in text
            if ord(char) > 127
            and not (0x1200 <= ord(char) <= 0x139F)
            and not (0x2D80 <= ord(char) <= 0x2DDF)
            and not (0x00A0 <= ord(char) <= 0x00FF)
        )

        return {
            "has_url": has_url,
            "url_count": len(urls),
            "has_mention": has_mention,
            "has_currency": has_currency,
            "is_shouting": is_shouting,
            "all_caps_count": len(all_caps_words),
            "suspicious_unicode_count": suspicious_unicode_count,
        }

    def normalize_text(self, text: str) -> str:
        """Normalizes raw text into ML-ready standardized tokens."""
        normalized = text

        # Order matters: replace URLs and currencies before generic numbers
        normalized = self.URL_PATTERN.sub("<URL>", normalized)
        normalized = self.CURRENCY_PATTERN.sub("<CURRENCY>", normalized)
        normalized = self.MENTION_PATTERN.sub("<MENTION>", normalized)
        normalized = self.NUMBER_PATTERN.sub("<NUM>", normalized)

        return normalized

    def process_message(self, text: str) -> dict:
        """Processes a single message, returning original, normalized, and extracted metadata."""
        features = self.extract_features(text)
        features["original_text"] = text
        features["normalized_text"] = self.normalize_text(text)
        return features

    def process_dataframe(
        self, df: pd.DataFrame, text_column: str = "text"
    ) -> pd.DataFrame:
        """Processes an entire pandas DataFrame containing text messages."""
        processed_records = df[text_column].apply(self.process_message).tolist()
        features_df = pd.DataFrame(processed_records)

        result_df = pd.concat(
            [
                df.reset_index(drop=True),
                features_df.drop(columns=["original_text"]),
            ],
            axis=1,
        )
        return result_df


if __name__ == "__main__":
    # Test with both English and Amharic currency formats
    sample_msgs = [
        "Congratulations! You won 50000 Birr from Telebirr!",
        "እንኳን ደስ አለዎት! የ 10000 ብር ሽልማት አሸንፈዋል",
        "URGENT! Your account is locked. Click http://secure-bank.com",
    ]

    preprocessor = MessagePreprocessor()
    print("--- UPDATED PREPROCESSOR TEST ---")
    for msg in sample_msgs:
        res = preprocessor.process_message(msg)
        print(f"Original   : {res['original_text']}")
        print(f"Normalized : {res['normalized_text']}")
        print(f"Currency?   : {res['has_currency']}")
        print("-" * 40)