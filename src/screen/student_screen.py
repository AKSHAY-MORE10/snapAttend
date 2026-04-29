import streamlit as st
from src.components.header import header_dashboard
from src.ui.base_layout import style_base_layout, style_background_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np

def student_screen():
    style_background_dashboard()
    style_base_layout()

    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")

    with c1:
        header_dashboard()

    with c2:
        if st.button("Go to home page", key='back_home_login'):
            st.session_state["login_type"] = None
            st.rerun()



    st.header("Login using face recognition")
    # st.divider()
    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        image = np.array(Image.open(photo_source))
        st.image(image, caption="Your face", use_column_width=True)
    
    st.divider()
    footer_dashboard()