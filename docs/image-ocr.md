# Screenshot Analysis and OCR

The Flutter client accepts PNG and JPEG images up to 5 MB, in the browser and
on Android, using the same FastAPI backend as text analysis. Image bytes are
validated and OCR'd in memory by the server; they are not written to disk or
sent to an external service. The resulting text is shown in the editable
message field and goes through the existing `/analyze` pipeline after the user
reviews it.

## Bilingual OCR: Amharic and English (`amh+eng`)

OCR is powered by Tesseract with bilingual language support for both **Amharic (`amh`)**
and **English (`eng`)**:

- In the production container (`Dockerfile`), both `tesseract-ocr-eng` and `tesseract-ocr-amh`
  are installed via apt.
- The OCR pipeline dynamically detects available language packs via `pytesseract.get_languages()`.
  When both language models are available, it runs with `lang="amh+eng"`.
- If `amh` trained data is missing or corrupted at runtime, the engine catches `TesseractError`
  and safely falls back to `lang="eng"`.
- If no readable text is detected in the image, a clean 422 error is returned:
  `"No readable text was found in the image."`

## Local Development vs Production Docker

### Production & Containerized Deployments
In Docker or Linux hosts:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-amh \
    && rm -rf /var/lib/apt/lists/*
```

### Local Windows Development
On Windows development machines without Tesseract binaries or Amharic trained data:
- Unit tests in `backend/tests/test_image_analysis.py` use isolated monkeypatching and mocks to verify language configuration, dynamic fallback, and error handling without requiring a local Tesseract installation.
- If Tesseract is installed locally at `C:\Program Files\Tesseract-OCR\tesseract.exe`, pytesseract automatically configures its path. To test Amharic locally, download `amh.traineddata` from the Tesseract tessdata repository into your local `tessdata/` directory.

## Running Backend and Frontend

Run the backend from the repository root with:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload
```

Run the Flutter client from `mobile/` with:

```powershell
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

For an Android device, set `API_BASE_URL` to a backend address reachable by the
device. Uploaded images and extracted message text are processed in memory;
the app does not retain uploaded screenshots.
