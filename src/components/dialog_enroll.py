import time

import streamlit as st

from src.database.config import supabase
from src.database.db import enroll_student_to_subject


@st.dialog("Enroll in Subject")
def enroll_dialog(subject_code: str | None = None):
    student_data = st.session_state.get('student_data')
    if not student_data:
        st.error('Please log in first.')
        return

    student_id = student_data['student_id']

    if subject_code:
        subject_code = subject_code.strip()

    if not subject_code:
        st.write('Enter the subject code provided by your teacher to enroll')
        subject_code = st.text_input('Subject Code', placeholder='Eg. CS101').strip()

    if st.button('Enroll now', type='primary', width='stretch'):
        if not subject_code:
            st.warning('Please enter a subject code')
            return

        res = (
            supabase.table('subjects')
            .select('subject_id, name, subject_code')
            .eq('subject_code', subject_code)
            .execute()
        )

        if not res.data:
            st.error('Subject code not found')
            return

        subject = res.data[0]

        check = (
            supabase.table('subject_students')
            .select('student_id')
            .eq('subject_id', subject['subject_id'])
            .eq('student_id', student_id)
            .execute()
        )

        if check.data:
            st.warning('You are already enrolled in this subject')
            return

        enroll_student_to_subject(student_id, subject['subject_id'])
        st.success('Successfully enrolled!')
        time.sleep(1)
        st.rerun()


auto_enroll_dialog = enroll_dialog