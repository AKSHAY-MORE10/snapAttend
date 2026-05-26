"""
src/screen/teacher_screen.py

All business logic removed — delegated to src/services/attendance_service.py
This file only handles UI: reading inputs, showing results, triggering actions.
"""

import streamlit as st
import pandas as pd

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog
from src.components.dialog_attendance_results import attendance_result_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    delete_subject,
    teacher_login,
    get_teacher_subjects,
)

# ── Service layer (no more raw supabase or pipeline imports here) ──
from src.services.attendance_service import (
    run_face_attendance,
    save_attendance,
    get_attendance_summary,
)


def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif st.session_state.get("teacher_login_type", "login") == "login":
        teacher_screen_login()
    else:
        teacher_screen_register()


# ──────────────────────────────────────────────────────────────
# Dashboard shell
# ──────────────────────────────────────────────────────────────

def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {teacher_data.get('name', '')}")
        if st.button("Logout", type="secondary", key="loginbackbtn"):
            st.session_state["is_logged_in"] = False
            st.session_state.pop("teacher_data", None)
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)
    with tab1:
        t = "primary" if st.session_state.current_teacher_tab == "take_attendance" else "tertiary"
        if st.button("Take Attendance", type=t, width="stretch", icon=":material/ar_on_you:"):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()
    with tab2:
        t = "primary" if st.session_state.current_teacher_tab == "manage_subjects" else "tertiary"
        if st.button("Manage Subjects", type=t, width="stretch", icon=":material/book_ribbon:"):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()
    with tab3:
        t = "primary" if st.session_state.current_teacher_tab == "attendance_records" else "tertiary"
        if st.button("Attendance Records", type=t, width="stretch", icon=":material/cards_stack:"):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    elif st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    elif st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()


# ──────────────────────────────────────────────────────────────
# Tab: Take Attendance
# ──────────────────────────────────────────────────────────────

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data.get("teacher_id")
    st.header("Take AI Attendance")

    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)
    if not subjects:
        st.warning("You haven't created any subjects yet! Please create one to begin!")
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s["subject_id"] for s in subjects}

    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        selected_label = st.selectbox("Select Subject", options=list(subject_options.keys()))
    with col2:
        if st.button("Add Photos", type="primary", icon=":material/photo_prints:", width="stretch"):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_label]

    st.divider()

    if st.session_state.attendance_images:
        st.header("Added Photos")
        gallery_cols = st.columns(4)
        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, caption=f"Photo {idx + 1}")

    has_photos = bool(st.session_state.attendance_images)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Clear all photos", width="stretch", type="tertiary",
                     icon=":material/delete:", disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()

    with c2:
        if st.button("Run Face Analysis", width="stretch", type="secondary",
                     icon=":material/analytics:", disabled=not has_photos):

            with st.spinner("Deep scanning classroom photos..."):
                # ── All logic now lives in the service ────────────
                report = run_face_attendance(
                    images=st.session_state.attendance_images,
                    subject_id=selected_subject_id,
                )

            if not report.results:
                st.warning("No students enrolled in this subject.")
            else:
                # Build display DataFrame for the results dialog
                display_df = pd.DataFrame([
                    {
                        "Name":   r.name,
                        "ID":     r.student_id,
                        "Source": ", ".join(r.sources) if r.sources else "—",
                        "Status": "✅ Present" if r.is_present else "❌ Absent",
                    }
                    for r in report.results
                ])

                # attendance_result_dialog still receives the raw logs list
                # so it can save — we convert the report for it
                logs = [
                    {
                        "student_id": r.student_id,
                        "subject_id": report.subject_id,
                        "timestamp":  report.timestamp,
                        "is_present": r.is_present,
                    }
                    for r in report.results
                ]
                attendance_result_dialog(display_df, logs)

    with c3:
        if st.button("Use Voice Attendance", type="primary", width="stretch", icon=":material/mic:"):
            voice_attendance_dialog(selected_subject_id)


# ──────────────────────────────────────────────────────────────
# Tab: Manage Subjects  (unchanged logic, kept exactly as original)
# ──────────────────────────────────────────────────────────────

def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data.get("teacher_id")

    col1, col2 = st.columns(2)
    with col1:
        st.header("Manage Subjects")
    with col2:
        st.markdown("<div style='display:flex; align-items:center; height:100%; padding-top:1rem;'>", unsafe_allow_html=True)
        if st.button("＋  Create New Subject", use_container_width=True):
            st.session_state.show_create_subject_form = True
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
        <style>
        .stAlert { background-color:#2c2c2c !important; color:#f0f0f0 !important;
                   border:1px solid #3d3d3d !important; border-radius:0.75rem !important; }
        div[data-testid="stNotification"] { background-color:#2c2c2c !important;
                   color:#c8c8c8 !important; border-left:4px solid #888888 !important;
                   border-radius:0.5rem !important; }
        hr { border-color:#3d3d3d !important; }
        </style>
    """, unsafe_allow_html=True)

    if "show_create_subject_form" not in st.session_state:
        st.session_state.show_create_subject_form = False

    if st.session_state.show_create_subject_form:
        create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id)

    if subjects:
        for sub in subjects:
            stats = [
                ("🫂", "Students", sub.get("total_students", 0)),
                ("🕰️", "Classes",  sub.get("total_classes",  0)),
            ]

            def make_share_btn(s):
                def share_btn():
                    share_col, delete_col = st.columns(2)
                    with share_col:
                        if st.button(f"Share Code: {s['name']}", key=f"share_{s['subject_id']}",
                                     icon=":material/share:", use_container_width=True):
                            share_subject_dialog(s["name"], s["subject_code"])
                    with delete_col:
                        if st.button("Delete Subject", key=f"delete_{s['subject_id']}",
                                     type="secondary", icon=":material/delete:", use_container_width=True):
                            st.session_state[f"confirm_delete_subject_{s['subject_id']}"] = True

                    if st.session_state.get(f"confirm_delete_subject_{s['subject_id']}"):
                        st.markdown(f"""
                            <div style="background-color:#2c2c2c; border:1px solid #e0a020;
                                border-left:4px solid #e0a020; border-radius:0.75rem;
                                padding:0.85rem 1rem; margin:0.5rem 0; color:#f0e0a0;
                                font-family:'Outfit',sans-serif; font-size:0.92rem;">
                                ⚠️ Delete <strong style="color:#fff;">{s['name']}</strong>
                                and all its attendance records?
                            </div>
                        """, unsafe_allow_html=True)
                        cc, ca = st.columns(2)
                        with cc:
                            if st.button("✓  Confirm Delete", key=f"confirm_delete_{s['subject_id']}",
                                         type="secondary", use_container_width=True):
                                delete_subject(s["subject_id"])
                                st.session_state.pop(f"confirm_delete_subject_{s['subject_id']}", None)
                                st.toast(f"✓ Deleted {s['name']} successfully")
                                st.rerun()
                        with ca:
                            if st.button("✕  Cancel", key=f"cancel_delete_{s['subject_id']}",
                                         type="tertiary", use_container_width=True):
                                st.session_state.pop(f"confirm_delete_subject_{s['subject_id']}", None)
                                st.rerun()
                return share_btn

            subject_card(
                name=sub.get("name"),
                code=sub.get("subject_code"),
                section=sub.get("section"),
                stats=stats,
                footer_callback=make_share_btn(sub),
            )
    else:
        st.markdown("""
            <div style="background-color:#2c2c2c; border:1px dashed #555555; border-radius:1rem;
                padding:2.5rem 1rem; text-align:center; margin-top:1rem;">
                <span style="font-size:2rem;">📭</span>
                <p style="color:#9a9a9a; font-family:'Outfit',sans-serif; font-size:1rem;
                   margin-top:0.5rem;">No subjects found. Create one above.</p>
            </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Tab: Attendance Records
# ──────────────────────────────────────────────────────────────

def teacher_tab_attendance_records():
    st.header("Attendance Records")
    teacher_id = st.session_state.teacher_data.get("teacher_id")

    # ── All formatting logic moved to service ─────────────────
    records = get_attendance_summary(teacher_id)

    if not records:
        st.info("No attendance records yet.")
        return

    df = pd.DataFrame(records)

    summary = (
        df.groupby(["timestamp", "time_display", "subject", "subject_code"])
        .agg(
            Present_Count=("is_present", "sum"),
            Total_Count=("is_present", "count"),
        )
        .reset_index()
    )

    summary["Attendance Stats"] = (
        "✅ " + summary["Present_Count"].astype(str)
        + " / " + summary["Total_Count"].astype(str) + " Students"
    )

    display_df = (
        summary.sort_values("timestamp", ascending=False)
        [["time_display", "subject", "subject_code", "Attendance Stats"]]
        .rename(columns={
            "time_display": "Time",
            "subject":      "Subject",
            "subject_code": "Subject Code",
        })
    )

    st.dataframe(display_df, width="stretch", hide_index=True)


# ──────────────────────────────────────────────────────────────
# Auth screens  (unchanged)
# ──────────────────────────────────────────────────────────────

def login_teacher(username, password):
    if not username or not password:
        return False
    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role   = "teacher"
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True
    return False


def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type="secondary", key="loginbackbtn"):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login using password", text_alignment="center")
    st.space()
    st.space()

    username = st.text_input("Enter username", placeholder="ananyaroy")
    password = st.text_input("Enter password", type="password", placeholder="Enter password")

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Login", icon=":material/passkey:", width="stretch"):
            if login_teacher(username, password):
                st.toast("Welcome back!", icon="👋")
                import time; time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username and password combo")
    with b2:
        if st.button("Register Instead", type="primary", icon=":material/passkey:", width="stretch"):
            st.session_state.teacher_login_type = "register"

    footer_dashboard()


def register_teacher(username, name, password, confirm):
    if not username or not name or not password:
        return False, "All fields are required!"
    if check_teacher_exists(username):
        return False, "Username already taken"
    if password != confirm:
        return False, "Passwords don't match"
    try:
        create_teacher(username, password, name)
        return True, "Successfully created! Login now."
    except Exception:
        return False, "Unexpected error!"


def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type="secondary", key="loginbackbtn"):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Register your teacher profile")
    st.space()
    st.space()

    username = st.text_input("Enter username", placeholder="ananyaroy")
    name     = st.text_input("Enter name",     placeholder="Ananya Roy")
    password = st.text_input("Enter password", type="password", placeholder="Enter password")
    confirm  = st.text_input("Confirm password", type="password", placeholder="Enter password")

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Register now", icon=":material/passkey:", width="stretch"):
            success, message = register_teacher(username, name, password, confirm)
            if success:
                st.success(message)
                import time; time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)
    with b2:
        if st.button("Login Instead", type="primary", icon=":material/passkey:", width="stretch"):
            st.session_state.teacher_login_type = "login"

    footer_dashboard()