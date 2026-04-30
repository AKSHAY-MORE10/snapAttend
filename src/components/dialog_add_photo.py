import streamlit as st


def add_photos_dialog():
    """Fallback photo uploader: appends uploaded images to `st.session_state.attendance_images`."""
    uploaded = st.file_uploader("Upload photos", accept_multiple_files=True, type=["png","jpg","jpeg"])
    if uploaded:
        if 'attendance_images' not in st.session_state:
            st.session_state.attendance_images = []
        for f in uploaded:
            try:
                img = f.getvalue()
                # Let Streamlit handle image bytes later; store raw bytes
                st.session_state.attendance_images.append(f)
            except Exception:
                st.warning(f"Could not add {f.name}")
        st.success("Added photos")
        st.experimental_rerun()
