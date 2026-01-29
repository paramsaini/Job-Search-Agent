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

# --- HELPER: CONSISTENT HEADER ---
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
    """Safe PDF Generator - Fixes White Screen Crash"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=11)
        
        # 1. Sanitize Text (Replace crash-prone characters)
        replacements = {
            '’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-',
            '•': '-', '…': '...', '\u2022': '-' 
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        # 2. Encode to Latin-1
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
        
        # 3. CRITICAL FIX: Explicitly convert to bytes
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
        # Self-Healing
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
        if res.user:
            try:
                existing = supabase.table("profiles").select("id").eq("id", res.user.id).execute()
                if not existing.data:
                    supabase.table("profiles").insert({"id": res.user.id, "username": username, "email": email}).execute()
            except:
                pass
        st.success("Account created! Check your email to confirm, then login.")
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            st.warning("This email is already registered. Please login instead.")
        else:
            st.error(f"Signup failed: {e}")

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

def delete_user_account():
    if not st.session_state.user_id:
        return False, "Not authenticated"
    user_id = st.session_state.user_id
    service_key = get_secret("SUPABASE_SERVICE_KEY")
    supabase_url = get_secret("SUPABASE_URL")
    if not service_key or not supabase_url:
        return False, "Server configuration error. Please contact support."
    try:
        from supabase import create_client
        admin_client = create_client(supabase_url, service_key)
        try: admin_client.table("mood_logs").delete().eq("user_id", user_id).execute()
        except: pass
        try: admin_client.table("analyses").delete().eq("user_id", user_id).execute()
        except: pass
        try: admin_client.table("applications").delete().eq("user_id", user_id).execute()
        except: pass
        try: admin_client.table("profiles").delete().eq("id", user_id).execute()
        except: pass
        try: admin_client.auth.admin.delete_user(user_id)
        except Exception as e: return False, f"Failed to delete authentication: {e}"
        try: supabase.auth.sign_out()
        except: pass
        return True, "Account and all data permanently deleted"
    except Exception as e:
        return False, f"Error deleting account: {e}"

def page_delete_account():
    st.header("🗑️ Delete Account")
    st.markdown("""
    <div style="background: rgba(220, 38, 38, 0.1); border: 1px solid #dc2626; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
        <h3 style="color: #dc2626 !important; margin-top: 0;">⚠️ Warning: This action is permanent</h3>
        <p style="color: #fca5a5 !important;">Deleting your account will remove all personal data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.show_delete_confirmation:
        if st.button("🗑️ I want to delete my account", type="primary", use_container_width=True):
            st.session_state.show_delete_confirmation = True
            st.rerun()
    else:
        st.warning("Are you absolutely sure?")
        confirm_text = st.text_input("Type 'DELETE' to confirm:", placeholder="Type DELETE here", key="delete_confirm_input")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_delete_confirmation = False
                st.rerun()
        with col2:
            delete_disabled = confirm_text.upper() != "DELETE"
            if st.button("🗑️ Permanently Delete", type="primary", use_container_width=True, disabled=delete_disabled):
                if confirm_text.upper() == "DELETE":
                    with st.spinner("Deleting your account..."):
                        success, message = delete_user_account()
                        if success:
                            st.success("✅ Your account has been deleted.")
                            for key in list(st.session_state.keys()): del st.session_state[key]
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

def page_cover_letter():
    st.header("✍️ Instant Cover Letter")
    c1, c2 = st.columns(2)
    with c1: jd_text = st.text_area("Paste Job Description:", height=300)
    with c2: uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"], key="cl_uploader")
    if st.button("Generate Letter", type="primary"):
        if not st.session_state.groq: return st.error("Groq API Key missing.")
        if not uploaded_file: return st.warning("Please upload your CV.")
        try:
            user_cv_text = extract_text(uploaded_file)
            if jd_text and user_cv_text:
                with st.spinner("Writing..."):
                    prompt = f"""
                    You are an expert career coach. Write a professional cover letter.
                    CANDIDATE INFO: {user_cv_text[:4000]} 
                    JOB DESCRIPTION: {jd_text}
                    INSTRUCTIONS: Match skills to job. Professional tone. No placeholders.
                    """
                    completion = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile" 
                    )
                    letter = completion.choices[0].message.content
                    st.subheader("Draft:")
                    st.write(letter)
                    pdf_bytes = create_pdf(letter)
                    if pdf_bytes:
                        st.download_button("📥 Download PDF", pdf_bytes, "cover_letter.pdf", "application/pdf")
                    else:
                        st.download_button("📥 Download Text (Fallback)", letter, "cover_letter.txt", "text/plain")
            else: st.warning("Please provide both CV and Job Description.")
        except Exception as e: st.error(f"Error: {e}")

def page_interview_sim():
    st.header("🎤 Voice Interview Simulator")
    if 'interview_q' not in st.session_state:
        st.session_state.interview_q = "Tell me about yourself?"
    jd_context = st.text_input("Enter Job Role (e.g. 'Senior Python Dev'):")
    if st.button("Generate Question"):
        if st.session_state.groq:
            try:
                q_resp = st.session_state.groq.chat.completions.create(
                    messages=[{"role": "user", "content": f"Ask a tough behavioural question for {jd_context}."}],
                    model="llama-3.1-8b-instant"
                )
                st.session_state.interview_q = q_resp.choices[0].message.content
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    st.markdown(f"### 🤖 AI asks: *{st.session_state.interview_q}*")
    audio_val = st.audio_input("Record your answer")
    if audio_val:
        if not st.session_state.groq: st.error("Groq API Key missing.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    transcription = st.session_state.groq.audio.transcriptions.create(
                        file=("audio.wav", audio_val, "audio/wav"),
                        model="whisper-large-v3", 
                        response_format="text"
                    )
                    st.info(f"🗣 You said: '{transcription}'")
                    feedback = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": f"Rate this interview answer 1-10: '{transcription}' for question '{st.session_state.interview_q}'"}],
                        model="llama-3.1-8b-instant"
                    )
                    st.success("Feedback:")
                    st.write(feedback.choices[0].message.content)
                except Exception as e: st.error(f"Error: {e}")

# --- 6. MAIN APP ---
def main():
    if not st.session_state.user:
        # LOGO FOR LOGIN SCREEN
        render_header()
        
        with st.container():
            c1, c2, c3 = st.columns([1,1,1])
            with c2:
                # Login/Signup Logic (truncated for brevity - use original logic)
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
                    if st.button("🔑 Forgot Password?", type="secondary", use_container_width=True):
                        st.session_state.show_forgot_password = True
                        st.rerun()
        return

    # LOGGED IN VIEW
    with st.sidebar:
        st.subheader(f"User: {st.session_state.user.split('@')[0]}")
        st.markdown("### 📱 Navigation")
        
        # Internal tools (same page)
        nav = st.radio("Dashboard Tools", [
            "Home Strategy", 
            "Instant Cover Letter", 
            "Voice Interview Sim",
            "⚙️ Account Settings"
        ])
        
        st.markdown("---")
        st.markdown("### 🚀 Advanced Tools")
        
        # External Pages (Switch Page)
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

    # RENDER HEADER ON MAIN PAGE
    render_header()

    if nav == "Home Strategy":
        st.title("🎯 Career Strategy Dashboard")
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
                            
                            if supabase and st.session_state.user_id:
                                try:
                                    supabase.table("analyses").insert({
                                        "user_id": st.session_state.user_id,
                                        "report_json": rep
                                    }).execute()
                                except: pass
                            st.rerun()

        if "results" in st.session_state:
            res = st.session_state.results
            with st.container():
                st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
                st.markdown(res['md'])
                
    elif nav == "Instant Cover Letter": page_cover_letter()
    elif nav == "Voice Interview Sim": page_interview_sim()
    elif nav == "⚙️ Account Settings": page_delete_account()

if __name__ == "__main__":
    main()
