"""
src/database/db.py

All database operations via Supabase.

Changes from original:
  - Added get_enrolled_students(subject_id) used by face_pipeline
    for subject-scoped SVC training (fixes cross-subject detection bug)
  - Everything else is identical to the original
"""

from src.database.config import supabase
# pyrefly: ignore [missing-import]
import bcrypt


# =========================
# TEACHERS
# =========================

def hash_pass(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_pass(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def check_teacher_exists(username: str) -> bool:
    res = supabase.table("teachers").select("teacher_id").eq("username", username).execute()
    return len(res.data) > 0


def create_teacher(username: str, password: str, name: str):
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name,
    }
    return supabase.table("teachers").insert(data).execute().data


def teacher_login(username: str, password: str):
    res = supabase.table("teachers").select("*").eq("username", username).execute()
    if res.data:
        teacher = res.data[0]
        if check_pass(password, teacher["password"]):
            return teacher
    return None


# =========================
# STUDENTS
# =========================

def get_all_students() -> list[dict]:
    return supabase.table("students").select("*").execute().data


def get_enrolled_students(subject_id: int) -> list[dict]:
    """
    Return only students enrolled in a specific subject.
    Used by face_pipeline to train a subject-scoped SVC so that
    a student not in Subject A cannot be falsely detected there.
    """
    res = (
        supabase.table("subject_students")
        .select("*, students(*)")
        .eq("subject_id", subject_id)
        .execute()
    )
    # Unwrap the nested students object into a flat list
    return [row["students"] for row in res.data if row.get("students")]


def _json_safe_embedding(embedding):
    if embedding is None:
        return None
    if hasattr(embedding, "tolist"):
        return embedding.tolist()
    return embedding


def create_student(name: str, roll_number: str, face_embedding=None, voice_embedding=None):
    data = {
        "name": name,
        "roll_number": roll_number,
        "face_embedding": _json_safe_embedding(face_embedding),
        "voice_embedding": _json_safe_embedding(voice_embedding),
    }
    return supabase.table("students").insert(data).execute().data


# =========================
# SUBJECTS
# =========================

def create_subject(subject_code: str, name: str, section: str, teacher_id: str):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id,
    }
    response = supabase.table("subjects").insert(data).execute()
    if not response.data:
        raise RuntimeError("Supabase returned no inserted subject data")
    return response.data


def delete_subject(subject_id: int):
    # Cascaded delete: attendance → enrollments → subject
    supabase.table("attendance").delete().eq("subject_id", subject_id).execute()
    supabase.table("subject_students").delete().eq("subject_id", subject_id).execute()
    return supabase.table("subjects").delete().eq("subject_id", subject_id).execute().data


def get_teacher_subjects(teacher_id: str) -> list[dict]:
    res = (
        supabase.table("subjects")
        .select("*, subject_students(count), attendance(timestamp)")
        .eq("teacher_id", teacher_id)
        .execute()
    )
    subjects = res.data
    for sub in subjects:
        sub["total_students"] = (
            sub.get("subject_students", [{}])[0].get("count", 0)
            if sub.get("subject_students")
            else 0
        )
        attendance = sub.get("attendance", [])
        sub["total_classes"] = len(set(log["timestamp"] for log in attendance))
        sub.pop("subject_students", None)
        sub.pop("attendance", None)
    return subjects


# =========================
# ENROLLMENT
# =========================

def enroll_student_to_subject(student_id: int, subject_id: int):
    data = {"student_id": student_id, "subject_id": subject_id}
    return supabase.table("subject_students").insert(data).execute().data


def unenroll_student_from_subject(student_id: int, subject_id: int):
    return (
        supabase.table("subject_students")
        .delete()
        .eq("student_id", student_id)
        .eq("subject_id", subject_id)
        .execute()
        .data
    )


def get_student_subjects(student_id: int) -> list[dict]:
    return (
        supabase.table("subject_students")
        .select("*, subjects(*)")
        .eq("student_id", student_id)
        .execute()
        .data
    )


# =========================
# ATTENDANCE
# =========================

def create_attendance(logs: list[dict]):
    return supabase.table("attendance").insert(logs).execute().data


def get_student_attendance(student_id: int) -> list[dict]:
    return (
        supabase.table("attendance")
        .select("*, subjects(*)")
        .eq("student_id", student_id)
        .execute()
        .data
    )


def get_attendance_for_teacher(teacher_id: str) -> list[dict]:
    return (
        supabase.table("attendance")
        .select("*, subjects!inner(*)")
        .eq("subjects.teacher_id", teacher_id)
        .execute()
        .data
    )