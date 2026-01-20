import streamlit as st
import os
import pypdf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from agent import JobSearchAgent
from supabase import create_client, Client

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="AEQUOR", page_icon="🚀", layout="wide")

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
    
    /* Buttons */
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. SUPABASE CONNECTION ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    supabase = None
    st.error(f"Database connection failed: {e}")

# --- 3. AUTHENTICATION & STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = 'login'
if 'cv_text_to_process' not in st.session_state: st.session_state['cv_text_to_process'] = ""

def login(email, password):
    if not supabase:
        st.error("Database not connected. Check API Keys.")
        return

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = response.user.email
        st.session_state.user_id = response.user.id
        
        # --- SELF-HEALING FIX: Ensure Profile Exists ---
        # This prevents the Foreign Key error if the Trigger failed previously.
        try:
            user_id = response.user.id
            profile = supabase.table("profiles").select("id").eq("id", user_id).execute()
            if not profile.data:
                supabase.table("profiles").insert({"id": user_id, "username": email}).execute()
        except Exception:
            pass # Ignore if it exists or fails silently
        # -----------------------------------------------

        st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def signup(email, password, username):
    if not supabase:
        st.error("Database not connected.")
        return

    try:
        response = supabase.auth.sign_up({
            "email": email, 
            "password": password, 
            "options": {"data": {"username": username}}
        })
        st.success("Account created! Check your email to confirm.")
    except Exception as e:
        st.error(f"Signup failed: {e}")

def logout():
    # Fix: Completely clear state to prevent data leaking to next user
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- 4. INIT AGENT ---
if 'agent' not in st.session_state:
    api = st.secrets.get("GEMINI_API_KEY")
    qh = st.secrets.get("QDRANT_HOST")
    qk = st.secrets.get("QDRANT_API_KEY")
    
    if api and qh:
        st.session_state.agent = JobSearchAgent(api, qh, qk)
    else:
        st.session_state.agent = None

if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None

# --- 5. APP LOGIC ---
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
            
            if not supabase:
                st.warning("⚠️ Secrets missing. Please check .streamlit/secrets.toml")
            
            mode = st.radio("Select Mode", ["Login", "Sign Up"], horizontal=True)
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if mode == "Sign Up":
                username = st.text_input("Username")
                if st.button("Sign Up", type="primary"): 
                    signup(email, password, username)
            else:
                if st.button("Login", type="primary"): 
                    login(email, password)
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
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Profile Status", "Active")
    c2.metric("User ID", st.session_state.user_id[:8] + "...")
    c3.metric("System Health", "Online", delta="Connected")
    
    st.divider()

    # Input Area
    st.subheader("📝 Start New Analysis")
    col_in, col_act = st.columns([2, 1])
    
    with col_in:
        role = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering", "HR"])
        f = st.file_uploader("Upload CV", type=["pdf", "txt"])
    
    with col_act:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Generate Strategy", type="primary", use_container_width=True):
            if f and st.session_state.agent:
                with st.spinner("Agent is searching live jobs..."):
                    txt = extract_text(f)
                    st.session_state['cv_text_to_process'] = txt 
                    
                    md, rep, src = st.session_state.agent.generate_strategy(txt, role)
                    
                    st.session_state.results = {"md": md, "rep": rep, "src": src}
                    st.session_state['skill_gap_report'] = rep
                    
                    # Save to Supabase (History)
                    if supabase:
                        try:
                            supabase.table("analyses").insert({
                                "user_id": st.session_state.user_id,
                                "report_json": rep
                            }).execute()
                        except Exception as e:
                            print(f"History save failed: {e}")

                    st.rerun()
            elif not st.session_state.agent:
                st.error("Agent not initialized. Check GEMINI/QDRANT keys.")

    # Results Display
    if "results" in st.session_state:
        res = st.session_state.results
        
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

        st.markdown("---")
        st.markdown(res['md'])
        
        if res['src']:
            with st.expander("🔗 Verified Sources"):
                for s in res['src']:
                    st.markdown(f"- [{s['title']}]({s['uri']})")

if __name__ == "__main__":
    main()
