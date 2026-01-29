import streamlit as st
import pandas as pd
import pypdf
import re
import numpy as np
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
    url, key = get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

try: supabase = init_supabase()
except: supabase = None
try: 
    key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    groq_client = Groq(api_key=key) if key else None
except: groq_client = None

def extract_text(file):
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=11)
    pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))
    return bytes(pdf.output())

def calculate_ats_compliance(cv_text, jd_text):
    if not cv_text or not jd_text: return 0
    cv_words = set(re.findall(r'\b\w{3,}\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w{3,}\b', jd_text.lower()))
    intersection = len(cv_words.intersection(jd_words))
    return int((intersection / len(cv_words.union(jd_words)) * 100) if cv_words else 0)

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

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to access CV Compiler.")
        return

    col_upload, col_jd = st.columns(2)
    with col_upload:
        uploaded_file = st.file_uploader("Upload your CV", type=["pdf", "txt"], key="compiler_cv")
    with col_jd:
        jd_text = st.text_area("Paste Job Description:", height=150, key="compiler_jd")
    
    cv_text = ""
    if uploaded_file: cv_text = extract_text(uploaded_file)

    if st.button("🚀 Optimize Bullets", type="primary"):
        if groq_client and cv_text and jd_text:
            with st.spinner("Optimizing..."):
                prompt = f"Rewrite these CV bullets to match this Job Description. CV: {cv_text[:3000]} JD: {jd_text}"
                resp = groq_client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.3-70b-versatile")
                st.session_state['opt_cv'] = resp.choices[0].message.content
                st.rerun()

    if 'opt_cv' in st.session_state:
        st.subheader("✨ Optimized CV")
        st.text_area("Result", st.session_state['opt_cv'], height=300)
        pdf = create_pdf(st.session_state['opt_cv'])
        st.download_button("Download PDF", pdf, "optimized.pdf", "application/pdf")

compiler_page()
