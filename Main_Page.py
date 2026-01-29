import streamlit as st
import os
import pypdf
import json
import pandas as pd
from dotenv import load_dotenv
from agent import JobSearchAgent
from supabase import create_client, Client
from groq import Groq
from fpdf import FPDF

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Job-Search-Agent Career Agent", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
        background-attachment: fixed;
        color: #e2e8f0;
    }
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"],
    div[data-testid="stExpanderDetails"],
    div[data-testid="stForm"],
    [data-testid="stSidebar"] > div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(88, 116, 176, 0.2) !important;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        padding: 15px;
    }
    h1, h2, h3, p, label, .stMarkdown { color: #e2e8f0 !important; }
    div[data-testid="stMetricValue"] { color: #00e0ff !important; text-shadow: 0 0 10px rgba(0, 224, 255, 0.6); }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(88, 116, 176, 0.3) !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #0062ff, #00c6ff);
        color: white !important;
        border: none;
        box-shadow: 0 0 10px rgba(0, 98, 255, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- HELPER: CONSISTENT LOGO ---
def render_header():
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #FF8C00; margin-bottom: 0;">🚀 Job-Search-Agent</h1>
        <p style="color: #e2e8f0; font-size: 1.2rem; margin-top: 5px;">AI-Powered Career Guidance</p>
        <hr style="border-color: rgba(255, 140, 0, 0.3);">
    </div>
    """, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def create_pdf(text):
    """Safe PDF Generator"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=11)
        replacements = {
            '’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-',
            '•': '-', '…': '...', '\u2022': '-' 
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
        return bytes(pdf.output())
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return None

def get_secret(key):
    if key in os.environ: return os.environ[key]
    try: return st.secrets[key]
    except: return None

# --- 3. INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

try: supabase = init_supabase()
except: supabase = None

if 'agent' not in st.session_state:
    api = get_secret("GEMINI_API_KEY")
    qh = get_secret("QDRANT_HOST")
    qk = get_secret("QDRANT_API_KEY")
    if api and qh: st.session_state.agent = JobSearchAgent(api, qh, qk)
    else: st.session_state.agent = None

if 'groq' not in st.session_state:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key: st.session_state.groq = Groq(api_key=groq_key)
    else: st.session_state.groq = None

# --- 4. AUTH & LOGIC ---
if 'user' not in st.session_state: st.session_state.user = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'show_delete_confirmation' not in st.session_state: st.session_state.show_delete_confirmation = False
if 'show_forgot_password' not in st.session_state: st.session_state.show_forgot_password = False
if 'password_reset_mode' not in st.session_state: st.session_state.password_reset_mode = False

def login(email, password):
    if not supabase: return st.error("Database error.")
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user.email
        st.session_state.user_id = res.user.id
        try:
            pid = res.user.id
            prof = supabase.table("profiles").select("*").eq("id", pid).execute()
            if not prof.data:
                supabase.table("profiles").insert({"id": pid, "username": email.split('@')[0], "email": email}).execute()
            elif not prof.data[0].get('email'):
                supabase.table("profiles").update({"email": email}).eq("id", pid).execute()
        except: pass
        st.rerun()
    except Exception as e: st.error(f"Login failed: {e}")

def signup(email, password, username):
    if not supabase: return
    try:
        res = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"username": username}}})
        st.success("Account created! Check your email to confirm, then login.")
    except Exception as e:
        if "already registered" in str(e).lower():
            st.warning("This email is already registered. Please login instead.")
        else:
            st.error(f"Signup failed: {e}")

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- ACCOUNT DELETION LOGIC ---
def delete_user_account():
    if not st.session_state.user_id: return False, "Not authenticated"
    user_id = st.session_state.user_id
    service_key = get_secret("SUPABASE_SERVICE_KEY")
    supabase_url = get_secret("SUPABASE_URL")
    if not service_key or not supabase_url: return False, "Server configuration error."
    try:
        from supabase import create_client
        admin_client = create_client(supabase_url, service_key)
        admin_client.table("mood_logs").delete().eq("user_id", user_id).execute()
        admin_client.table("analyses").delete().eq("user_id", user_id).execute()
        admin_client.table("applications").delete().eq("user_id", user_id).execute()
        admin_client.table("profiles").delete().eq("id", user_id).execute()
        admin_client.auth.admin.delete_user(user_id)
        supabase.auth.sign_out()
        return True, "Account deleted"
    except Exception as e: return False, str(e)

def page_delete_account():
    st.header("🗑️ Delete Account")
    st.warning("Warning: This action is permanent and will remove all your data.")
    if not st.session_state.show_delete_confirmation:
        if st.button("🗑️ I want to delete my account", type="primary"):
            st.session_state.show_delete_confirmation = True
            st.rerun()
    else:
        st.error("Are you absolutely sure?")
        confirm_text = st.text_input("Type 'DELETE' to confirm:", key="del_conf")
        c1, c2 = st.columns(2)
        if c1.button("❌ Cancel"):
            st.session_state.show_delete_confirmation = False
            st.rerun()
        if c2.button("Confirm Delete", disabled=(confirm_text != "DELETE")):
            success, msg = delete_user_account()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

# --- INTERNAL PAGES (Cover Letter & Interview Sim) ---
def page_cover_letter():
    st.header("✍️ Instant Cover Letter")
    c1, c2 = st.columns(2)
    with c1: jd_text = st.text_area("Paste Job Description:", height=300)
    with c2: uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"])
    if st.button("Generate Letter", type="primary"):
        if not st.session_state.groq: return st.error("Groq API Key missing.")
        if not uploaded_file: return st.warning("Please upload your CV.")
        try:
            user_cv_text = extract_text(uploaded_file)
            if jd_text and user_cv_text:
                with st.spinner("Writing..."):
                    prompt = f"Write a professional cover letter. CV: {user_cv_text[:3000]} Job: {jd_text}"
                    completion = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    letter = completion.choices[0].message.content
                    st.write(letter)
                    pdf_bytes = create_pdf(letter)
                    if pdf_bytes: st.download_button("Download PDF", pdf_bytes, "cover_letter.pdf", "application/pdf")
        except Exception as e: st.error(f"Error: {e}")

def page_interview_sim():
    st.header("🎤 Voice Interview Simulator")
    if 'interview_q' not in st.session_state: st.session_state.interview_q = "Tell me about yourself?"
    jd_context = st.text_input("Enter Job Role (e.g. 'Senior Python Dev'):")
    if st.button("Generate Question"):
        if st.session_state.groq:
            q_resp = st.session_state.groq.chat.completions.create(
                messages=[{"role": "user", "content": f"Ask a tough behavioural question for {jd_context}."}],
                model="llama-3.1-8b-instant"
            )
            st.session_state.interview_q = q_resp.choices[0].message.content
            st.rerun()
    st.markdown(f"### 🤖 AI asks: *{st.session_state.interview_q}*")
    audio_val = st.audio_input("Record your answer")
    if audio_val and st.session_state.groq:
        with st.spinner("Analyzing..."):
            transcription = st.session_state.groq.audio.transcriptions.create(
                file=("audio.wav", audio_val, "audio/wav"), model="whisper-large-v3", response_format="text"
            )
            st.info(f"You said: {transcription}")
            feedback = st.session_state.groq.chat.completions.create(
                messages=[{"role": "user", "content": f"Rate answer: '{transcription}' for question '{st.session_state.interview_q}'"}],
                model="llama-3.1-8b-instant"
            )
            st.success("Feedback:")
            st.write(feedback.choices[0].message.content)

# --- 6. MAIN APP ---
def main():
    # Only show the centered logo on the Login screen
    if not st.session_state.user:
        render_header()
        c1, c2, c3 = st.columns([1,1,1])
        with c2:
            st.header("Login")
            mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True)
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            if mode == "Sign Up":
                user = st.text_input("Username")
                if st.button("Sign Up"): signup(email, pwd, user)
            else:
                if st.button("Login"): login(email, pwd)
                st.markdown("---")
                if st.button("🔑 Forgot Password?", type="secondary"): 
                    st.switch_page("Reset_Password.py") # Assuming you have this file or logic
        return

    # Authenticated View
    with st.sidebar:
        st.subheader(f"User: {st.session_state.user.split('@')[0]}")
        
        # Navigation
        st.markdown("### 📱 Navigation")
        
        # Internal Dashboard Tabs
        nav_internal = st.radio("Dashboard Tools", [
            "Home Strategy", 
            "Instant Cover Letter", 
            "Voice Interview Sim",
            "⚙️ Account Settings"
        ])
        
        st.markdown("---")
        st.markdown("### 🚀 Advanced Tools")
        
        # External Pages Linked via Buttons (acting as separate pages)
        if st.button("📈 Skill Migration Map", use_container_width=True):
            st.switch_page("3_Skill_Migration.py")
        
        if st.button("🔄 Feedback Loop", use_container_width=True):
            st.switch_page("2_Feedback_Loop.py")
            
        if st.button("🧘 Emotional Tracker", use_container_width=True):
            st.switch_page("1_Emotional_Tracker.py")
            
        if st.button("🤖 CV Compiler", use_container_width=True):
            st.switch_page("4_CV_Compiler.py")
            
        st.markdown("---")
        if st.button("💬 Support Center", use_container_width=True):
            st.switch_page("Support.py")

        st.divider()
        if st.button("Logout"): logout()

    # RENDER SELECTED INTERNAL PAGE
    # Consistent Header on all Dashboard pages
    render_header()
    
    if nav_internal == "Home Strategy":
        st.subheader("🎯 Career Strategy Dashboard")
        with st.container():
            c1, c2 = st.columns([2,1])
            with c1:
                role = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering"])
                f = st.file_uploader("Upload CV for Strategy", type=["pdf", "txt"])
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Generate Strategy", type="primary"):
                    if f and st.session_state.agent:
                        with st.spinner("Agent working..."):
                            txt = extract_text(f)
                            md, rep, src = st.session_state.agent.generate_strategy(txt, role)
                            st.session_state.results = {"md": md, "rep": rep, "src": src}
                            st.rerun()

        if "results" in st.session_state:
            res = st.session_state.results
            st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
            st.markdown(res['md'])

    elif nav_internal == "Instant Cover Letter":
        page_cover_letter()
    elif nav_internal == "Voice Interview Sim":
        page_interview_sim()
    elif nav_internal == "⚙️ Account Settings":
        page_delete_account()

if __name__ == "__main__":
    main()
