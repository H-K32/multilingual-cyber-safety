# Screenshot analysis and OCR

The Flutter client accepts PNG and JPEG images up to 5 MB, in the browser and
on Android, using the same FastAPI backend as text analysis. Image bytes are
validated and OCR'd in memory by the server; they are not written to disk or
sent to an external service. The resulting text is shown in the editable
message field and goes through the existing `/analyze` pipeline after the user
reviews it.

OCR uses the local Tesseract executable with the `eng` language data only. It
supports English text when Tesseract and its English trained data are installed
on the backend host. Amharic OCR is **not supported or verified**: the Amharic
trained data is not bundled, and it must not be assumed to exist on a host.
Install Tesseract for the backend operating system and ensure `eng` is available
on `TESSDATA_PREFIX` before enabling screenshot OCR. If the runtime is missing,
the endpoint returns a clear service-unavailable response; pasted-text analysis
continues to work.

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
