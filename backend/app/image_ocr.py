from io import BytesIO
import os
import warnings

from PIL import Image, UnidentifiedImageError

# On Windows, Tesseract is typically not on PATH — point pytesseract at the
# default install location unless the caller has already set the env variable.
_TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == "nt" and os.path.isfile(_TESSERACT_DEFAULT):
    try:
        import pytesseract as _pt
        if not _pt.pytesseract.tesseract_cmd or _pt.pytesseract.tesseract_cmd == "tesseract":
            _pt.pytesseract.tesseract_cmd = _TESSERACT_DEFAULT
    except ImportError:
        pass


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg"}


class InvalidImageError(ValueError):
    pass


class OCREngineUnavailableError(RuntimeError):
    pass


class OCRProcessingError(RuntimeError):
    pass


def get_available_ocr_languages() -> set[str]:
    """Inspect local Tesseract installation and return set of installed language codes."""
    try:
        import pytesseract
        return set(pytesseract.get_languages())
    except Exception:
        return set()


def determine_ocr_language_config() -> tuple[str, list[str]]:
    """Determine the optimal Tesseract lang parameter and list of active languages.

    Returns:
        (lang_param, active_languages_list)
        e.g. ("amh+eng", ["amh", "eng"]) or ("eng", ["eng"])
    """
    langs = get_available_ocr_languages()
    if "amh" in langs and "eng" in langs:
        return "amh+eng", ["amh", "eng"]
    elif "amh" in langs:
        return "amh", ["amh"]
    else:
        return "eng", ["eng"]


def extract_text_from_image(image_bytes: bytes, content_type: str) -> str:
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise InvalidImageError("Only PNG and JPEG images are supported.")
    if not image_bytes:
        raise InvalidImageError("The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise InvalidImageError("The uploaded image exceeds the 5 MB limit.")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(image_bytes)) as source:
                if source.format not in {"PNG", "JPEG"}:
                    raise InvalidImageError("The image content is not PNG or JPEG.")
                expected_content_type = (
                    "image/png" if source.format == "PNG" else "image/jpeg"
                )
                if content_type != expected_content_type:
                    raise InvalidImageError(
                        "The declared image type does not match the image content."
                    )
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise InvalidImageError("The image dimensions exceed the supported limit.")
                source.verify()

            with Image.open(BytesIO(image_bytes)) as source:
                source.load()
                image = source.convert("RGB")
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise InvalidImageError("The uploaded file is not a readable PNG or JPEG image.") from error
    except Image.DecompressionBombWarning as error:
        raise InvalidImageError("The image dimensions exceed the supported limit.") from error

    # Downscale large images before OCR to reduce processing time on hosted
    # servers (e.g. Render free tier).  Tesseract works well at 1500 px on the
    # long edge; going larger only adds latency without improving accuracy for
    # typical screenshot text.
    MAX_OCR_LONG_EDGE = 1500
    w, h = image.size
    long_edge = max(w, h)
    if long_edge > MAX_OCR_LONG_EDGE:
        scale = MAX_OCR_LONG_EDGE / long_edge
        image = image.resize(
            (int(w * scale), int(h * scale)),
            Image.Resampling.LANCZOS,
        )

    try:
        import pytesseract
    except ImportError as error:
        raise OCREngineUnavailableError(
            "OCR dependencies are unavailable on the server."
        ) from error

    # Use a generous timeout for hosted environments (Render free tier is slow
    # on cold starts).  pytesseract raises RuntimeError on timeout.
    OCR_TIMEOUT = int(os.environ.get("OCR_TIMEOUT_SECONDS", "55"))

    lang_param, _ = determine_ocr_language_config()

    try:
        try:
            text = pytesseract.image_to_string(
                image,
                lang=lang_param,
                config="--psm 6",
                timeout=OCR_TIMEOUT,
            ).strip()
        except pytesseract.TesseractError:
            # If bilingual OCR fails (e.g. missing amh traineddata), fall back safely to eng
            if lang_param != "eng":
                text = pytesseract.image_to_string(
                    image,
                    lang="eng",
                    config="--psm 6",
                    timeout=OCR_TIMEOUT,
                ).strip()
            else:
                raise
    except pytesseract.TesseractNotFoundError as error:
        raise OCREngineUnavailableError(
            "The server OCR engine is not installed or configured."
        ) from error
    except pytesseract.TesseractError as error:
        raise OCRProcessingError("The server could not read text from this image.") from error
    except RuntimeError as error:
        raise OCRProcessingError(
            "OCR timed out on the server. The image may be too large or complex. "
            "Try cropping to just the message text and uploading again."
        ) from error

    if not text:
        raise OCRProcessingError("No readable text was found in the image.")
    if len(text) > 5000:
        raise OCRProcessingError(
            "The image contains more than 5000 characters. Upload a smaller crop."
        )
    return text
