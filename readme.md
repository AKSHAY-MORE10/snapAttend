# SnapClass — AI Attendance (Face & Voice)

SnapClass is a production-grade AI attendance system using face recognition and voice recognition. It provides separate Teacher and Student portals, a REST API backend, and is fully containerised with Docker.

---

## What's Inside

| Layer | Technology | Purpose |
|-------|-----------|---------|
| UI | Streamlit | Teacher & Student web portal |
| API | FastAPI + Uvicorn | REST API exposing AI pipelines |
| Face AI | dlib + scikit-learn SVC | Face detection, embedding, classification |
| Voice AI | Resemblyzer + librosa | Speaker embedding + cosine similarity matching |
| Database | Supabase (Postgres) | Students, subjects, attendance records |
| Auth | bcrypt | Teacher password hashing |
| Containers | Docker + Docker Compose | Reproducible, portable deployment |
| CI/CD | GitHub Actions | Auto-deploy to server on push to `main` |

---

## Architecture

```
┌─────────────────────┐        ┌──────────────────────────┐
│   Streamlit UI      │        │   FastAPI REST API        │
│   (port 8501)       │        │   (port 8000)             │
│                     │        │   /api/attendance/face    │
│  teacher_screen.py  │        │   /api/attendance/voice   │
│  student_screen.py  │        │   /api/attendance/save    │
└────────┬────────────┘        └────────────┬─────────────┘
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                           │
│            src/services/attendance_service.py           │
│   run_face_attendance()  run_voice_attendance()         │
│   save_attendance()      get_attendance_summary()       │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
      ┌────────▼──────┐     ┌─────────▼────────┐
      │  AI Pipelines  │     │    Database       │
      │  face_pipeline │     │    db.py          │
      │  voice_pipeline│     │    Supabase       │
      └────────────────┘     └──────────────────┘
```

**Why this architecture?**

The original project had business logic, database calls, and AI pipeline calls all mixed inside the Streamlit UI functions. This was refactored into three clean layers:

- **UI layer** — only handles display and user input. Zero database or pipeline imports.
- **Service layer** — all business logic lives here. Both Streamlit and FastAPI call this layer.
- **Data layer** — pipelines and database functions. No UI coupling whatsoever.

This means the FastAPI backend and Streamlit frontend share the exact same AI logic with no duplication.

---

## Key Improvements Over Original

### 1. Decoupled Configuration (`src/database/config.py`)
The original crashed if Streamlit wasn't running because it read credentials exclusively from `st.secrets`. The new version reads from environment variables first, falling back to Streamlit secrets — making the same codebase work in both Streamlit and Docker/FastAPI contexts.

### 2. Fixed Model Caching (`src/pipelines/face_pipeline.py`)
The original used a single `@st.cache_resource` for both dlib models and the SVC classifier. When a new student registered, `cache.clear()` wiped the heavy dlib models too, causing a full reload on every new registration.

Now:
- **dlib models** — cached permanently, never reloaded
- **SVC per subject** — stored in a plain dict, per-subject invalidation only
- **Subject-scoped training** — SVC trained only on students enrolled in the specific subject, fixing a bug where a student in Subject A could be detected present in Subject B

### 3. Service Layer (`src/services/attendance_service.py`)
Extracted all attendance logic from `teacher_screen.py` into a dedicated service. The service returns typed dataclasses (`AttendanceReport`, `StudentResult`) that both Streamlit and FastAPI consume.

### 4. FastAPI REST API (`api/main.py`)
A fully independent REST API alongside Streamlit. Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/subjects/{id}/students` | List enrolled students |
| POST | `/api/attendance/face` | Run face recognition on photos |
| POST | `/api/attendance/voice` | Run voice recognition on audio |
| POST | `/api/attendance/save` | Save attendance report |
| GET | `/api/teachers/{id}/attendance` | Get attendance records |

Interactive docs available at `http://localhost:8000/docs`

### 5. Pinned Dependencies (`requirements.txt`)
All package versions are now pinned for reproducible installs across environments.

### 6. Docker + Docker Compose
Both services containerised. A single `docker compose up --build` starts everything.

### 7. CI/CD Pipeline (`.github/workflows/deploy.yml`)
GitHub Actions workflow auto-deploys on every push to `main`.

---

## Quick Start — Local Development

### Prerequisites
- Python 3.11
- Git

### 1. Clone the repository

```bash
git clone https://github.com/AKSHAY-MORE10/snapAttend.git
cd snapAttend
```

### 2. Create virtual environment

```powershell
# Windows
python -m venv myenv
.\myenv\Scripts\activate

# macOS / Linux
python -m venv myenv
source myenv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install fastapi uvicorn[standard] python-multipart
```

### 4. Configure credentials

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_ANON_OR_SERVICE_ROLE_KEY"
```

Or set environment variables:

```bash
# Windows PowerShell
$env:SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
$env:SUPABASE_KEY="your-key"

# macOS / Linux
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_KEY="your-key"
```

### 5. Run Streamlit UI

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

### 6. Run FastAPI backend (separate terminal)

```bash
python -m uvicorn api.main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI schema: `http://localhost:8000/openapi.json`

---

## Docker Deployment

### Prerequisites
- Docker Desktop installed
- `.env` file in project root (copy from `.env.example`)

```bash
cp .env.example .env
# Edit .env and fill in SUPABASE_URL and SUPABASE_KEY
```

### Run everything

```bash
docker compose up --build
```

This starts:
- FastAPI at `http://localhost:8000`
- Streamlit at `http://localhost:8501`

### Stop

```bash
docker compose down
```

---

## Project Structure

```
.
├── app.py                          # Streamlit entry point
├── requirements.txt                # Pinned dependencies
├── Dockerfile                      # FastAPI container
├── Dockerfile.streamlit            # Streamlit container
├── docker-compose.yml              # Runs both services
├── .env.example                    # Environment variable template
│
├── api/
│   ├── __init__.py
│   └── main.py                     # FastAPI app and all routes
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD auto-deploy pipeline
│
└── src/
    ├── services/
    │   └── attendance_service.py   # Business logic layer (NEW)
    ├── pipelines/
    │   ├── face_pipeline.py        # dlib + SVC face recognition
    │   └── voice_pipeline.py       # Resemblyzer voice recognition
    ├── database/
    │   ├── config.py               # Environment-aware Supabase client
    │   └── db.py                   # All database operations
    ├── screen/
    │   ├── teacher_screen.py       # Teacher portal UI
    │   └── student_screen.py       # Student portal UI
    ├── components/                 # Reusable UI components
    └── ui/                         # Base layout helpers
```

---

## Database Schema (Supabase)

```sql
teachers        — teacher_id (PK), username, password, name
students        — student_id (PK), name, roll_number, face_embedding, voice_embedding
subjects        — subject_id (PK), subject_code, name, section, teacher_id (FK)
subject_students — id (PK), subject_id (FK), student_id (FK)
attendance      — id (PK), subject_id (FK), student_id (FK), timestamp, is_present
```

Enable RLS policies in Supabase for production. Use anon key for local development.

---

## AI Pipeline Details

### Face Pipeline

1. Detect faces using dlib's frontal face detector
2. Extract 68-point facial landmarks per face
3. Compute 128-dimensional face descriptor per face
4. Classify using scikit-learn SVC (linear kernel) — trained only on students enrolled in the specific subject
5. Verify prediction via Euclidean distance against stored embeddings (threshold: 0.6)

Default threshold: **0.6** — lower = stricter matching

### Voice Pipeline

1. Load audio with librosa
2. Split by silence into segments
3. Embed each segment using Resemblyzer's VoiceEncoder (L2-normalized)
4. Compare against enrolled student voice profiles using cosine similarity
5. Mark present if similarity exceeds threshold

Default threshold: **0.65** — higher = stricter matching

---

## API Usage Examples

### Check health

```bash
curl http://localhost:8000/
```

### Run face attendance

```bash
curl -X POST http://localhost:8000/api/attendance/face \
  -F "subject_id=1" \
  -F "threshold=0.6" \
  -F "images=@classroom_photo.jpg"
```

### Run voice attendance

```bash
curl -X POST http://localhost:8000/api/attendance/voice \
  -F "subject_id=1" \
  -F "audio=@classroom_recording.wav"
```

---

## Configuration Reference

| Variable | Source | Description |
|----------|--------|-------------|
| `SUPABASE_URL` | env var or secrets.toml | Your Supabase project URL |
| `SUPABASE_KEY` | env var or secrets.toml | Supabase anon or service role key |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pkg_resources'`**
```bash
pip install --force-reinstall "setuptools<70.0.0"
```

**`ModuleNotFoundError: No module named 'src.services'`**
Make sure `src/services/__init__.py` exists (empty file).

**Face not detected**
- Use well-lit, frontal photos
- Ensure face is large enough in the frame
- dlib works best with faces occupying at least 80x80 pixels

**Voice attendance not matching**
- Record enrollment in a quiet environment
- Use the same microphone for enrollment and attendance
- Speak clearly for at least 3-5 seconds during enrollment

**Supabase connection fails**
- Verify `SUPABASE_URL` and `SUPABASE_KEY` are set correctly
- Check that all required tables exist in your Supabase project

---

## License

MIT License — see `LICENSE` file.
