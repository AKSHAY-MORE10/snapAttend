"""
api/main.py

FastAPI backend for SnapClass.
Runs independently of Streamlit — same service/db/pipeline layer underneath.

Start locally:
    uvicorn api.main:app --reload --port 8000

Endpoints:
    GET  /                                         health check

    -- Auth --
    POST /api/auth/teacher/login
    POST /api/auth/teacher/register
    POST /api/auth/student/face-login
    POST /api/auth/student/register

    -- Subjects --
    GET  /api/teachers/{teacher_id}/subjects
    POST /api/subjects
    DELETE /api/subjects/{subject_id}
    GET  /api/subjects/{subject_id}/students

    -- Enrollment --
    POST /api/enroll
    DELETE /api/students/{student_id}/subjects/{subject_id}
    GET  /api/students/{student_id}/subjects
    GET  /api/students/{student_id}/attendance

    -- Attendance --
    POST /api/attendance/face
    POST /api/attendance/voice
    POST /api/attendance/save
    GET  /api/teachers/{teacher_id}/attendance
"""

import io
import logging
from contextlib import asynccontextmanager

import numpy as np
from PIL import Image

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
from src.database.db import (
    get_enrolled_students,
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
    create_subject,
    delete_subject,
    get_all_students,
    create_student,
    enroll_student_to_subject,
    unenroll_student_from_subject,
    get_student_subjects,
    get_student_attendance,
)
from src.database.config import supabase

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
    version="2.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────
# CORS — allow React frontend (localhost:5173) and any local dev origin
# In production, replace "*" with your actual domain
# ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Shared response / request schemas
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
    results: list[dict]   # [{student_id, is_present, name?, roll_number?, sources?}]


class TeacherLoginRequest(BaseModel):
    username: str
    password: str


class TeacherRegisterRequest(BaseModel):
    username: str
    name:     str
    password: str
    confirm:  str


class CreateSubjectRequest(BaseModel):
    teacher_id:   str
    name:         str
    subject_code: str
    section:      str


class EnrollRequest(BaseModel):
    student_id:   int
    subject_code: str  # student provides the code, we look up subject_id


# ──────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "service": "SnapClass API", "version": "2.0.0"}


# ──────────────────────────────────────────────────────────────
# Auth — Teacher
# ──────────────────────────────────────────────────────────────

@app.post("/api/auth/teacher/login", tags=["Auth"])
def api_teacher_login(body: TeacherLoginRequest):
    """Login a teacher with username + password."""
    if not body.username or not body.password:
        raise HTTPException(status_code=422, detail="Username and password are required")

    teacher = teacher_login(body.username, body.password)
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Don't return the hashed password to the client
    teacher.pop("password", None)
    return {"teacher": teacher}


@app.post("/api/auth/teacher/register", tags=["Auth"])
def api_teacher_register(body: TeacherRegisterRequest):
    """Register a new teacher account."""
    if not body.username or not body.name or not body.password:
        raise HTTPException(status_code=422, detail="All fields are required")
    if body.password != body.confirm:
        raise HTTPException(status_code=422, detail="Passwords do not match")
    if check_teacher_exists(body.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    try:
        result = create_teacher(body.username, body.password, body.name)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create teacher")
        teacher = result[0]
        teacher.pop("password", None)
        return {"teacher": teacher}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Teacher register failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during registration") from exc


# ──────────────────────────────────────────────────────────────
# Auth — Student (face login + registration)
# ──────────────────────────────────────────────────────────────

@app.post("/api/auth/student/face-login", tags=["Auth"])
async def api_student_face_login(
    image: UploadFile = File(..., description="Webcam photo of the student"),
):
    """
    Attempt to identify a student from a webcam photo using face recognition.
    Returns the matched student data, or a 'not_found' flag if unrecognized.
    """
    from src.pipelines.face_pipeline import get_face_embeddings, get_trained_model
    import numpy as _np

    img_bytes = await image.read()
    try:
        img_np = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}") from exc

    embeddings = get_face_embeddings(img_np)
    num_faces = len(embeddings)

    if num_faces == 0:
        return {"matched": False, "reason": "no_face", "num_faces": 0}
    if num_faces > 1:
        return {"matched": False, "reason": "multiple_faces", "num_faces": num_faces}

    GLOBAL_SUBJECT_ID = 0
    model_data = get_trained_model(GLOBAL_SUBJECT_ID)

    if model_data is None:
        return {"matched": False, "reason": "no_model", "num_faces": 1}

    clf              = model_data["model"]
    known_embeddings = model_data["embeddings"]
    labels           = model_data["labels"]
    encoding         = embeddings[0]

    predicted_id = labels[0] if clf is None else clf.predict([encoding])[0]

    student_indices = _np.where(labels == predicted_id)[0]
    distances = [
        _np.linalg.norm(known_embeddings[i] - encoding)
        for i in student_indices
    ]

    if min(distances) <= 0.6:
        student_id = int(predicted_id)
        all_students = get_all_students()
        student = next((s for s in all_students if s["student_id"] == student_id), None)
        if student:
            student.pop("face_embedding", None)
            student.pop("voice_embedding", None)
            return {"matched": True, "student": student}

    return {"matched": False, "reason": "unrecognized", "num_faces": 1}


@app.post("/api/auth/student/register", tags=["Auth"])
async def api_student_register(
    name:        str        = Form(..., description="Student's full name"),
    roll_number: str        = Form(..., description="Student's roll number"),
    image:       UploadFile = File(..., description="Webcam photo for face enrollment"),
    audio:       UploadFile = File(None, description="Optional voice sample for voice enrollment"),
):
    """
    Register a new student with face (required) and optional voice enrollment.
    Rebuilds the global face login model after registration.
    """
    from src.pipelines.face_pipeline import get_face_embeddings, _model_cache, _build_model_for_subject
    from src.database.db import get_all_students
    import numpy as _np
    from sklearn.svm import SVC

    if not name or not roll_number:
        raise HTTPException(status_code=422, detail="Name and roll number are required")

    img_bytes = await image.read()
    try:
        img_np = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cannot decode image: {exc}") from exc

    encodings = get_face_embeddings(img_np)
    if not encodings:
        raise HTTPException(status_code=422, detail="No face detected in the image")

    face_emb  = encodings[0].tolist()
    voice_emb = None

    if audio:
        audio_bytes = await audio.read()
        if audio_bytes:
            from src.pipelines.voice_pipeline import get_voice_embedding
            voice_emb = get_voice_embedding(audio_bytes)

    try:
        result = create_student(name, roll_number, face_embedding=face_emb, voice_embedding=voice_emb)
    except Exception as exc:
        logger.error("Student register failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create student account") from exc

    if not result:
        raise HTTPException(status_code=500, detail="No data returned from database")

    # Rebuild global login model so this new student can log in immediately
    GLOBAL_SUBJECT_ID = 0
    students = get_all_students()
    X, y = [], []
    for s in students:
        emb = s.get("face_embedding")
        if emb is not None:
            X.append(_np.array(emb))
            y.append(s["student_id"])

    if X:
        X = _np.array(X)
        y = _np.array(y)
        clf = None
        if len(set(y)) > 1:
            clf = SVC(kernel="linear", probability=True, class_weight="balanced")
            clf.fit(X, y)
        _model_cache[GLOBAL_SUBJECT_ID] = {"model": clf, "embeddings": X, "labels": y}

    student = result[0]
    student.pop("face_embedding", None)
    student.pop("voice_embedding", None)
    return {"student": student}


# ──────────────────────────────────────────────────────────────
# Subjects
# ──────────────────────────────────────────────────────────────

@app.get(
    "/api/teachers/{teacher_id}/subjects",
    tags=["Subjects"],
    summary="Get all subjects for a teacher",
)
def api_get_teacher_subjects(teacher_id: str):
    subjects = get_teacher_subjects(teacher_id)
    return {"teacher_id": teacher_id, "subjects": subjects}


@app.post("/api/subjects", tags=["Subjects"], summary="Create a new subject")
def api_create_subject(body: CreateSubjectRequest):
    if not body.name or not body.subject_code or not body.section:
        raise HTTPException(status_code=422, detail="All fields (name, subject_code, section) are required")
    try:
        result = create_subject(body.subject_code, body.name, body.section, body.teacher_id)
        return {"subject": result[0]}
    except Exception as exc:
        logger.error("Create subject failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/api/subjects/{subject_id}", tags=["Subjects"], summary="Delete a subject and its records")
def api_delete_subject(subject_id: int):
    try:
        delete_subject(subject_id)
        return {"deleted": True, "subject_id": subject_id}
    except Exception as exc:
        logger.error("Delete subject failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete subject") from exc


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


# ──────────────────────────────────────────────────────────────
# Enrollment
# ──────────────────────────────────────────────────────────────

@app.post("/api/enroll", tags=["Enrollment"], summary="Enroll a student in a subject by subject code")
def api_enroll_student(body: EnrollRequest):
    """
    Enroll a student using a subject code string (e.g. 'CS101').
    Looks up the subject, checks for duplicate enrollment, then enrolls.
    Also re-trains the face classifier for the subject.
    """
    res = supabase.table("subjects").select("subject_id, name, subject_code").eq("subject_code", body.subject_code).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Subject code not found")

    subject = res.data[0]
    subject_id = subject["subject_id"]

    # Check if already enrolled
    check = (
        supabase.table("subject_students")
        .select("*")
        .eq("subject_id", subject_id)
        .eq("student_id", body.student_id)
        .execute()
    )
    if check.data:
        raise HTTPException(status_code=409, detail="Already enrolled in this subject")

    try:
        enroll_student_to_subject(body.student_id, subject_id)
        # Retrain classifier for this subject so the new student is recognized
        from src.pipelines.face_pipeline import train_classifier
        train_classifier(subject_id)
    except Exception as exc:
        logger.error("Enrollment failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Enrollment failed") from exc

    return {"enrolled": True, "subject": subject}


@app.delete(
    "/api/students/{student_id}/subjects/{subject_id}",
    tags=["Enrollment"],
    summary="Unenroll a student from a subject",
)
def api_unenroll_student(student_id: int, subject_id: int):
    try:
        unenroll_student_from_subject(student_id, subject_id)
        return {"unenrolled": True, "student_id": student_id, "subject_id": subject_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unenroll failed") from exc


@app.get(
    "/api/students/{student_id}/subjects",
    tags=["Students"],
    summary="Get all subjects a student is enrolled in",
)
def api_get_student_subjects(student_id: int):
    subjects = get_student_subjects(student_id)
    return {"student_id": student_id, "subjects": subjects}


@app.get(
    "/api/students/{student_id}/attendance",
    tags=["Students"],
    summary="Get all attendance records for a student",
)
def api_get_student_attendance(student_id: int):
    records = get_student_attendance(student_id)
    return {"student_id": student_id, "records": records}


# ──────────────────────────────────────────────────────────────
# Attendance
# ──────────────────────────────────────────────────────────────

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
                            "subject_id": {"type": "integer"},
                            "threshold":  {"type": "number", "default": 0.6},
                            "images":     {"type": "array", "items": {"type": "string", "format": "binary"}},
                        },
                    }
                }
            }
        }
    },
)
async def face_attendance(
    subject_id: int = Form(...),
    threshold:  float = Form(0.6),
    images: list[UploadFile] = File(...),
):
    """
    Upload classroom photos and get an attendance report.
    Runs dlib face detection + SVC classification scoped to enrolled students.
    """
    if not images:
        raise HTTPException(status_code=422, detail="At least one image is required")

    image_bytes = [await upload.read() for upload in images]

    try:
        report = run_face_attendance(images=image_bytes, subject_id=subject_id, threshold=threshold)
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
    subject_id: int   = Form(...),
    threshold:  float = Form(0.65),
    audio: UploadFile = File(...),
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
        report = run_voice_attendance(audio_bytes=audio_bytes, subject_id=subject_id, threshold=threshold)
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
        "saved":      True,
        "records":    len(results),
        "subject_id": payload.subject_id,
    }


@app.get(
    "/api/teachers/{teacher_id}/attendance",
    tags=["Teachers"],
    summary="Get all attendance records for a teacher's subjects",
)
def teacher_attendance(teacher_id: str):
    records = get_attendance_summary(teacher_id)
    return {"teacher_id": teacher_id, "records": records}