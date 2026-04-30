import streamlit as st
from src.database.db import create_subject

def create_subject_dialog(teacher_id):
    """Simple inline create-subject form used as a fallback dialog.
    Calls `create_subject(subject_code, name, section, teacher_id)` if available.
    """
    with st.form("create_subject_form"):
        name = st.text_input("Subject name")
        subject_code = st.text_input("Subject code")
        section = st.text_input("Section")
        submitted = st.form_submit_button("Create")
        if submitted:
            try:
                # create_subject expected signature: (subject_code, name, section, teacher_id)
                # try both possible orders defensively
                try:
                    res = create_subject(subject_code, name, section, teacher_id)
                except TypeError:
                    res = create_subject(name, subject_code, section, teacher_id)

                st.success("Subject created")
                # show DB response for debugging (will be a list with inserted row or error)
                st.write(res)
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Could not create subject: {e}")
