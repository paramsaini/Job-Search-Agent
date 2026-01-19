import streamlit as st
import os
import pypdf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from agent import JobSearchAgent

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="AEQUOR", page_icon="🌊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fff; font-family: 'Inter', sans-serif; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1d222a; 
        border: 1px solid #333;
        border-radius: 8px;
        padding: 16px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #FFD700 !important; }
    /* Force Tables to look good */
    table { width: 100% !important; border-collapse: collapse !important; }
    th { background-color: #333 !important; color: #FFD700 !important; padding: 10px !important; }
    td { border-bottom: 1px solid #444 !important; padding: 10px !important; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. AUTH & SETUP ---
if 'user' not in st.session_state: st.session_state.user = None
if 'db_users' not in st.session_state: st.session_state.db_users = {"demo": "password", "admin": "admin"}
if 'user_history' not in st.session_state: st.session_state.user_history = {}

def login(u, p):
    if u in st.session_state.db_users and st.session_state.db_users[u] == p:
        st.session_state.user = u
        if u not in st.session_state.user_history: st.session_state.user_history[u] = []
        st.rerun()
    else: st.error("Invalid Login (Try: demo / password)")

def logout():
    st.session_state.user = None
    st.rerun()

# --- 3. AGENT INITIALIZATION ---
if 'agent' not in st.session_state:
    api = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    qh = st.secrets.get("QDRANT_HOST", os.environ.get("QDRANT_HOST"))
    qk = st.secrets.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY"))
    
    if api and qh:
        st.session_state.agent = JobSearchAgent(api, qh, qk)
    else:
        st.session_state.agent = None

if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None

# --- 4. MAIN APP ---
def extract_text(file):
    try:
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def main():
    # Login Screen
    if not st.session_state.user:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.title("AEQUOR Access")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login", type="primary"): login(u, p)
        return

    # Logged In UI
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.user}**")
        st.divider()
        nav = st.radio("Navigate", ["Dashboard", "Emotional Tracker", "Skill Migration", "CV Compiler"])
        st.divider()
        if st.button("Logout"): logout()

    # Routing
    if nav != "Dashboard":
        # Map to your existing pages
        page_map = {
            "Emotional Tracker": "pages/1_Emotional_Tracker.py",
            "Skill Migration": "pages/3_Skill_Migration.py",
            "CV Compiler": "pages/4_CV_Compiler.py"
        }
        st.switch_page(page_map[nav])

    # Dashboard Content
    st.title("🚀 Career Strategy Dashboard")
    
    # Input
    col_in, col_act = st.columns([3, 1])
    with col_in:
        role = st.selectbox("Target Role Context", ["All", "Data Science", "Sales", "Engineering", "HR"])
        f = st.file_uploader("Upload CV", type=["pdf", "txt"])
    
    with col_act:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Generate Strategy", type="primary"):
            if f and st.session_state.agent:
                with st.spinner("Agent is analyzing & searching..."):
                    txt = extract_text(f)
                    md, rep, src = st.session_state.agent.generate_strategy(txt, role)
                    st.session_state.results = {"md": md, "rep": rep, "src": src}
                    st.session_state['skill_gap_report'] = rep
                    st.session_state.user_history[st.session_state.user].append(datetime.now())
                    st.rerun()

    # Results
    if "results" in st.session_state:
        res = st.session_state.results
        
        st.markdown("### 📊 Live Analysis")
        k1, k2, k3 = st.columns(3)
        with k1: 
             st.metric("Match Score", f"{res['rep'].get('predictive_score', 0)}%")
             st.progress(res['rep'].get('predictive_score', 0)/100)
        with k2: st.metric("Tech Depth", f"{res['rep'].get('tech_score', 0)}%")
        with k3: st.error(f"Weakest Link: {res['rep'].get('weakest_link_skill', 'None')}")

        st.markdown("---")
        st.markdown(res['md'])
        
        if res['src']:
            with st.expander("View Source Links"):
                for s in res['src']: st.markdown(f"- [{s['title']}]({s['uri']})")

if __name__ == "__main__":
    main()
