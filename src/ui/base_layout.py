import streamlit as st



def style_background_home():

    st.markdown("""
        <style>

                .stApp {
                    background: #5865F2 !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color:#E0E3FF !important;
                    padding:2.5rem !important;
                    border-radius: 5rem !important;
                    }
        </style>  

                """
            ,unsafe_allow_html=True)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background: #E0E3FF !important;
                }

        </style>  

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

        # #MainMenu, footer, header {
        #     visibility: hidden;
        }

        .block-container {
            padding-top:1.5rem !important;    
        }

        h1 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 3.5rem !important;
            line-height:1.1 !important;
            margin-bottom:0rem !important;
        }

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 2rem !important;
            line-height:0.9 !important;
            margin-bottom:0rem !important;
            color: #3a3a3a !important;
        }

        h3, h4, p {
            font-family: 'Outfit', sans-serif;    
        }


        .stApp .stTextInput input,
        .stApp .stTextArea textarea {
            color: var(--text-color) !important;
            opacity: 0.95 !important;
            border: 1px solid #ccc !important;
        }

        .stApp .stTextInput input::placeholder,
        .stApp .stTextArea textarea::placeholder,
        .stApp input::placeholder,
        .stApp textarea::placeholder {
            color: var(--text-color) !important;
            opacity: 0.45 !important;
        }

        .stApp .stTextInput input::-webkit-input-placeholder,
        .stApp .stTextArea textarea::-webkit-input-placeholder,
        .stApp input::-webkit-input-placeholder,
        .stApp textarea::-webkit-input-placeholder {
            color: var(--text-color) !important;
            opacity: 0.55 !important;
        }

        /* OPTIONAL: label color */
        .stTextInput label {
            color: black !important;
        }

        /* Buttons */
        button[kind="primary"]{
            color: white !important;
        }

        button{
            border-radius: 1.5rem !important;
            background-color: #5865F2 !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out !important;
        }

        button[kind="secondary"]{
            border-radius: 1.5rem !important;
            background-color: #EB459E !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
        }

        button[kind="tertiary"]{
            border-radius: 1.5rem !important;
            background-color: black !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
        }

        button:hover{
            transform: scale(1.05);
        }

        hr {
            background-color: #878787 !important;
            border: none !important;
            height: 1px !important;
        }

        </style>
    """, unsafe_allow_html=True)