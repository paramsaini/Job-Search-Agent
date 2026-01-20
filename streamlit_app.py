import streamlit as st
import os
import pypdf
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from agent import JobSearchAgent
from supabase import create_client, Client

# --- 1. CONFIG & STYLING (NEW ANIMATED BACKGROUND) ---
st.set_page_config(page_title="AEQUOR", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    /* 1. The Static Professional Blue Background */
    .stApp {
        /* A deep, professional, static dark blue to purple gradient */
        background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
        background-attachment: fixed; /* Ensures background stays fixed while scrolling */
    }

    /* REMOVED: The animation keyframes are gone now. */

    /* 2. Glassmorphism Theme (Semi-transparent Containers) */
    /* Targets main containers, metrics, expanders, forms, and sidebar content */
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"],
    div[data-testid="stExpanderDetails"],
    div[data-testid="stForm"],
    [data-testid="stSidebar"] > div {
        background-color: rgba(15, 23, 42, 0.6) !important; /* Dark blue semi-transparent */
        backdrop-filter: blur(12px); /* The frosted glass effect */
        border: 1px solid rgba(88, 116, 176, 0.2) !important; /* Subtle glowing border */
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        padding: 15px;
        margin-bottom: 10px;
    }

    /* Text & Metric Colors to pop against the dark background */
    h1, h2, h3, p, label, .stMarkdown, div[data-testid="stCaptionContainer"] {
        color: #e2e8f0 !important; /* Light gray/white text */
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        color: #00e0ff !important; /* Neon Cyan for numbers */
        text-shadow: 0 0 10px rgba(0, 224, 255, 0.6);
    }
    div[data-testid="stMetricDelta"] {
        color: #10b981 !important; /* Neon Green for positive changes */
    }

    /* Buttons with a digital glow (KEPT AS REQUESTED) */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        background: linear-gradient(90deg, #0062ff, #00c6ff); /* Cyan/Blue Gradient */
        border: none;
        color: white !important;
        box-shadow: 0 0 10px rgba(0, 98, 255, 0.5); /* The shinning glow effect */
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(0, 198, 255, 0.8); /* Brighter shine on hover */
        transform: translateY(-2px);
    }

    /* Input fields styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(88, 116, 176, 0.3) !important;
        border-radius: 8px;
    }
    
    /* Sidebar specific fix to ensure it blends in */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 14, 26, 0.85); /* Slightly darker sidebar background */
        border-right: 1px solid rgba(88, 116, 176, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. SUPABASE CONNECTION ---
@st.cache_resource
def init_supabase():
    # Helper to get secrets from EITHER Railway (Env) OR Local (File)
    def get_secret(key):
        if key in os.environ:
            return os.environ[key]
        try:
            return st.secrets[key]
        except:
            return None

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key:
        return None
    return create_client(url, key)
    # --- CORRECT INDENTATION BELOW ---
try:
    supabase = init_supabase()     # This is now indented correctly
except Exception as e:
    supabase = None
    print(f"Supabase init failed: {e}")

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
        
        # --- SELF-HEALING FIX: Update Profile with Email ---
        try:
            user_id = response.user.id
            # Check if profile exists
            profile = supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if not profile.data:
                # Create if missing
                supabase.table("profiles").insert({
                    "id": user_id, 
                    "username": email.split('@')[0], 
                    "email": email
                }).execute()
            else:
                # Update email if it's missing in the database
                if not profile.data[0].get('email'):
                    supabase.table("profiles").update({"email": email}).eq("id", user_id).execute()
        except Exception:
            pass 
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
        
        # --- NEW BLOCK: Save to Profiles Table ---
        if response.user:
            try:
                supabase.table("profiles").insert({
                    "id": response.user.id,
                    "username": username,
                    "email": email  # <--- NOW WE SAVE THE EMAIL
                }).execute()
            except Exception as e:
                print(f"Profile creation error: {e}")
        # -----------------------------------------

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
    # Try getting keys from Environment (Railway) OR Secrets File (Local)
    def get_secret(key):
        if key in os.environ:
            return os.environ[key]
        try:
            return st.secrets[key]
        except:
            return None

    api = get_secret("GEMINI_API_KEY")
    qh = get_secret("QDRANT_HOST")
    qk = get_secret("QDRANT_API_KEY")
    
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
        # Wrap login in a container for glass effect
        with st.container():
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
    
    # Use container for glass effect on metrics
    with st.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("Profile Status", "Active")
        c2.metric("User ID", st.session_state.user_id[:8] + "...")
        c3.metric("System Health", "Online", delta="Connected")
    
    st.divider()

    # Input Area in a container
    with st.container():
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
        # Use container for results area
        with st.container():
            k1, k2, k3 = st.columns(3)
            
            with k1: 
                st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
                st.progress(res['rep'].get('predictive_score', 0)/100)
            with k2:
                st.metric("Tech Depth", f"{res['rep'].get('tech_score')}%")
                st.progress(res['rep'].get('tech_score', 0)/100)
            with k3:
                st.error(f"Weakest Link: {res['rep'].get('weakest_link_skill')}")
                st.caption("Focus your learning here.")

        st.markdown("---")
        
        # Use container for markdown report
        with st.container():
            st.markdown(res['md'])
            
            if res['src']:
                with st.expander("🔗 Verified Sources"):
                    for s in res['src']:
                        st.markdown(f"- [{s['title']}]({s['uri']})")

if __name__ == "__main__":
    main()
