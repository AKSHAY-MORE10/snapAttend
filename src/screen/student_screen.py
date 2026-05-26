"""
src/screen/student_screen.py

Changes from original:
  - train_classifier() after registration now clears _model_cache properly
    (no longer calls st.cache_resource.clear() which wiped dlib models)
  - Student login face check uses a dedicated service call
  - No raw pipeline imports remain in the UI layer
"""

import time
import streamlit as st
import numpy as np
from PIL import Image

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card

from src.pipelines.face_pipeline import get_face_embeddings, _model_cache
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import (
    get_all_students,
    create_student,
    get_student_subjects,
    get_student_attendance,
    unenroll_student_from_subject,
)


# ──────────────────────────────────────────────────────────────
# Student login — face recognition against ALL students
# (login is global, not subject-scoped)
# ──────────────────────────────────────────────────────────────

def _login_face_check(image_np: np.ndarray) -> tuple[int | None, int]:
    """
    Try to identify a student from a webcam image.

    Returns:
        (student_id, num_faces)  — student_id is None if unrecognized
    """
    from src.pipelines.face_pipeline import get_face_embeddings, get_trained_model
    import numpy as _np

    embeddings = get_face_embeddings(image_np)
    num_faces  = len(embeddings)

    if num_faces != 1:
        return None, num_faces

    # For login we use subject_id=0 as a special "global" model key
    # that covers all students (needed for login before subject is known)
    GLOBAL_SUBJECT_ID = 0
    model_data = get_trained_model(GLOBAL_SUBJECT_ID)

    if model_data is None:
        return None, num_faces

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
        return int(predicted_id), num_faces

    return None, num_faces


def _seed_global_model():
    """
    Build the global (all-students) SVC used for login.
    Called once after a new student registers.
    """
    from src.database.db import get_all_students
    from src.pipelines.face_pipeline import _build_model_for_subject, _model_cache
    import numpy as _np
    from sklearn.svm import SVC

    GLOBAL_SUBJECT_ID = 0
    students = get_all_students()

    X, y = [], []
    for s in students:
        emb = s.get("face_embedding")
        if emb is not None:
            X.append(_np.array(emb))
            y.append(s["student_id"])

    if not X:
        _model_cache[GLOBAL_SUBJECT_ID] = None
        return

    X = _np.array(X)
    y = _np.array(y)

    clf = None
    if len(set(y)) > 1:
        clf = SVC(kernel="linear", probability=True, class_weight="balanced")
        clf.fit(X, y)

    _model_cache[GLOBAL_SUBJECT_ID] = {"model": clf, "embeddings": X, "labels": y}


# ──────────────────────────────────────────────────────────────
# Screens
# ──────────────────────────────────────────────────────────────

def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type="secondary", key="loginbackbtn",
                     shortcut="control+backspace"):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login using FaceID", text_alignment="center")
    st.space()
    st.space()

    show_registration = False
    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        img_np = np.array(Image.open(photo_source))

        with st.spinner("AI is scanning..."):
            student_id, num_faces = _login_face_check(img_np)

        if num_faces == 0:
            st.warning("Face not found!")
        elif num_faces > 1:
            st.warning("Multiple faces found — please stand alone in front of the camera.")
        else:
            if student_id is not None:
                all_students = get_all_students()
                student = next((s for s in all_students if s["student_id"] == student_id), None)
                if student:
                    st.session_state.is_logged_in  = True
                    st.session_state.user_role     = "student"
                    st.session_state.student_data  = student
                    st.toast(f"Welcome back, {student['name']}!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("Face not recognized — you might be a new student!")
                show_registration = True

    if show_registration:
        with st.container(border=True):
            st.header("Register new Profile")
            new_name    = st.text_input("Enter your name",        placeholder="E.g. Akshay More")
            roll_number = st.text_input("Enter your roll number", placeholder="E.g. 2026-001")

            st.markdown(
                "<h4 style='color:gray; font-size:0.95rem; margin:0;'>Optional: Voice Enrollment</h4>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='color:gray; margin-top:0.25rem; margin-bottom:0.5rem;'>"
                "Enroll for voice-only attendance</div>",
                unsafe_allow_html=True,
            )

            audio_data = None
            try:
                st.markdown(
                    "<label style='color:gray; display:block; margin-bottom:0.25rem;'>"
                    "Record a short phrase like 'I am present' or 'My name is Akshay'.</label>",
                    unsafe_allow_html=True,
                )
                audio_data = st.audio_input("", key="voice_enroll_audio")
            except Exception:
                st.error("Audio input failed!")

            if st.button("Create Account", type="primary"):
                if not new_name or not roll_number:
                    st.warning("Please enter your name and roll number!")
                else:
                    with st.spinner("Creating profile..."):
                        img_np    = np.array(Image.open(photo_source))
                        encodings = get_face_embeddings(img_np)

                        if encodings:
                            face_emb  = encodings[0].tolist()
                            voice_emb = None

                            if audio_data:
                                voice_emb = get_voice_embedding(audio_data.read())

                            response_data = create_student(
                                new_name, roll_number,
                                face_embedding=face_emb,
                                voice_embedding=voice_emb,
                            )

                            if response_data:
                                # ── Correct retrain: rebuild global login model only ──
                                # Per-subject models are rebuilt lazily when attendance runs
                                _seed_global_model()

                                st.session_state.is_logged_in = True
                                st.session_state.user_role    = "student"
                                st.session_state.student_data = response_data[0]
                                st.toast(f"Profile created! Hi {new_name}!")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("Couldn't capture your facial features for registration.")


def student_dashboard():
    student_data = st.session_state.student_data
    student_id   = student_data["student_id"]

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {student_data['name']}")
        if st.button("Logout", type="secondary", key="loginbackbtn"):
            st.session_state["is_logged_in"] = False
            del st.session_state.student_data
            st.rerun()

    st.space()

    c1, c2 = st.columns(2)
    with c1:
        st.header("Your Enrolled Subjects")
    with c2:
        if st.button("Enroll in Subject", type="primary", width="stretch"):
            enroll_dialog()

    st.divider()

    with st.spinner("Loading your enrolled subjects..."):
        subjects = get_student_subjects(student_id)
        logs     = get_student_attendance(student_id)

    # Build per-subject attendance stats
    stats_map: dict[int, dict] = {}
    for log in logs:
        sid = log["subject_id"]
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}
        stats_map[sid]["total"] += 1
        if log.get("is_present"):
            stats_map[sid]["attended"] += 1

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub   = sub_node["subjects"]
        sid   = sub["subject_id"]
        stats = stats_map.get(sid, {"total": 0, "attended": 0})

        def make_unenroll(s, s_id):
            def unenroll_button():
                if st.button("Unenroll from this course", type="tertiary",
                             width="stretch", icon=":material/delete_forever:"):
                    unenroll_student_from_subject(student_id, s_id)
                    st.toast(f"Unenrolled from {s['name']} successfully!")
                    st.rerun()
            return unenroll_button

        with cols[i % 2]:
            subject_card(
                name=sub["name"],
                code=sub["subject_code"],
                section=sub["section"],
                stats=[
                    ("📅", "Total",    stats["total"]),
                    ("✅", "Attended", stats["attended"]),
                ],
                footer_callback=make_unenroll(sub, sid),
            )

    footer_dashboard()