import streamlit as st
import pandas as pd
import pypdf
from supabase import create_client
import os
import json
from groq import Groq

# --- Configuration ---
st.set_page_config(page_title="Skill Migration", page_icon="📈", layout="wide")

ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"

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

if 'groq' not in st.session_state:
    key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    st.session_state.groq = Groq(api_key=key) if key else None

def extract_text(file):
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def fetch_latest_report():
    user_id = st.session_state.get('user_id')
    if not user_id or not supabase: return None
    try:
        response = supabase.table("analyses").select("report_json").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if response.data:
            return response.data[0]['report_json']
    except: pass
    return None

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

    # INITIALIZATION
    if 'sprint_plan' not in st.session_state: st.session_state.sprint_plan = None
    if 'completed_tasks' not in st.session_state: st.session_state.completed_tasks = set()

    # SECTION 1: CV Upload
    st.subheader("1️⃣ Upload Your Document")
    col_upload, col_buttons = st.columns([3, 1])
    with col_upload:
        uploaded_cv = st.file_uploader("Upload your CV (PDF/TXT)", type=["pdf", "txt"], key="skill_cv")
    with col_buttons:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Analyze CV", type="primary", use_container_width=True):
            if uploaded_cv and st.session_state.get('agent'):
                with st.spinner("Analyzing..."):
                    txt = extract_text(uploaded_cv)
                    md, rep, src = st.session_state.agent.generate_strategy(txt, "All")
                    st.session_state.skill_migration_report = rep
                    st.rerun()

    # LOAD REPORT
    report = st.session_state.get('skill_migration_report')
    if not report: report = fetch_latest_report()

    if not report:
        st.info("Upload CV to see your Skill Migration report.")
        return

    # SECTION 2: SCORES
    st.subheader("2️⃣ Your Profile Scores")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Predictive Match", f"{report.get('predictive_score', 0)}%")
    with c2: st.metric("Skills Strength", f"{report.get('tech_score', 0)}%")
    with c3: st.error(f"Focus Area: {report.get('weakest_link_skill', 'N/A')}")

    # SECTION 3: SPRINT PLAN
    st.subheader("3️⃣ AI-Powered 90-Day Skill Sprint")
    if st.button("🚀 Generate Sprint Plan", type="primary"):
        weakest = report.get('weakest_link_skill', 'Skills')
        if st.session_state.groq:
            prompt = f"Create a 4-week sprint plan to improve {weakest}. Format: Week 1: Task..."
            resp = st.session_state.groq.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.3-70b-versatile")
            st.session_state.sprint_plan = resp.choices[0].message.content
            st.rerun()

    if st.session_state.sprint_plan:
        st.markdown(st.session_state.sprint_plan)

skill_migration_page()
