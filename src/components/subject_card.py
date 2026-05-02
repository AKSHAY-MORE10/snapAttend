import streamlit as st

STAT_ICONS = {
    "Students": "group",
    "Classes": "calendar_clock",
    "Attendance": "fact_check",
    "Pending": "pending",
}
def subject_card(name, code, section, stats=None, footer_callback=None):

    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet"/>
    """, unsafe_allow_html=True)
     
    if stats:
        stats_html = '<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:1rem;">'
        for _, label, value in stats:
            icon_name = STAT_ICONS.get(label, "info")
            stats_html += f"""
            <div style="display:inline-flex; align-items:center; gap:5px;
                        background:#333333; border:1px solid #444;
                        padding:4px 12px; border-radius:999px;
                        font-size:0.85rem; color:#d4d4d4; font-family:'Outfit',sans-serif;">
                <span class="material-symbols-outlined" style="font-size:0.95rem; color:#888;">{icon_name}</span>
                <b style="color:#f0f0f0;">{value}</b>&nbsp;{label}
            </div>
            """
        stats_html += "</div>"

        html = f"""
            <div style="background:#2c2c2c; border-left:6px solid #c8c8c8; padding:1.4rem 1.6rem 1rem 1.6rem;
                        border-radius:1rem; border:1px solid #3d3d3d; margin-bottom:1.25rem;
                        box-shadow:0 2px 12px rgba(0,0,0,0.35);">
                        <h3 style="margin:0 0 0.6rem 0; color:#f0f0f0; font-family:'Climate Crisis',sans-serif;
                           font-size:1.3rem; letter-spacing:0.02em;">{name}</h3>
                           <div style="display:flex; align-items:center; gap:8px; margin-bottom:1rem; flex-wrap:wrap;">
                           <span style="display:inline-flex; align-items:center; gap:4px;
                                 background:#3a3a3a; color:#c8c8c8; padding:3px 10px;
                                 border-radius:999px; font-size:0.82rem; border:1px solid #555;
                                 font-family:'Outfit',sans-serif;">
                        <span class="material-symbols-outlined" style="font-size:0.9rem; vertical-align:middle;">tag</span>
                        {code}
                               </span>
                               <span style="color:#555; font-size:0.75rem;">•</span>
                               <span style="display:inline-flex; align-items:center; gap:4px;
                                   background:#3a3a3a; color:#c8c8c8; padding:3px 10px;
                                            border-radius:999px; font-size:0.82rem; border:1px solid #555;
                                            font-family:'Outfit',sans-serif;">
                                   <span class="material-symbols-outlined" style="font-size:0.9rem; vertical-align:middle;">door_open</span>
                                   Section {section}</span>
                            </div>{stats_html}
            </div>
            """
        
    st.markdown(html, unsafe_allow_html=True)

    if footer_callback:
        footer_callback()
        
