import streamlit as st
import os
import pypdf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from agent import JobSearchAgent

# --- 1. PAGE CONFIG & STUDIO STYLE ---
st.set_page_config(page_title="AEQUOR", page_icon="🌊", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1d222a; border: 1px solid #2b313e;
        border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    h1, h2, h3 { color: #ffffff; }
    .stButton>button { background-color: #FFD700; color: #000; font-weight: bold; border: none; }
    .stDataFrame { border: 1px solid #333; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. AUTHENTICATION SYSTEM ---
if 'user' not in st.session_state: st.session_state.user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = 'login' # login or signup

# Mock Database (In production, replace this with SQL/Firebase)
if 'db_users' not in st.session_state:
    st.session_state.db_users = {"demo": "password123"} # Default user
if 'user_history' not in st.session_state:
    st.session_state.user_history = {} # Key: username, Value: DataFrame

def login_user(username, password):
    if username in st.session_state.db_users and st.session_state.db_users[username] == password:
        st.session_state.user = username
        st.rerun()
    else:
        st.error("Invalid username or password")

def signup_user(username, password):
    if username in st.session_state.db_users:
        st.error("User already exists")
    else:
        st.session_state.db_users[username] = password
        st.session_state.user_history[username] = pd.DataFrame(columns=["Date", "Company", "Role", "Status"])
        st.success("Account created! Please log in.")
        st.session_state.auth_mode = 'login'

def logout_user():
    st.session_state.user = None
    st.rerun()

# --- 3. AGENT SETUP ---
if 'agent' not in st.session_state:
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    q_host = st.secrets.get("QDRANT_HOST", os.environ.get("QDRANT_HOST"))
    q_key = st.secrets.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY"))
    
    if api_key and q_host:
        st.session_state.agent = JobSearchAgent(api_key, q_host, q_key)
    else:
        st.session_state.agent = None

if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None

# --- 4. DASHBOARD COMPONENT ---
def render_user_dashboard():
    st.title(f"👋 Welcome back, {st.session_state.user}")
    
    # Profile Summary
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.container(border=True):
            st.subheader("👤 Profile")
            st.markdown(f"**Username:** {st.session_state.user}")
            st.markdown(f"**Status:** Active Candidate")
            st.markdown(f"**Last Login:** {datetime.now().strftime('%Y-%m-%d')}")
            if st.button("Logout", type="secondary"):
                logout_user()

    with col2:
        with st.container(border=True):
            st.subheader("📂 Application History")
            # Mock Data if empty
            user_data = st.session_state.user_history.get(st.session_state.user, pd.DataFrame())
            if user_data.empty:
                # Add some dummy data for visualization
                dummy_data = {
                    "Date": ["2024-01-10", "2024-01-12", "2024-01-15"],
                    "Company": ["Google", "Spotify", "Tesla"],
                    "Role": ["Data Analyst", "Product Manager", "Engineer"],
                    "Status": ["Applied", "Interviewing", "Rejected"]
                }
                user_data = pd.DataFrame(dummy_data)
                
            st.dataframe(user_data, use_container_width=True, hide_index=True)

# --- 5. MAIN APP LOGIC ---
def extract_text(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            return "".join([page.extract_text() for page in reader.pages])
        else:
            return uploaded_file.read().decode("utf-8")
    except: return ""

def main():
    # --- AUTH GUARD ---
    if not st.session_state.user:
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            st.image("aequor_logo_placeholder.png", width=100)
            st.title("AEQUOR Access")
            
            mode = st.radio("Select Mode", ["Login", "Sign Up"], horizontal=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if mode == "Login":
                if st.button("Login", use_container_width=True, type="primary"):
                    login_user(username, password)
            else:
                if st.button("Create Account", use_container_width=True, type="primary"):
                    signup_user(username, password)
        return  # STOP here if not logged in

    # --- APP CONTENT (Only reaches here if logged in) ---
    
    # sidebar
    with st.sidebar:
        st.image("aequor_logo_placeholder.png", width=50)
        st.header("Navigation")
        page = st.radio("Go to", ["Home / Dashboard", "Emotional Tracker", "Skill Migration", "CV Compiler"])
        st.divider()
        st.markdown(f"Logged in as: **{st.session_state.user}**")
        if st.button("Logout"): logout_user()

    # Routing
    if page == "Home / Dashboard":
        render_user_dashboard()
        
        st.divider()
        st.header("🚀 Start New Strategy")
        
        col_input, col_kpi = st.columns([1, 1])
        
        with col_input:
            role_filter = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering", "HR"])
            uploaded_file = st.file_uploader("Upload CV for Analysis", type=["pdf", "txt"])
            
            if st.button("Generate Strategy", type="primary"):
                if uploaded_file and st.session_state.agent:
                    with st.spinner("Agent Analyzing..."):
                        cv_text = extract_text(uploaded_file)
                        md, report, sources = st.session_state.agent.generate_strategy(cv_text, role_filter)
                        st.session_state.results = {"md": md, "report": report, "sources": sources}
                        st.session_state['skill_gap_report'] = report
                        st.rerun()

        # Display Results
        if "results" in st.session_state:
            res = st.session_state.results
            
            # KPI Cards
            st.markdown("### 📊 Live Analysis")
            k1, k2, k3 = st.columns(3)
            k1.metric("Match Score", f"{res['report'].get('predictive_score')}%")
            k2.metric("Tech Depth", f"{res['report'].get('tech_score')}%")
            k3.error(f"Weakness: {res['report'].get('weakest_link_skill')}")
            
            st.divider()
            
            # MARKDOWN TABLES (This will now render the tables from Agent)
            st.markdown(res['md'])

    # Placeholder pages for routing demo
    elif page == "Emotional Tracker":
        st.switch_page("pages/1_Emotional_Tracker.py")
    elif page == "Skill Migration":
        st.switch_page("pages/3_Skill_Migration.py")
    elif page == "CV Compiler":
        st.switch_page("pages/4_CV_Compiler.py")

if __name__ == "__main__":
    main()
