import streamlit as st
import pandas as pd
from supabase import create_client
import os
import json
import pypdf
from groq import Groq

# --- Configuration ---
st.set_page_config(page_title="Skill Migration", page_icon="📈", layout="wide")

ACCENT_ORANGE = "#FF8C00"
ACCENT_CYAN = "#00E0FF"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    def get_secret(key):
        if key in os.environ: return os.environ[key]
        try: return st.secrets[key]
        except: return None
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

try: supabase = init_supabase()
except: supabase = None

# --- Page Render ---
def skill_migration_page():
    # BACK BUTTON
    if st.button("← Back to Main Page"):
        st.switch_page("Main_Page.py")
        
    # CONSISTENT HEADER
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #FF8C00; margin-bottom: 0;">🚀 Job-Search-Agent</h1>
        <p style="color: #e2e8f0; font-size: 1.2rem; margin-top: 5px;">AI-Powered Career Guidance</p>
        <hr style="border-color: rgba(255, 140, 0, 0.3);">
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📈 Skill Migration Map")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to view your skill migration map.")
        return

    # SECTION 1: CV Upload Feature
    st.subheader("1️⃣ Upload Your Document")
    col_upload, col_buttons = st.columns([3, 1])
    
    with col_upload:
        uploaded_cv = st.file_uploader("Upload your CV (PDF/TXT)", type=["pdf", "txt"], key="skill_cv")
    
    with col_buttons:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Analyze CV", type="primary", use_container_width=True):
            st.info("Analysis started... (Connect to Agent logic here)")
            
    # Placeholder for logic
    st.info("Upload CV to see Industry Career Paths, Skill Gaps, and 90-Day Sprint Plans.")

skill_migration_page()
