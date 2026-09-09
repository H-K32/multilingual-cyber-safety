import re
import pandas as pd


class UnicodeLanguageDetector:
    """Rule-based language detector for English, Amharic, and Mixed text using Unicode character inspection."""

    # URL regex to strip before language detection
    URL_PATTERN = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )

    def __init__(self, min_letters: int = 3, minor_script_threshold: float = 0.08):
        self.min_letters = min_letters
        self.minor_script_threshold = minor_script_threshold

    @staticmethod
    def is_ethiopic(char: str) -> bool:
        """Check if character belongs to Ethiopic Unicode block."""
        code = ord(char)
        return (0x1200 <= code <= 0x139F) or (0x2D80 <= code <= 0x2DDF)

    @staticmethod
    def is_latin(char: str) -> bool:
        """Check if character is a Latin letter."""
        return ("a" <= char <= "z") or ("A" <= char <= "Z")

    def detect_language(self, text: str) -> dict:
        """Detects language (AMHARIC, ENGLISH, MIXED, UNKNOWN) based on script proportions."""
        # 1. Important: Strip URLs first so Latin URL characters don't dilute Amharic text
        clean_text = self.URL_PATTERN.sub("", str(text))

        ethiopic_count = 0
        latin_count = 0

        for char in clean_text:
            if self.is_ethiopic(char):
                ethiopic_count += 1
            elif self.is_latin(char):
                latin_count += 1

        total_letters = ethiopic_count + latin_count

        # 2. Check if total letter count meets minimum threshold
        if total_letters < self.min_letters:
            return {
                "detected_language": "UNKNOWN",
                "is_code_switched": False,
                "ethiopic_ratio": 0.0,
                "latin_ratio": 0.0,
                "total_letters": total_letters,
            }

        ethiopic_ratio = ethiopic_count / total_letters
        latin_ratio = latin_count / total_letters

        # 3. Classify based on minor script threshold (default 8%)
        if (
            ethiopic_ratio >= self.minor_script_threshold
            and latin_ratio >= self.minor_script_threshold
        ):
            detected_lang = "MIXED"
            is_code_switched = True
        elif ethiopic_ratio > latin_ratio:
            detected_lang = "AMHARIC"
            is_code_switched = False
        else:
            detected_lang = "ENGLISH"
            is_code_switched = False

        return {
            "detected_language": detected_lang,
            "is_code_switched": is_code_switched,
            "ethiopic_ratio": round(ethiopic_ratio, 4),
            "latin_ratio": round(latin_ratio, 4),
            "total_letters": total_letters,
        }

    def process_dataframe(
        self, df: pd.DataFrame, text_column: str = "text"
    ) -> pd.DataFrame:
        """Applies language detection across a DataFrame."""
        results = df[text_column].apply(self.detect_language).tolist()
        results_df = pd.DataFrame(results)

        # Merge with existing dataframe
        return pd.concat([df.reset_index(drop=True), results_df], axis=1)


if __name__ == "__main__":
    detector = UnicodeLanguageDetector()

    sample_texts = [
        "Hello, your bank account is suspended. Click http://scam-link.com",
        "ሰላም፡ የመለያዎ ይለፍ ቃል ተቀይሯል።",
        "ይህ የ Telebirr ማረጋገጫ መልእክት ነው። Your code is 4920.",
        "123456 !!!",
    ]

    print("--- LANGUAGE DETECTOR SANITY CHECK ---")
    for text in sample_texts:
        res = detector.detect_language(text)
        print(f"Text     : {text}")
        print(
            f"Detected : {res['detected_language']} (Ethiopic: {res['ethiopic_ratio']}, Latin: {res['latin_ratio']})"
        )
        print("-" * 50)