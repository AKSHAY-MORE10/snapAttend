Replace existing README with a detailed, polished README describing usage, configuration, pipelines, and development notes.

*** Begin File
# SnapClass — AI attendance (face & voice)

SnapClass is a Streamlit web application that speeds up classroom attendance using face recognition and optional speaker (voice) recognition. The app provides separate Teacher and Student portals. Teachers create subjects, share join links or QR codes, and take attendance using photos and/or classroom audio. Students enroll using face (and optionally voice) profiles and can join subjects via a code or shared link.

Table of contents
- Features
- Technology stack
- Quick start (run locally)
- Configuration
- Database schema (Supabase)
- AI pipeline details
- Project layout
- Troubleshooting & tips
- Contributing
- License

---

## Features

- Dual portals: Student and Teacher flows from the home screen.
- Teacher authentication (username/password, bcrypt hashed).
- Student authentication via Face ID (webcam) and optional voice enrollment.
- Student registration captures face embedding and optional voice embedding.
- Subjects: create, share (link + QR), manage enrolled students.
- Enrollment: manual subject code or one-click via `?join-code=<SUBJECT_CODE>` deep link.
- Face attendance: upload or capture photos → run face analysis (dlib + SVC) → review & save.
- Voice attendance: record classroom audio → segment + embed (Resemblyzer) → match enrolled voice profiles.
- Attendance records with export / per-session stats.

---

## Technology stack

- UI: Streamlit (`app.py`, `src/screen`, `src/components`, `src/ui`)
- Database: Supabase (Postgres) via the Supabase Python client (`src/database/*.py`)
- Face recognition: dlib (detector + shape predictor + 128-D face descriptors) and `face_recognition_models` for model weights
- Classifier: scikit-learn `SVC` (linear kernel) for multi-class student recognition
- Voice recognition: `librosa` + `resemblyzer` to produce speaker embeddings
- Utilities: NumPy, pandas, Pillow, segno (QR generation)

Default thresholds used in code:
- Face verification distance threshold: 0.6
- Voice similarity threshold: 0.65

---

## Quick start (run locally)

1. Clone the repository and open the project root.

2. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
# On macOS / Linux:
# python -m venv .venv
# source .venv/bin/activate
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

Notes:
- `dlib-bin` is included to avoid building dlib from source on many platforms.
- `face_recognition_models` is installed from Git for required model weights.

4. Configure Supabase secrets (see Configuration below).

5. Run the Streamlit app:

```powershell
streamlit run app.py
```

Open the URL Streamlit provides (usually http://localhost:8501).

If you want to deploy the landing frontend, see `fontend/ai-attendance-project-landing` — it contains a small static landing app and its own requirements.

---

## Configuration

The app reads Supabase configuration from Streamlit secrets (recommended). Create `.streamlit/secrets.toml` in the project root:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_ANON_OR_SERVICE_ROLE_KEY"
```

Place the appropriate key depending on your security needs. Do NOT commit secrets to source control.

The database client is initialized in `src/database/config.py`.

---

## Database (Supabase) — expected schema

The app expects tables with roughly the following columns. Adjust column names or queries if your schema differs.

- `teachers` — `id (PK)`, `username`, `password_hash`, `name`
- `students` — `id (PK)`, `name`, `roll_number`, `face_embedding` (array/JSON), `voice_embedding` (array/JSON)
- `subjects` — `id (PK)`, `subject_code`, `name`, `section`, `teacher_id (FK)`
- `subject_students` — `id (PK)`, `subject_id (FK)`, `student_id (FK)`
- `attendance` — `id (PK)`, `subject_id (FK)`, `student_id (FK)`, `timestamp`, `is_present`, `source` (e.g., "photo", "audio")

Implement appropriate RLS policies in Supabase for production; tests and local development can use an anon key.

---

## AI pipeline details

### Face pipeline (`src/pipelines/face_pipeline.py`)

1. Face detection using dlib's frontal face detector.
2. Face landmarking (68 points) and extraction of a 128-dimensional descriptor per face.
3. When multiple students have face embeddings, the app trains an `SVC` (linear kernel) to classify among known students; when only one student exists, the pipeline uses direct matching.
4. After classification, the predicted student is verified by computing Euclidean distance between the detected face embedding and stored embeddings for that student. Default verification threshold: **0.6**.

Notes:
- Good photo quality and frontal faces improve detection and embeddings.

### Voice pipeline (`src/pipelines/voice_pipeline.py`)

1. Enrollment: teacher/student records a short sample; audio is loaded with `librosa` and passed through `resemblyzer`'s `VoiceEncoder` to produce an embedding (L2-normalized) stored on the student record.
2. Attendance: classroom audio is segmented (silence-based splitting). Each segment is embedded and compared against enrolled student voice embeddings using cosine similarity (dot product of normalized vectors). Default match threshold: **0.65**.

Notes:
- Voice attendance works best in low-noise environments and when students speak a consistent phrase during enrollment.

---

## Project layout

```
.
├── app.py                        # Streamlit app entry point
├── requirements.txt
├── fontend/                      # Landing static frontend (optional)
└── src/
    ├── components/              # Dialogs and reusable UI components
    ├── database/                # Supabase config + db helpers
    ├── pipelines/               # face_pipeline.py, voice_pipeline.py
    ├── screen/                  # Student, Teacher, Home screens
    └── ui/                      # Base layout & helpers
```

---

## Troubleshooting & tips

- If Supabase authentication fails, verify `SUPABASE_URL` and `SUPABASE_KEY` in `.streamlit/secrets.toml` and ensure required tables/columns exist.
- For face recognition:
  - Use well-lit, frontal photos.
  - Ensure faces are large enough in uploaded classroom photos for dlib to detect.
- For voice recognition:
  - Use a clear enrollment sample per student.
  - Lower the noise in the classroom or use directional microphones for better results.
- If model downloads or package installs fail, check `pip` output for missing binary wheels and consider matching Python version with available wheels.

---

## Contributing

Contributions are welcome. Suggested next steps for contributions:

1. Create an issue describing the bug or feature request.
2. Make changes on a topic branch and open a pull request.
3. Include a short description of changes and any migration steps (DB schema updates).

---

## License

Add a license to this repository if you plan to open-source it (e.g., MIT, Apache-2.0). Currently no license is specified.

---

If you want additional content added (full Supabase SQL, example `.sql` migrations, or a deployment guide for Streamlit Cloud / Vercel), tell me which you'd like and I will add it.

*** End File