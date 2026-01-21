import streamlit as st
import os
import pypdf
from dotenv import load_dotenv
from agent import JobSearchAgent
from supabase import create_client, Client
from groq import Groq
from fpdf import FPDF

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Job-Search-Agent", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
        background-attachment: fixed;
        color: #e2e8f0;
    }

    /* Glassmorphism Containers */
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

    /* Typography & Metrics */
    h1, h2, h3, p, label, .stMarkdown { color: #e2e8f0 !important; }
    div[data-testid="stMetricValue"] { color: #00e0ff !important; text-shadow: 0 0 10px rgba(0, 224, 255, 0.6); }
    
    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(88, 116, 176, 0.3) !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #0062ff, #00c6ff);
        color: white !important;
        border: none;
        box-shadow: 0 0 10px rgba(0, 98, 255, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. HELPER FUNCTIONS (Moved to top for global access) ---
def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def create_pdf(text):
    """Helper to convert text to PDF bytes"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Encode to latin-1 to handle standard characters, replacing unknown ones
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest='S').encode('latin-1')

def get_secret(key):
    if key in os.environ: return os.environ[key]
    try: return st.secrets[key]
    except: return None

# --- 3. INITIALIZATION (SUPABASE, AGENT, GROQ) ---

# A. Supabase
@st.cache_resource
def init_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    supabase = None

# B. Gemini Agent (For Job Search)
if 'agent' not in st.session_state:
    api = get_secret("GEMINI_API_KEY")
    qh = get_secret("QDRANT_HOST")
    qk = get_secret("QDRANT_API_KEY")
    if api and qh:
        st.session_state.agent = JobSearchAgent(api, qh, qk)
    else:
        st.session_state.agent = None

# C. Groq Client (For Open Source Features)
if 'groq' not in st.session_state:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key:
        st.session_state.groq = Groq(api_key=groq_key)
    else:
        st.session_state.groq = None

# --- 4. AUTHENTICATION LOGIC ---
if 'user' not in st.session_state: st.session_state.user = None
if 'user_id' not in st.session_state: st.session_state.user_id = None

def login(email, password):
    if not supabase: return st.error("Database error.")
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user.email
        st.session_state.user_id = res.user.id
        
        # Self-Healing Profile Check
        try:
            pid = res.user.id
            prof = supabase.table("profiles").select("*").eq("id", pid).execute()
            if not prof.data:
                supabase.table("profiles").insert({"id": pid, "username": email.split('@')[0], "email": email}).execute()
        except: pass
        st.rerun()
    except Exception as e: st.error(f"Login failed: {e}")

def signup(email, password, username):
    if not supabase: return
    try:
        res = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"username": username}}})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "username": username, "email": email}).execute()
        st.success("Account created! Confirm email to login.")
    except Exception as e: st.error(f"Signup failed: {e}")

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 5. NEW FEATURE FUNCTIONS (UPDATED WITH FILE UPLOAD) ---

def page_cover_letter():
    st.header("✍️ Instant Cover Letter")
    st.caption("Generates a tailored cover letter in seconds using Open Source AI.")
    
    c1, c2 = st.columns(2)
    with c1:
        jd_text = st.text_area("Paste Job Description:", height=300)
    with c2:
        # UPDATED: File Uploader instead of Text Area
        uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"], key="cl_uploader")
    
    if st.button("Generate Letter", type="primary"):
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
            return

        # Extract text from uploaded file
        user_cv_text = ""
        if uploaded_file:
            user_cv_text = extract_text(uploaded_file)

        if jd_text and user_cv_text:
            with st.spinner("Llama 3 (70B) is reading your PDF & writing..."):
                prompt = f"""
                You are an expert career coach. Write a professional cover letter.
                
                CANDIDATE INFO (Extracted from PDF): {user_cv_text[:3000]} 
                JOB DESCRIPTION: {jd_text}
                
                INSTRUCTIONS:
                1. Match candidate skills to the job requirements.
                2. Professional, enthusiastic tone.
                3. Do not use placeholders like '[Your Name]' - use 'The Applicant' if name is missing.
                """
                
                completion = st.session_state.groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-70b-8192"
                )
                
                letter = completion.choices[0].message.content
                st.subheader("Draft:")
                st.write(letter)
                
                st.download_button(
                    label="📥 Download PDF",
                    data=create_pdf(letter),
                    file_name="cover_letter.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Please upload your CV and paste the Job Description.")

def page_cv_tailor():
    st.header("🎯 Smart CV Tailor (ATS Optimized)")
    st.caption("Rewrites your bullet points to match the Job Description keywords.")
    
    jd = st.text_area("Paste Job Description:", height=150)
    
    # UPDATED: File Uploader instead of Text Area
    uploaded_file = st.file_uploader("Upload your CV (PDF) to optimize", type=["pdf"], key="cv_uploader")
    
    if st.button("Optimize Bullets", type="primary"):
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
            return

        # Extract text from uploaded file
        cv_text = ""
        if uploaded_file:
            cv_text = extract_text(uploaded_file)

        if jd and cv_text:
            with st.spinner("Analyzing keywords & rewriting..."):
                prompt = f"""
                Act as an ATS Optimization Expert.
                JOB DESCRIPTION: {jd}
                CURRENT CV CONTENT: {cv_text[:3000]}
                
                TASK:
                1. Extract top 5 keywords from the JD.
                2. Rewrite the CV bullet points to naturally include these keywords.
                3. Use strong action verbs.
                4. Output ONLY the rewritten bullet points in Markdown.
                """
                
                completion = st.session_state.groq.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-70b-8192"
                )
                
                optimized = completion.choices[0].message.content
                
                c1, c2 = st.columns(2)
                with c1:
                    st.info("Original (Extracted)")
                    st.text(cv_text[:1000] + "...") # Show preview of extracted text
                with c2:
                    st.success("Optimized Version")
                    st.code(optimized, language='markdown')
                
                st.download_button(
                    label="📥 Download Optimized Text",
                    data=create_pdf(optimized),
                    file_name="optimized_cv.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("Please upload your CV and paste the Job Description.")

def page_interview_sim():
    st.header("🎤 Voice Interview Simulator")
    st.caption("Speak your answers. AI (Whisper) listens and rates you.")
    
    # Session State for Question
    if 'interview_q' not in st.session_state:
        st.session_state.interview_q = "Tell me about yourself and why you want this role?"
    
    # 1. Generate New Question
    jd_context = st.text_input("Enter Job Role (e.g. 'Senior Python Dev') to generate a specific question:")
    if st.button("Generate New Question"):
        if st.session_state.groq:
            q_resp = st.session_state.groq.chat.completions.create(
                messages=[{"role": "user", "content": f"Ask a tough behavioural interview question for a {jd_context}."}],
                model="llama3-8b-8192"
            )
            st.session_state.interview_q = q_resp.choices[0].message.content
    
    st.markdown(f"### 🤖 AI asks: *{st.session_state.interview_q}*")
    
    # 2. Record Answer
    audio_val = st.audio_input("Record your answer")
    
    if audio_val:
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
        else:
            with st.spinner("Transcribing & Analyzing..."):
                # A. Transcribe (Whisper)
                transcription = st.session_state.groq.audio.transcriptions.create(
                    file=("audio.wav", audio_val, "audio/wav"),
                    model="distil-whisper-large-v3-en-main",
                    response_format="text"
                )
                
                st.info(f"🗣 You said: '{transcription}'")
                
                # B. Analyze (Llama 3)
                feedback_prompt = f"""
                Question: {st.session_state.interview_q}
                Answer: {transcription}
                
                Task: Rate answer 1-10. Give 1 pro and 1 con.
                """
                
                feedback = st.session_state.groq.chat.completions.create(
                    messages=[{"role": "user", "content": feedback_prompt}],
                    model="llama3-8b-8192"
                )
                
                st.success("Feedback:")
                st.write(feedback.choices[0].message.content)

# --- 6. MAIN APP ---

def main():
    # A. Login Screen
    if not st.session_state.user:
        with st.container():
            c1, c2, c3 = st.columns([1,1,1])
            with c2:
                st.header("Job-Search-Agent Login")
                mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True)
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                if mode == "Sign Up":
                    user = st.text_input("Username")
                    if st.button("Sign Up"): signup(email, pwd, user)
                else:
                    if st.button("Login"): login(email, pwd)
        return

    # B. Sidebar Navigation
    with st.sidebar:
        st.subheader(f"User: {st.session_state.user.split('@')[0]}")
        nav = st.radio("Menu", [
            "Dashboard", 
            "Smart CV Tailor", 
            "Instant Cover Letter", 
            "Voice Interview Sim",
            "Emotional Tracker"
        ])
        st.divider()
        if st.button("Logout"): logout()

    # C. Routing
    if nav == "Smart CV Tailor":
        page_cv_tailor()
    elif nav == "Instant Cover Letter":
        page_cover_letter()
    elif nav == "Voice Interview Sim":
        page_interview_sim()
    elif nav == "Emotional Tracker":
        try:
            st.switch_page("pages/1_Emotional_Tracker.py")
        except:
            st.info("Emotional Tracker module not found in this version.")
    
    elif nav == "Dashboard":
        # Original Dashboard Logic
        st.title("🚀 Career Strategy Dashboard")
        
        with st.container():
            c1, c2 = st.columns([2,1])
            with c1:
                role = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering"])
                # File uploader logic already exists here for the dashboard
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
            with st.container():
                st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
                st.markdown(res['md'])

if __name__ == "__main__":
    main()
