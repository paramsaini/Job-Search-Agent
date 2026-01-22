import streamlit as st
import os
import pypdf
from dotenv import load_dotenv
from agent import JobSearchAgent
from supabase import create_client, Client
from groq import Groq
from fpdf import FPDF

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Aequor Career Agent", page_icon="🚀", layout="wide")

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

# --- 2. HELPER FUNCTIONS ---
def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file is None:
            return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except Exception as e:
        return ""

def create_pdf(text):
    """Safe PDF Generator - Fixes 'bytearray' crash"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=11)
        
        # 1. Sanitize Text
        replacements = {
            '’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-',
            '•': '-', '…': '...', '\u2022': '-' 
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        # 2. Encode to Latin-1
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
        
        # 3. CRITICAL FIX: Convert bytearray to immutable bytes
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
            supabase.table("profiles").insert({"id": res.user.id, "username": username, "email": email}).execute()
        st.success("Account created! Confirm email to login.")
    except Exception as e: st.error(f"Signup failed: {e}")

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# --- 5. APP PAGES ---

def page_cover_letter():
    st.header("✍️ Instant Cover Letter")
    st.caption("Generates a tailored cover letter in seconds.")
    
    c1, c2 = st.columns(2)
    with c1:
        jd_text = st.text_area("Paste Job Description:", height=300)
    with c2:
        uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"], key="cl_uploader")
    
    if st.button("Generate Letter", type="primary"):
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
            return
        if not uploaded_file:
            st.warning("Please upload your CV.")
            return

        try:
            user_cv_text = extract_text(uploaded_file)
            if jd_text and user_cv_text:
                with st.spinner("Writing..."):
                    prompt = f"""
                    You are an expert career coach. Write a professional cover letter.
                    CANDIDATE INFO: {user_cv_text[:4000]} 
                    JOB DESCRIPTION: {jd_text}
                    INSTRUCTIONS:
                    1. Match candidate skills to the job.
                    2. Professional, enthusiastic tone.
                    3. Do not use placeholders like '[Your Name]'.
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
                        st.warning("PDF generation failed. Copy the text manually.")
            else:
                st.warning("Please provide both CV and Job Description.")
        except Exception as e:
            st.error(f"Error: {e}")

def page_cv_tailor():
    st.header("🎯 Smart CV Tailor")
    st.caption("Rewrites your bullet points to match the Job Description keywords.")
    
    jd = st.text_area("Paste Job Description:", height=150)
    uploaded_file = st.file_uploader("Upload your CV (PDF) to optimize", type=["pdf"], key="cv_uploader")
    
    if st.button("Optimize Bullets", type="primary"):
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
            return
        if not uploaded_file:
            st.warning("Please upload a CV.")
            return

        try:
            cv_text = extract_text(uploaded_file)
            if jd and cv_text:
                with st.spinner("Analyzing..."):
                    prompt = f"""
                    Act as an ATS Optimization Expert.
                    JOB DESCRIPTION: {jd}
                    CURRENT CV CONTENT: {cv_text[:4000]}
                    
                    TASK:
                    1. Extract top 5 keywords from the JD.
                    2. Rewrite the CV bullet points to include these keywords naturally.
                    3. Use strong action verbs.
                    4. Output ONLY the rewritten bullet points in Markdown format.
                    """
                    
                    completion = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    
                    optimized = completion.choices[0].message.content
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.info("Original")
                        st.text(cv_text[:1000] + "...") 
                    with c2:
                        st.success("Optimized")
                        st.code(optimized, language='markdown')
                    
                    pdf_bytes = create_pdf(optimized)
                    if pdf_bytes:
                        st.download_button("📥 Download Optimized PDF", pdf_bytes, "optimized_cv.pdf", "application/pdf")
                    else:
                        st.warning("PDF generation failed. Copy text manually.")
            else:
                st.warning("Please paste the Job Description.")
        except Exception as e:
            st.error(f"Error: {e}")

def page_interview_sim():
    st.header("🎤 Voice Interview Simulator")
    st.caption("Speak your answers. AI (Whisper) listens and rates you.")
    
    if 'interview_q' not in st.session_state:
        st.session_state.interview_q = "Tell me about yourself and why you want this role?"
    
    jd_context = st.text_input("Enter Job Role (e.g. 'Senior Python Dev') to generate a specific question:")
    if st.button("Generate New Question"):
        if st.session_state.groq:
            try:
                q_resp = st.session_state.groq.chat.completions.create(
                    messages=[{"role": "user", "content": f"Ask a tough behavioural interview question for a {jd_context}."}],
                    model="llama-3.1-8b-instant"
                )
                st.session_state.interview_q = q_resp.choices[0].message.content
            except Exception as e: st.error(f"Error: {e}")
    
    st.markdown(f"### 🤖 AI asks: *{st.session_state.interview_q}*")
    
    audio_val = st.audio_input("Record your answer")
    
    if audio_val:
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    transcription = st.session_state.groq.audio.transcriptions.create(
                        file=("audio.wav", audio_val, "audio/wav"),
                        model="whisper-large-v3", 
                        response_format="text"
                    )
                    st.info(f"🗣 You said: '{transcription}'")
                    
                    feedback_prompt = f"""
                    Question: {st.session_state.interview_q}
                    Answer: {transcription}
                    Task: Rate answer 1-10. Give 1 pro and 1 con.
                    """
                    
                    feedback = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": feedback_prompt}],
                        model="llama-3.1-8b-instant"
                    )
                    st.success("Feedback:")
                    st.write(feedback.choices[0].message.content)
                except Exception as e:
                    st.error(f"Voice Error: {e}")

# --- 6. MAIN APP ---

def main():
    if not st.session_state.user:
        with st.container():
            c1, c2, c3 = st.columns([1,1,1])
            with c2:
                st.header("Aequor Login")
                mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True)
                email = st.text_input("Email")
                pwd = st.text_input("Password", type="password")
                if mode == "Sign Up":
                    user = st.text_input("Username")
                    if st.button("Sign Up"): signup(email, pwd, user)
                else:
                    if st.button("Login"): login(email, pwd)
        return

    with st.sidebar:
        st.subheader(f"User: {st.session_state.user.split('@')[0]}")
        nav = st.radio("Menu", [
            "Dashboard", 
            "Smart CV Tailor", 
            "Instant Cover Letter", 
            "Voice Interview Sim"
        ])
        st.divider()
        if st.button("Logout"): logout()

    if nav == "Smart CV Tailor": page_cv_tailor()
    elif nav == "Instant Cover Letter": page_cover_letter()
    elif nav == "Voice Interview Sim": page_interview_sim()
    elif nav == "Dashboard":
        st.title("🚀 Career Strategy Dashboard")
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
            with st.container():
                st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
                st.markdown(res['md'])

if __name__ == "__main__":
    main()
