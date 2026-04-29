from src.database.config import supabase
import bcrypt

# =========================
# TEACHERS
# =========================
def hash_pass(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_pass(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))



def check_teacher_exists(username):
    res = supabase.table("teachers").select("teacher_id").eq("username", username).execute()
    return len(res.data) > 0


def create_teacher(username, password, name):
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name
    }
    return supabase.table("teachers").insert(data).execute().data


def teacher_login(username, password):
    res = supabase.table("teachers").select("*").eq("username", username).execute()
    if res.data:
        teacher = res.data[0]
        if check_pass(password, teacher["password"]):
            return teacher
    return None


# =========================
# STUDENTS
# =========================
def get_all_students():
    return supabase.table("students").select("*").execute().data


def create_student(name, roll_number, face_embedding=None, voice_embedding=None):
    data = {
        "name": name,
        "roll_number": roll_number,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding
    }
    return supabase.table("students").insert(data).execute().data


# =========================
# SUBJECTS
# =========================
def create_subject(subject_code, name, section, teacher_id):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }
    return supabase.table("subjects").insert(data).execute().data


def get_teacher_subjects(teacher_id):
    res = supabase.table("subjects") \
        .select("*, subject_students(count), attendance(timestamp)") \
        .eq("teacher_id", teacher_id) \
        .execute()

    subjects = res.data

    for sub in subjects:
        # total students
        sub["total_students"] = (
            sub.get("subject_students", [{}])[0].get("count", 0)
            if sub.get("subject_students") else 0
        )

        # total classes
        attendance = sub.get("attendance", [])
        unique_sessions = len(set(log["timestamp"] for log in attendance))
        sub["total_classes"] = unique_sessions

        sub.pop("subject_students", None)
        sub.pop("attendance", None)

    return subjects


# =========================
# ENROLLMENT
# =========================
def enroll_student_to_subject(student_id, subject_id):
    data = {"student_id": student_id, "subject_id": subject_id}
    return supabase.table("subject_students").insert(data).execute().data


def unenroll_student_from_subject(student_id, subject_id):
    return supabase.table("subject_students") \
        .delete() \
        .eq("student_id", student_id) \
        .eq("subject_id", subject_id) \
        .execute().data


def get_student_subjects(student_id):
    return supabase.table("subject_students") \
        .select("*, subjects(*)") \
        .eq("student_id", student_id) \
        .execute().data


# =========================
# ATTENDANCE
# =========================
def create_attendance(logs):
    return supabase.table("attendance").insert(logs).execute().data


def get_student_attendance(student_id):
    return supabase.table("attendance") \
        .select("*, subjects(*)") \
        .eq("student_id", student_id) \
        .execute().data


def get_attendance_for_teacher(teacher_id):
    return supabase.table("attendance") \
        .select("*, subjects!inner(*)") \
        .eq("subjects.teacher_id", teacher_id) \
        .execute().data