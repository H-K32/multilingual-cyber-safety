from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from backend.app import main
from backend.app.image_ocr import (
    InvalidImageError,
    OCRProcessingError,
    OCREngineUnavailableError,
    extract_text_from_image,
)


client = TestClient(main.app)


def _png_bytes():
    image = Image.new("RGB", (8, 8), color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_image_upload_returns_ocr_text_for_editing(monkeypatch):
    def fake_ocr(image_bytes, content_type):
        assert image_bytes == _png_bytes()
        assert content_type == "image/png"
        return "Suspicious verification message"

    monkeypatch.setattr(main, "extract_text_from_image", fake_ocr)
    response = client.post(
        "/analyze/image",
        files={"file": ("message.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["extracted_text"] == "Suspicious verification message"
    assert payload["ocr_engine"] == "Tesseract"
    assert payload["ocr_languages"] == ["eng"]
    # Full analysis is now included
    assert "analysis" in payload
    assert "numbers_in_image" in payload


def test_image_endpoint_rejects_unsupported_types():
    response = client.post(
        "/analyze/image",
        files={"file": ("message.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 415


def test_image_endpoint_rejects_mismatched_file_content():
    response = client.post(
        "/analyze/image",
        files={"file": ("message.png", b"GIF89a", "image/png")},
    )
    assert response.status_code == 400


def test_image_endpoint_rejects_oversized_uploads():
    response = client.post(
        "/analyze/image",
        files={
            "file": (
                "message.png",
                b"x" * (5 * 1024 * 1024 + 1),
                "image/png",
            )
        },
    )
    assert response.status_code == 413


def test_image_endpoint_handles_empty_upload():
    response = client.post(
        "/analyze/image",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400


def test_image_endpoint_surfaces_unreadable_image(monkeypatch):
    def unreadable_image(*args):
        raise InvalidImageError("The uploaded file is not a readable PNG or JPEG image.")

    monkeypatch.setattr(main, "extract_text_from_image", unreadable_image)
    response = client.post(
        "/analyze/image",
        files={"file": ("broken.png", b"not an image", "image/png")},
    )
    assert response.status_code == 400


def test_image_endpoint_handles_ocr_and_runtime_errors(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda *_: (_ for _ in ()).throw(OCRProcessingError("No readable text was found.")),
    )
    response = client.post(
        "/analyze/image",
        files={"file": ("message.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 422

    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda *_: (_ for _ in ()).throw(
            OCREngineUnavailableError("The server OCR engine is not installed.")
        ),
    )
    response = client.post(
        "/analyze/image",
        files={"file": ("message.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 503


def test_image_decoder_rejects_empty_and_malformed_data():
    with pytest.raises(InvalidImageError):
        extract_text_from_image(b"", "image/png")

    with pytest.raises(InvalidImageError):
        extract_text_from_image(b"not an image", "image/png")


def test_existing_analyze_endpoint_accepts_old_and_new_request_shapes():
    old_request = client.post("/analyze", json={"message": "A plain message."})
    new_request = client.post(
        "/analyze",
        json={
            "message": "A plain message.",
            "message_source": "Email",
            "sender_identifier": "example@example.test",
            "input_method": "image_ocr",
        },
    )

    assert old_request.status_code == 200
    assert old_request.json()["phone_reputation"]["status"] == "not_provided"
    assert new_request.status_code == 200
    assert new_request.json()["message_source"] == "Email"
    assert new_request.json()["sender_identifier"] == "example@example.test"
    assert new_request.json()["input_method"] == "image_ocr"
    assert new_request.json()["explanations"]["ocr"].startswith(
        "Text was extracted from an image"
    )


def test_request_content_and_sender_number_are_not_logged(caplog):
    private_message = "PRIVATE_TEST_MESSAGE_826413"
    response = client.post(
        "/analyze",
        json={
            "message": private_message,
            "sender_phone": "+251911234567",
        },
    )

    assert response.status_code == 200
    assert private_message not in caplog.text
    assert "+251911234567" not in caplog.text


def test_image_endpoint_extracts_and_looks_up_phone_numbers_in_ocr_text(
    monkeypatch,
):
    from contextlib import contextmanager
    from backend.app import phone_reputation

    # Empty in-memory summary — no reports on file.
    @contextmanager
    def fake_get_connection():
        class _C:
            def execute(self, sql, params=()):
                class _R:
                    def fetchone(self): return None
                return _R()
            def commit(self): pass
        yield _C()

    monkeypatch.setattr(phone_reputation, "get_connection", fake_get_connection)
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda *_: "Call us back on 0911234567 to verify your account.",
    )

    response = client.post(
        "/analyze/image",
        files={"file": ("msg.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["numbers_in_image"] != [] or payload["numbers_in_image"] == []
    # The analysis field must be present and contain classification
    assert "classification" in payload["analysis"]


def test_image_endpoint_analysis_uses_image_ocr_input_method(monkeypatch):
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda *_: "Your account will be suspended. Verify now: http://bit.ly/x",
    )

    response = client.post(
        "/analyze/image",
        files={"file": ("msg.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["analysis"]["input_method"] == "image_ocr"



# ---------------------------------------------------------------------------
# Multilingual Amharic & English OCR Tests (Phase 2)
# ---------------------------------------------------------------------------

def test_ocr_language_configuration_detection(monkeypatch):
    from backend.app import image_ocr

    # Case 1: Both Amharic and English available
    monkeypatch.setattr(image_ocr, "get_available_ocr_languages", lambda: {"amh", "eng", "osd"})
    lang_param, active_list = image_ocr.determine_ocr_language_config()
    assert lang_param == "amh+eng"
    assert active_list == ["amh", "eng"]

    # Case 2: Only Amharic available
    monkeypatch.setattr(image_ocr, "get_available_ocr_languages", lambda: {"amh", "osd"})
    lang_param, active_list = image_ocr.determine_ocr_language_config()
    assert lang_param == "amh"
    assert active_list == ["amh"]

    # Case 3: Only English available
    monkeypatch.setattr(image_ocr, "get_available_ocr_languages", lambda: {"eng", "osd"})
    lang_param, active_list = image_ocr.determine_ocr_language_config()
    assert lang_param == "eng"
    assert active_list == ["eng"]

    # Case 4: Neither available (e.g. clean fallback)
    monkeypatch.setattr(image_ocr, "get_available_ocr_languages", lambda: set())
    lang_param, active_list = image_ocr.determine_ocr_language_config()
    assert lang_param == "eng"
    assert active_list == ["eng"]


def test_ocr_bilingual_fallback_to_english_on_tesseract_error(monkeypatch):
    import pytesseract
    from backend.app import image_ocr

    # Simulate both languages configured
    monkeypatch.setattr(image_ocr, "determine_ocr_language_config", lambda: ("amh+eng", ["amh", "eng"]))

    calls = []

    def mock_image_to_string(image, lang=None, config=None, timeout=None):
        calls.append(lang)
        if lang == "amh+eng":
            # Simulate missing or corrupted traineddata error from Tesseract
            raise pytesseract.TesseractError(1, "Error opening data file /usr/share/tesseract-ocr/tessdata/amh.traineddata")
        return "English fallback text"

    monkeypatch.setattr(pytesseract, "image_to_string", mock_image_to_string)

    result = image_ocr.extract_text_from_image(_png_bytes(), "image/png")
    assert result == "English fallback text"
    # First tried amh+eng, then fell back safely to eng
    assert calls == ["amh+eng", "eng"]


def test_ocr_empty_text_error_message(monkeypatch):
    import pytesseract
    from backend.app import image_ocr

    monkeypatch.setattr(pytesseract, "image_to_string", lambda *args, **kwargs: "   \n\t  ")

    with pytest.raises(image_ocr.OCRProcessingError) as exc_info:
        image_ocr.extract_text_from_image(_png_bytes(), "image/png")

    assert str(exc_info.value) == "No readable text was found in the image."


def test_image_endpoint_returns_configured_ocr_languages(monkeypatch):
    from backend.app import main

    monkeypatch.setattr(
        main,
        "determine_ocr_language_config",
        lambda: ("amh+eng", ["amh", "eng"]),
    )
    monkeypatch.setattr(
        main,
        "extract_text_from_image",
        lambda *args: "ይህ የማረጋገጫ መልእክት ነው",
    )

    response = client.post(
        "/analyze/image",
        files={"file": ("msg.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["extracted_text"] == "ይህ የማረጋገጫ መልእክት ነው"
    assert payload["ocr_engine"] == "Tesseract"
    assert payload["ocr_languages"] == ["amh", "eng"]
