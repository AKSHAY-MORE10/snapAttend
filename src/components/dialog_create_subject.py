import streamlit as st
from src.database.db import create_subject

def create_subject_dialog(teacher_id):
    """Inline create-subject form that stays visible until the user submits or cancels."""

    st.subheader("Create New Subject")

    with st.form("create_subject_form"):
        name = st.text_input("Subject name")
        subject_code = st.text_input("Subject code")
        section = st.text_input("Section")

        form_col1, form_col2 = st.columns(2)
        with form_col1:
            submitted = st.form_submit_button("Create")
        with form_col2:
            cancelled = st.form_submit_button("Cancel")

        if cancelled:
            st.session_state.show_create_subject_form = False
            st.rerun()

        if submitted:
            if not name or not subject_code or not section:
                st.error("All fields are required.")
                return

            try:
                result = create_subject(subject_code, name, section, teacher_id)
                if not result:
                    st.error("Subject was not created. Please check the database response.")
                    return

                st.session_state.show_create_subject_form = False
                st.success("Subject created")
                st.rerun()
            except Exception as e:
                st.error(f"Could not create subject: {e}")
