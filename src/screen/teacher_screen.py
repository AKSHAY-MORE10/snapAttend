import streamlit as st
from src.components.header import header_dashboard
from src.ui.base_layout import style_base_layout, style_background_dashboard
from src.components.footer import footer_dashboard


def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    # Default page
    if "teacher_page" not in st.session_state:
        st.session_state["teacher_page"] = "login"

    if st.session_state["teacher_page"] == "login":
        teacher_screen_login()
    elif st.session_state["teacher_page"] == "register":
        teacher_register()
    elif st.session_state["teacher_page"] == "dashboard":
        teacher_dashboard()


# ---------------- LOGIN ----------------
def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")

    with c1:
        header_dashboard()

    with c2:
        if st.button("Go to home page", key='back_home_login'):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login using password")
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    username = st.text_input("Enter username", placeholder="Enter your username")
    password = st.text_input("Enter password", type="password")

    st.divider()

    btn1, btn2 = st.columns(2)

    with btn1:
        if st.button("Login", key='login_btn', icon=":material/login:", width="stretch"):
            if username and password:
                st.session_state["teacher_name"] = username
                st.session_state["teacher_page"] = "dashboard"
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Enter username & password")

    with btn2:
        if st.button("Register Instead", key='go_register_btn', icon=":material/person_add:", width="stretch"):
            st.session_state["teacher_page"] = "register"
            st.rerun()

    footer_dashboard()




# ---------------- REGISTER ----------------
def teacher_register():
    c1, c2 = st.columns(2, vertical_alignment="center", gap="large")

    with c1:
        header_dashboard()

    with c2:
        if st.button("Go to home page", key='back_home_register'):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Register your teacher profile")
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ✅ ADD NAME FIELD
    teacher_name = st.text_input("Enter your name", placeholder="e.g. John Doe")
    teacher_username = st.text_input("Create username", placeholder="Enter username")
    teacher_password = st.text_input("Create password", type="password", placeholder="Enter password")
    confirm_password = st.text_input("Confirm password", type="password", placeholder="Re-enter password")

    st.divider()

    btn1, btn2 = st.columns(2)



    with btn1:
        if st.button("Register", key='register_btn', icon=":material/person_add:", width="stretch", type="primary"):
            
            # ✅ VALIDATION
            if not teacher_name or not teacher_username or not teacher_password:
                st.error("All fields are required")

            elif teacher_password != confirm_password:
                st.error("Passwords do not match")

            else:
                # ✅ SAVE DATA (for now session only)
                st.session_state["teacher_name"] = teacher_name
                st.session_state["teacher_username"] = teacher_username

                st.success(f"Registered successfully, {teacher_name}!")

                # Go back to login
                st.session_state["teacher_page"] = "login"
                st.rerun()




    with btn2:
        if st.button("Back to Login", key='back_login_btn', width="stretch"):
            st.session_state["teacher_page"] = "login"
            st.rerun()

    footer_dashboard()