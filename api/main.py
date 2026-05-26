"""
api/main.py

FastAPI backend for SnapClass.
Runs independently of Streamlit — same service/db/pipeline layer underneath.

Start locally:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    GET  /                              health check
    GET  /api/subjects/{subject_id}/students
    POST /api/attendance/face
    POST /api/attendance/voice
    POST /api/attendance/save
    GET  /api/teachers/{teacher_id}/attendance
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.attendance_service import (
    AttendanceReport,
    run_face_attendance,
    run_voice_attendance,
    save_attendance,
    get_attendance_summary,
)
from src.database.db import get_enrolled_students

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# App lifecycle
# ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load dlib models on startup so first request isn't slow."""
    logger.info("Loading dlib models on startup...")
    from src.pipelines.face_pipeline import _load_dlib_models
    _load_dlib_models()
    logger.info("Startup complete.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="SnapClass API",
    description="AI-powered attendance system — face & voice recognition",
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────
# CORS — allow Streamlit frontend and any local dev origin
# In production, replace "*" with your actual domain
# ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────────────────────

class StudentResultSchema(BaseModel):
    student_id:  int
    name:        str
    roll_number: str
    is_present:  bool
    sources:     list[str]
    status:      str


class AttendanceReportSchema(BaseModel):
    subject_id:    int
    timestamp:     str
    present_count: int
    absent_count:  int
    results:       list[StudentResultSchema]


class SaveRequest(BaseModel):
    subject_id: int
    timestamp:  str
    results: list[dict]   # [{student_id, is_present}]


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "service": "SnapClass API"}


@app.get(
    "/api/subjects/{subject_id}/students",
    tags=["Subjects"],
    summary="List enrolled students for a subject",
)
def get_subject_students(subject_id: int):
    students = get_enrolled_students(subject_id)
    if students is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"subject_id": subject_id, "students": students}


@app.post(
    "/api/attendance/face",
    response_model=AttendanceReportSchema,
    tags=["Attendance"],
    summary="Run face recognition attendance on uploaded photos",
    openapi_extra={
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["subject_id", "images"],
                        "properties": {
                            "subject_id": {"type": "integer", "description": "Subject to take attendance for"},
                            "threshold":  {"type": "number",  "default": 0.6, "description": "Face verification distance threshold"},
                            "images":     {"type": "array", "items": {"type": "string", "format": "binary"}, "description": "One or more classroom photos"},
                        },
                    }
                }
            }
        }
    },
)
async def face_attendance(
    subject_id: int = Form(..., description="Subject to take attendance for"),
    threshold:  float = Form(0.6, description="Face verification distance threshold"),
    images: list[UploadFile] = File(..., description="One or more classroom photos"),
):
    """
    Upload classroom photos and get an attendance report.
    Runs dlib face detection + SVC classification scoped to enrolled students.
    """
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required")

    image_bytes = []
    for upload in images:
        content = await upload.read()
        image_bytes.append(content)

    try:
        report = run_face_attendance(
            images=image_bytes,
            subject_id=subject_id,
            threshold=threshold,
        )
    except Exception as exc:
        logger.error("Face attendance failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Face recognition failed") from exc

    return report.to_dict()


@app.post(
    "/api/attendance/voice",
    response_model=AttendanceReportSchema,
    tags=["Attendance"],
    summary="Run voice recognition attendance on recorded audio",
)
async def voice_attendance(
    subject_id: int = Form(..., description="Subject to take attendance for"),
    threshold:  float = Form(0.65, description="Voice cosine similarity threshold"),
    audio: UploadFile = File(..., description="Classroom audio recording"),
):
    """
    Upload classroom audio and get an attendance report.
    Segments audio by silence, embeds each segment with Resemblyzer,
    matches against enrolled student voice profiles.
    """
    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Audio file is empty")

    try:
        report = run_voice_attendance(
            audio_bytes=audio_bytes,
            subject_id=subject_id,
            threshold=threshold,
        )
    except Exception as exc:
        logger.error("Voice attendance failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Voice recognition failed") from exc

    return report.to_dict()


@app.post(
    "/api/attendance/save",
    tags=["Attendance"],
    summary="Persist an attendance report to the database",
)
def save_attendance_route(payload: SaveRequest):
    """
    Save a previously generated attendance report.
    Call this after the teacher reviews and confirms the results.
    """
    from src.services.attendance_service import AttendanceReport, StudentResult

    results = [
        StudentResult(
            student_id=r["student_id"],
            name=r.get("name", ""),
            roll_number=r.get("roll_number", ""),
            is_present=r["is_present"],
            sources=r.get("sources", []),
        )
        for r in payload.results
    ]

    report = AttendanceReport(
        subject_id=payload.subject_id,
        timestamp=payload.timestamp,
        results=results,
    )

    success = save_attendance(report)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save attendance")

    return {
        "saved":   True,
        "records": len(results),
        "subject_id": payload.subject_id,
    }


@app.get(
    "/api/teachers/{teacher_id}/attendance",
    tags=["Teachers"],
    summary="Get all attendance records for a teacher's subjects",
)
def teacher_attendance(teacher_id: int):
    records = get_attendance_summary(teacher_id)
    return {"teacher_id": teacher_id, "records": records}