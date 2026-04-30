import streamlit as st


def attendance_result_dialog(results_df, attendance_list=None):
    """Displays attendance results in a table and stores attendance_list in session_state for later processing."""
    st.subheader("Attendance Results")
    try:
        st.dataframe(results_df)
    except Exception:
        st.write(results_df)

    if attendance_list:
        st.session_state.last_attendance_to_log = attendance_list
        if st.button("Log Attendance"):
            st.success("Attendance queued (stub)")
