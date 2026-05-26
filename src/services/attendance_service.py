"""
src/services/attendance_service.py

Business logic layer for attendance operations.

This sits between the UI (Streamlit) / API (FastAPI) and the pipelines/database.
Neither teacher_screen.py nor any future API route should ever call supabase
directly or import from pipelines — they go through this service instead.

Rules:
  - No Streamlit imports here (zero UI coupling)
  - No raw supabase calls (use db.py functions only)
  - Returns plain dicts/dataclasses — caller decides how to present them
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from PIL import Image
import io

from src.database.db import (
    create_attendance,
    get_enrolled_students,
    get_attendance_for_teacher,
)
from src.pipelines.face_pipeline import predict_attendance, train_classifier
from src.pipelines.voice_pipeline import process_bulk_audio

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Data shapes returned by this service
# Plain dataclasses — no Streamlit, no FastAPI deps
# ──────────────────────────────────────────────────────────────

@dataclass
class StudentResult:
    student_id: int
    name: str
    roll_number: str
    is_present: bool
    sources: list[str] = field(default_factory=list)   # e.g. ["Photo 1", "Photo 3"]

    @property
    def status_label(self) -> str:
        return "Present" if self.is_present else "Absent"

    def to_dict(self) -> dict:
        return {
            "student_id":  self.student_id,
            "name":        self.name,
            "roll_number": self.roll_number,
            "is_present":  self.is_present,
            "sources":     self.sources,
            "status":      self.status_label,
        }


@dataclass
class AttendanceReport:
    subject_id:  int
    timestamp:   str                         # ISO-8601 string
    results:     list[StudentResult]

    @property
    def present_count(self) -> int:
        return sum(1 for r in self.results if r.is_present)

    @property
    def absent_count(self) -> int:
        return len(self.results) - self.present_count

    def to_dict(self) -> dict:
        return {
            "subject_id":    self.subject_id,
            "timestamp":     self.timestamp,
            "present_count": self.present_count,
            "absent_count":  self.absent_count,
            "results":       [r.to_dict() for r in self.results],
        }


# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────

def _load_image_as_np(image_source) -> np.ndarray:
    """
    Accept multiple image formats and return an RGB numpy array.

    Handles:
      - PIL.Image
      - raw bytes / BytesIO
      - Streamlit UploadedFile (has .read() / .getvalue())
      - numpy array (passthrough)
    """
    if isinstance(image_source, np.ndarray):
        return image_source

    if isinstance(image_source, Image.Image):
        return np.array(image_source.convert("RGB"))

    # File-like or bytes
    try:
        raw = (
            image_source.getvalue()
            if hasattr(image_source, "getvalue")
            else image_source.read()
            if hasattr(image_source, "read")
            else image_source
        )
        return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
    except Exception as exc:
        raise ValueError(f"Cannot convert image source to numpy array: {exc}") from exc


def _build_voice_candidates(enrolled: list[dict]) -> dict[int, list]:
    """Return {student_id: voice_embedding} for students who have voice enrolled."""
    return {
        s["student_id"]: s["voice_embedding"]
        for s in enrolled
        if s.get("voice_embedding") is not None
    }


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────

def run_face_attendance(
    images: list,
    subject_id: int,
    threshold: float = 0.6,
) -> AttendanceReport:
    """
    Run face recognition across a list of images for a given subject.

    Args:
        images:     List of image sources (PIL, bytes, UploadedFile, numpy)
        subject_id: Subject to take attendance for
        threshold:  Face verification distance threshold (default 0.6)

    Returns:
        AttendanceReport with per-student present/absent results
    """
    enrolled = get_enrolled_students(subject_id)

    if not enrolled:
        logger.warning("run_face_attendance: no enrolled students for subject_id=%s", subject_id)
        return AttendanceReport(
            subject_id=subject_id,
            timestamp=_now(),
            results=[],
        )

    # Map student_id → {sources detected in}
    detected_in: dict[int, list[str]] = {}

    for idx, image_source in enumerate(images):
        label = f"Photo {idx + 1}"
        try:
            img_np = _load_image_as_np(image_source)
        except ValueError as exc:
            logger.error("Skipping %s — could not load image: %s", label, exc)
            continue

        detected, _, _ = predict_attendance(img_np, subject_id=subject_id, threshold=threshold)

        for sid in detected:
            detected_in.setdefault(sid, []).append(label)

    # Build per-student results against full enrolled list
    timestamp = _now()
    results: list[StudentResult] = []

    for student in enrolled:
        sid     = int(student["student_id"])
        sources = detected_in.get(sid, [])

        results.append(StudentResult(
            student_id=sid,
            name=student["name"],
            roll_number=student.get("roll_number", ""),
            is_present=len(sources) > 0,
            sources=sources,
        ))

    logger.info(
        "Face attendance: subject=%s, present=%d/%d",
        subject_id,
        sum(1 for r in results if r.is_present),
        len(results),
    )

    return AttendanceReport(subject_id=subject_id, timestamp=timestamp, results=results)


def run_voice_attendance(
    audio_bytes: bytes,
    subject_id: int,
    threshold: float = 0.65,
) -> AttendanceReport:
    """
    Run voice-based attendance for a subject using bulk classroom audio.

    Args:
        audio_bytes: Raw audio bytes from the recording
        subject_id:  Subject to take attendance for
        threshold:   Cosine similarity threshold (default 0.65)

    Returns:
        AttendanceReport with per-student present/absent results
    """
    enrolled   = get_enrolled_students(subject_id)
    candidates = _build_voice_candidates(enrolled)

    if not candidates:
        logger.warning("run_voice_attendance: no voice profiles for subject_id=%s", subject_id)
        return AttendanceReport(
            subject_id=subject_id,
            timestamp=_now(),
            results=[],
        )

    # {student_id: best_similarity_score}
    identified = process_bulk_audio(audio_bytes, candidates, threshold=threshold)

    timestamp = _now()
    results: list[StudentResult] = []

    for student in enrolled:
        sid      = int(student["student_id"])
        detected = sid in identified

        results.append(StudentResult(
            student_id=sid,
            name=student["name"],
            roll_number=student.get("roll_number", ""),
            is_present=detected,
            sources=["Voice"] if detected else [],
        ))

    logger.info(
        "Voice attendance: subject=%s, identified=%d/%d",
        subject_id,
        sum(1 for r in results if r.is_present),
        len(results),
    )

    return AttendanceReport(subject_id=subject_id, timestamp=timestamp, results=results)


def save_attendance(report: AttendanceReport) -> bool:
    """
    Persist an AttendanceReport to the database.

    Returns True on success, False on failure.
    """
    if not report.results:
        logger.warning("save_attendance: empty report for subject_id=%s", report.subject_id)
        return False

    logs = [
        {
            "student_id": r.student_id,
            "subject_id": report.subject_id,
            "timestamp":  report.timestamp,
            "is_present": r.is_present,
        }
        for r in report.results
    ]

    try:
        create_attendance(logs)
        logger.info(
            "Saved attendance: subject=%s, %d records at %s",
            report.subject_id, len(logs), report.timestamp,
        )
        return True
    except Exception as exc:
        logger.error("save_attendance failed: %s", exc)
        return False


def retrain_for_subject(subject_id: int) -> bool:
    """
    Rebuild the face recognition model for a subject.
    Call this after a student enrolls or updates their face embedding.
    """
    return train_classifier(subject_id)


def get_attendance_summary(teacher_id: int) -> list[dict]:
    """
    Return attendance records for all subjects owned by teacher_id.
    Formatted for display — no raw DB types exposed.
    """
    records = get_attendance_for_teacher(teacher_id)
    summary = []

    for r in records:
        ts = r.get("timestamp")
        summary.append({
            "timestamp":    ts,
            "time_display": _format_ts(ts),
            "subject":      r["subjects"]["name"],
            "subject_code": r["subjects"]["subject_code"],
            "is_present":   bool(r.get("is_present", False)),
        })

    return summary


# ──────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _format_ts(ts: str | None) -> str:
    if not ts:
        return "N/A"
    try:
        return datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p")
    except ValueError:
        return ts