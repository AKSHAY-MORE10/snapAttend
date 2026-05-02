import streamlit as st


def style_background_home():
    st.markdown("""
        <style>
                .stApp {
                    background: #1a1a1a !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color: #2c2c2c !important;
                    padding: 2.5rem !important;
                    border-radius: 5rem !important;
                }
        </style>  
        """, unsafe_allow_html=True)


def style_background_dashboard():
    st.markdown("""
        <style>
                .stApp {
                    background: #242424 !important;
                }
        </style>  
        """, unsafe_allow_html=True)


def style_base_layout():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

        :root {
            --accent:       #c8c8c8;
            --accent-alt:   #888888;
            --text-primary: #f0f0f0;
            --text-muted:   #9a9a9a;
            --surface:      #2c2c2c;
            --border:       #3d3d3d;
        }
        
        #MainMenu, footer, header {
             visibility: hidden;
        }

        .block-container {
            padding-top: 1.5rem !important;
        }

        h1 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 3.5rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0rem !important;
            color: #f0f0f0 !important;
        }

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 2rem !important;
            line-height: 0.9 !important;
            margin-bottom: 0rem !important;
            color: #c8c8c8 !important;
        }

        h3, h4, p {
            font-family: 'Outfit', sans-serif;
            color: #d4d4d4 !important;
        }

        /* Inputs */
        .stApp .stTextInput input,
        .stApp .stTextArea textarea {
            background-color: #333333 !important;
            color: #f0f0f0 !important;
            border: 1px solid #3d3d3d !important;
            border-radius: 0.5rem !important;
        }

        .stApp .stTextInput input::placeholder,
        .stApp .stTextArea textarea::placeholder,
        .stApp input::placeholder,
        .stApp textarea::placeholder {
            color: #7a7a7a !important;
            opacity: 1 !important;
        }

        .stApp .stTextInput input::-webkit-input-placeholder,
        .stApp .stTextArea textarea::-webkit-input-placeholder {
            color: #7a7a7a !important;
            opacity: 1 !important;
        }

        .stTextInput label,
        .stTextArea label {
            color: #c8c8c8 !important;
        }

        /* ── PRIMARY button (default) ── */
        button {
            border-radius: 1.5rem !important;
            background-color: #c8c8c8 !important;
            color: #1a1a1a !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out, background-color 0.2s, color 0.2s !important;
        }

        /* keep inner <p> / <span> dark too */
        button p, button span {
            color: #1a1a1a !important;
        }

        /* ── PRIMARY hover ── */
        button:hover {
            transform: scale(1.05) !important;
            background-color: #ffffff !important;
            color: #1a1a1a !important;
        }

        button:hover p, button:hover span {
            color: #1a1a1a !important;
        }

        /* ── SECONDARY button ── */
        button[kind="secondary"] {
            background-color: #555555 !important;
            color: #f0f0f0 !important;
        }

        button[kind="secondary"] p, button[kind="secondary"] span {
            color: #f0f0f0 !important;
        }

        /* ── SECONDARY hover ── */
        button[kind="secondary"]:hover {
            background-color: #6e6e6e !important;
            color: #ffffff !important;
        }

        button[kind="secondary"]:hover p, button[kind="secondary"]:hover span {
            color: #ffffff !important;
        }

        /* ── TERTIARY button ── */
        button[kind="tertiary"] {
            background-color: #3a3a3a !important;
            color: #c8c8c8 !important;
            border: 1px solid #555555 !important;
        }

        button[kind="tertiary"] p, button[kind="tertiary"] span {
            color: #c8c8c8 !important;
        }

        /* ── TERTIARY hover ── */
        button[kind="tertiary"]:hover {
            background-color: #4a4a4a !important;
            color: #ffffff !important;
            border-color: #888888 !important;
        }

        button[kind="tertiary"]:hover p, button[kind="tertiary"]:hover span {
            color: #ffffff !important;
        }

        hr {
            background-color: #3d3d3d !important;
            border: none !important;
            height: 1px !important;
        }

        </style>
    """, unsafe_allow_html=True)