import streamlit as st
from supabase import create_client, Client
import os
import pypdf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from agent import JobSearchAgent

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="AEQUOR", page_icon="🌊", layout="wide")

st.markdown("""
    <style>
    /* Dark Theme Optimization */
    .stApp { background-color: #0e1117; color: #fff; font-family: 'Inter', sans-serif; }
    
    /* Card/Container Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1d222a; 
        border: 1px solid #333;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 10px;
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #FFD700 !important; }
    
    /* Table Styling */
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #333; color: #FFD700; padding: 8px; text-align: left; }
    td { border-bottom: 1px solid #444; padding: 8px; }
    
    /* Buttons */
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- INIT SUPABASE ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- AUTHENTICATION LOGIC ---
if 'user' not in st.session_state: st.session_state.user = None
if 'user_id' not in st.session_state: st.session_state.user_id = None

def login(email, password):
    try:
        # Supabase handles security
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = response.user.email
        st.session_state.user_id = response.user.id
        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def signup(email, password, username):
    try:
        # Metadata 'username' is passed to the Postgres Trigger we created
        response = supabase.auth.sign_up({
            "email": email, 
            "password": password, 
            "options": {"data": {"username": username}}
        })
        st.success("Account created! Please check your email to confirm.")
    except Exception as e:
        st.error(f"Signup failed: {e}")



def logout():
    st.session_state.user = None
    st.rerun()

# --- 3. INIT AGENT ---
if 'agent' not in st.session_state:
    api = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    qh = st.secrets.get("QDRANT_HOST", os.environ.get("QDRANT_HOST"))
    qk = st.secrets.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY"))
    
    if api and qh:
        st.session_state.agent = JobSearchAgent(api, qh, qk)
    else:
        st.session_state.agent = None

if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None

# --- 4. APP LOGIC ---
def extract_text(file):
    try:
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def main():
    # --- LOGIN SCREEN ---
    if not st.session_state.user:
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.header("AEQUOR Access")
            mode = st.radio("Select Mode", ["Login", "Sign Up"], horizontal=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            
            if mode == "Login":
                if st.button("Login", type="primary"): login(u, p)
            else:
                if st.button("Sign Up", type="primary"): signup(u, p)
        return

    # --- MAIN DASHBOARD (LOGGED IN) ---
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.user}**")
        st.divider()
        nav = st.radio("Navigate", ["Dashboard", "Emotional Tracker", "Skill Migration", "CV Compiler"])
        st.divider()
        if st.button("Logout"): logout()

    # Routing
    if nav == "Emotional Tracker": st.switch_page("pages/1_Emotional_Tracker.py")
    if nav == "Skill Migration": st.switch_page("pages/3_Skill_Migration.py")
    if nav == "CV Compiler": st.switch_page("pages/4_CV_Compiler.py")

    # --- DASHBOARD CONTENT ---
    st.title(f"🚀 Career Strategy Dashboard")
    
    # User Stats Row
    c1, c2, c3 = st.columns(3)
    c1.metric("Profile Status", "Active")
    c2.metric("Jobs Analyzed", len(st.session_state.user_history.get(st.session_state.user, [])))
    c3.metric("System Health", "Online", delta="Stable")
    
    st.divider()

    # Input Area
    st.subheader("📄 Start New Analysis")
    col_in, col_act = st.columns([2, 1])
    
    with col_in:
        role = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering", "HR"])
        f = st.file_uploader("Upload CV", type=["pdf", "txt"])
    
    with col_act:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Generate Strategy", type="primary", use_container_width=True):
            if f and st.session_state.agent:
                with st.spinner("Agent is searching live jobs..."):
                    txt = extract_text(f)
                    
                    # --- FIX: SAVE TEXT FOR OTHER PAGES ---
                    st.session_state['cv_text_to_process'] = txt 
                    
                    md, rep, src = st.session_state.agent.generate_strategy(txt, role)
                    
                    # Save results
                    st.session_state.results = {"md": md, "rep": rep, "src": src}
                    st.session_state['skill_gap_report'] = rep
                    # Log history
                    st.session_state.user_history[st.session_state.user].append(datetime.now())
                    st.rerun()

    # Results Display
    if "results" in st.session_state:
        res = st.session_state.results
        
        # 1. KPI Cards
        st.markdown("### 📊 Analysis Results")
        k1, k2, k3 = st.columns(3)
        
        with k1: 
            with st.container(border=True):
                st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
                st.progress(res['rep'].get('predictive_score', 0)/100)
        with k2:
            with st.container(border=True):
                st.metric("Tech Depth", f"{res['rep'].get('tech_score')}%")
                st.progress(res['rep'].get('tech_score', 0)/100)
        with k3:
            with st.container(border=True):
                st.error(f"Weakest Link: {res['rep'].get('weakest_link_skill')}")
                st.caption("Focus your learning here.")

        # 2. MARKDOWN TABLES (The Fixed Output)
        st.markdown("---")
        st.markdown(res['md'])
        
        # 3. Sources
        if res['src']:
            with st.expander("🔗 Verified Sources"):
                for s in res['src']:
                    st.markdown(f"- [{s['title']}]({s['uri']})")

if __name__ == "__main__":
    main()
