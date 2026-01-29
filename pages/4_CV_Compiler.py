import streamlit as st
import pandas as pd
import pypdf
from supabase import create_client
from groq import Groq
from fpdf import FPDF
import os

# --- Configuration ---
st.set_page_config(page_title="CV Compiler", page_icon="🤖", layout="wide")
ACCENT_ORANGE = "#FF8C00"

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

def compiler_page():
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
    
    st.subheader("🤖 CV Compiler & Optimizer")
    st.caption("All-in-one: Optimize your CV, check ATS compliance, and track applications")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to access CV Compiler.")
        return

    # Content
    col_upload, col_jd = st.columns(2)
    with col_upload:
        st.file_uploader("Upload your CV (PDF/TXT)", type=["pdf", "txt"], key="compiler_cv")
    with col_jd:
        st.text_area("Paste Job Description:", height=150, key="compiler_jd")
    
    if st.button("🚀 Optimize Bullets", type="primary", use_container_width=True):
        st.info("Connecting to AI for optimization...")

compiler_page()
