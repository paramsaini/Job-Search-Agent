import streamlit as st
import os
import pypdf
import json
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
    /* Delete Account Button Styling */
    .delete-btn button {
        background: linear-gradient(90deg, #dc2626, #ef4444) !important;
        box-shadow: 0 0 10px rgba(220, 38, 38, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

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
            ''': "'", ''': "'", '"': '"', '"': '"', '–': '-', '—': '-',
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
            # Try to insert profile, but handle if it already exists
            try:
                supabase.table("profiles").insert({"id": res.user.id, "username": username, "email": email}).execute()
            except Exception as profile_error:
                # Profile might already exist, try to update instead
                try:
                    supabase.table("profiles").upsert({"id": res.user.id, "username": username, "email": email}).execute()
                except:
                    pass  # Profile creation is optional, user can still login
        st.success("Account created! Confirm email to login.")
    except Exception as e: 
        error_msg = str(e)
        if "User already registered" in error_msg:
            st.error("This email is already registered. Please login instead.")
        else:
            st.error(f"Signup failed: {e}")

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

def delete_user_account():
    """
    PERMANENTLY deletes user account and ALL associated data from Supabase.
    This includes: analyses, applications, mood_logs, profiles, AND auth.users
    Required for Apple App Store Guideline 5.1.1(v) compliance.
    """
    if not st.session_state.user_id:
        return False, "Not authenticated"
    
    user_id = st.session_state.user_id
    
    # Get service role key for admin operations (REQUIRED for auth deletion)
    service_key = get_secret("SUPABASE_SERVICE_KEY")
    supabase_url = get_secret("SUPABASE_URL")
    
    if not service_key or not supabase_url:
        return False, "Server configuration error. Please contact support."
    
    try:
        # Create admin client with service_role key (has full database access)
        from supabase import create_client
        admin_client = create_client(supabase_url, service_key)
        
        # ========================================
        # STEP 1: Delete ALL user data from tables
        # ========================================
        
        # Delete from mood_logs
        try:
            admin_client.table("mood_logs").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"mood_logs deletion: {e}")
        
        # Delete from analyses
        try:
            admin_client.table("analyses").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"analyses deletion: {e}")
        
        # Delete from applications
        try:
            admin_client.table("applications").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"applications deletion: {e}")
        
        # Delete from profiles (MUST be before auth.users due to foreign key)
        try:
            admin_client.table("profiles").delete().eq("id", user_id).execute()
        except Exception as e:
            print(f"profiles deletion: {e}")
        
        # ========================================
        # STEP 2: Delete from Supabase Authentication
        # ========================================
        try:
            admin_client.auth.admin.delete_user(user_id)
        except Exception as e:
            print(f"auth deletion: {e}")
            return False, f"Failed to delete authentication: {e}"
        
        # ========================================
        # STEP 3: Sign out current session
        # ========================================
        try:
            supabase.auth.sign_out()
        except:
            pass
        
        return True, "Account and all data permanently deleted"
        
    except Exception as e:
        return False, f"Error deleting account: {e}"

# --- 5. APP PAGES ---

def page_delete_account():
    """Account Deletion Page - Required for Apple App Store compliance"""
    st.header("🗑️ Delete Account")
    
    st.markdown("""
    <div style="background: rgba(220, 38, 38, 0.1); border: 1px solid #dc2626; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
        <h3 style="color: #dc2626 !important; margin-top: 0;">⚠️ Warning: This action is permanent</h3>
        <p style="color: #fca5a5 !important;">Deleting your account will:</p>
        <ul style="color: #fca5a5 !important;">
            <li>Permanently delete all your personal data</li>
            <li>Remove all your saved analyses and reports</li>
            <li>Delete your application history and tracking data</li>
            <li>Remove all mood logs and emotional tracking data</li>
            <li>This action <strong>cannot be undone</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show current user info
    st.markdown(f"**Account to be deleted:** `{st.session_state.user}`")
    
    st.markdown("---")
    
    # Confirmation flow
    if not st.session_state.show_delete_confirmation:
        st.markdown("To proceed with account deletion, click the button below:")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ I want to delete my account", type="primary", use_container_width=True):
                st.session_state.show_delete_confirmation = True
                st.rerun()
    else:
        # Second confirmation step
        st.markdown("""
        <div style="background: rgba(220, 38, 38, 0.2); border: 2px solid #dc2626; border-radius: 10px; padding: 20px; text-align: center;">
            <h3 style="color: #dc2626 !important;">🚨 Final Confirmation Required</h3>
            <p style="color: white !important;">Are you absolutely sure? This will permanently delete your account and all data.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Type confirmation
        confirm_text = st.text_input(
            "Type 'DELETE' to confirm:",
            placeholder="Type DELETE here",
            key="delete_confirm_input"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_delete_confirmation = False
                st.rerun()
        
        with col2:
            delete_disabled = confirm_text.upper() != "DELETE"
            
            if st.button(
                "🗑️ Permanently Delete Account", 
                type="primary", 
                use_container_width=True,
                disabled=delete_disabled
            ):
                if confirm_text.upper() == "DELETE":
                    with st.spinner("Deleting your account..."):
                        success, message = delete_user_account()
                        
                        if success:
                            st.success("✅ Your account has been deleted.")
                            st.info("You will be redirected to the login page...")
                            # Clear all session state and redirect
                            for key in list(st.session_state.keys()): 
                                del st.session_state[key]
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            st.info("Please try again or contact support.")

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

import re
import numpy as np
import pandas as pd

# --- CV Compiler Helper Functions ---
def calculate_ats_compliance(cv_text, jd_text):
    """Calculate ATS keyword match percentage"""
    if not cv_text or not jd_text: return 0
    cv_words = set(re.findall(r'\b\w{3,}\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w{3,}\b', jd_text.lower()))
    intersection = len(cv_words.intersection(jd_words))
    union = len(cv_words.union(jd_words))
    score = (intersection / union) * 100 if union > 0 else 0
    return int(np.clip(score, 0, 100))

def calculate_human_clarity(text):
    """Calculate readability/clarity score"""
    if not text: return 0
    metric_count = len(re.findall(r'\d[\d,\.]*', text))
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_words = len(re.findall(r'\b\w+\b', text))
    avg_words = total_words / len(sentences) if sentences else 0
    clarity = 50
    if 0 < avg_words < 15:
        clarity += (15 - avg_words) * 1.0
    clarity += min(30, metric_count * 5)
    return int(np.clip(clarity, 40, 100))

def fetch_application_ledger(user_id):
    """Fetch user's application history"""
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("applications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "created_at": "Date", "company_name": "Company", "job_id": "JobID",
                "compliance_score": "Compliance", "clarity_score": "Clarity", "outcome": "Outcome"
            })
            return df
    except: pass
    return pd.DataFrame()

def save_application(user_id, company, job_id, comp, clar):
    """Save application to database"""
    if not supabase: return False
    try:
        supabase.table("applications").insert({
            "user_id": user_id, "company_name": company, "job_id": job_id,
            "compliance_score": comp, "clarity_score": clar, "outcome": "Pending"
        }).execute()
        return True
    except: return False

def update_application_status(app_id, new_status):
    """Update application outcome"""
    if not supabase: return
    try:
        supabase.table("applications").update({"outcome": new_status}).eq("id", app_id).execute()
    except: pass

# --- CV Compiler Page ---
def page_cv_compiler():
    st.header("🤖 CV Compiler & Optimizer")
    st.caption("All-in-one: Optimize your CV, check ATS compliance, and track applications")
    
    # --- SECTION 1: Smart CV Tailor ---
    st.subheader("1️⃣ Smart CV Tailor")
    
    col_upload, col_jd = st.columns(2)
    with col_upload:
        uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"], key="compiler_cv_upload")
    with col_jd:
        jd_text = st.text_area("Paste Job Description:", height=150, key="compiler_jd")
    
    # Extract CV text
    cv_text = ""
    if uploaded_file:
        cv_text = extract_text(uploaded_file)
        st.session_state['compiler_cv_text'] = cv_text
    elif 'compiler_cv_text' in st.session_state:
        cv_text = st.session_state['compiler_cv_text']
    
    if st.button("🚀 Optimize Bullets", type="primary", use_container_width=True):
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
        elif not cv_text or cv_text.strip() == "":
            st.warning("Please upload a CV.")
        elif not jd_text or jd_text.strip() == "":
            st.warning("Please paste the Job Description.")
        else:
            try:
                with st.spinner("AI is optimizing your CV..."):
                    prompt = f"""
                    Act as an ATS Optimization Expert.
                    JOB DESCRIPTION: {jd_text}
                    CURRENT CV: {cv_text[:4000]}
                    TASK: Rewrite bullets to include JD keywords. Output ONLY bullets in Markdown.
                    """
                    completion = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    if completion and completion.choices:
                        optimized = completion.choices[0].message.content
                        if optimized and optimized.strip():
                            st.session_state['compiler_optimized'] = optimized
                            st.session_state['compiler_original'] = cv_text[:1000]
                            st.session_state['compiler_jd_stored'] = jd_text
                        else:
                            st.error("Empty response from AI.")
                    else:
                        st.error("No response received.")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display optimization results
    if 'compiler_optimized' in st.session_state:
        st.markdown("---")
        col_orig, col_opt = st.columns(2)
        with col_orig:
            st.info("📄 Original CV Preview")
            st.text(st.session_state.get('compiler_original', '')[:800] + "...")
        with col_opt:
            st.success("✨ Optimized Bullets")
            st.code(st.session_state['compiler_optimized'], language='markdown')
        
        # Download buttons
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            try:
                pdf_bytes = create_pdf(st.session_state['compiler_optimized'])
                if pdf_bytes:
                    st.download_button("📥 Download Optimized PDF", pdf_bytes, "optimized_cv.pdf", "application/pdf", use_container_width=True)
            except:
                pass
        with col_dl2:
            st.download_button("📥 Download as Text", st.session_state['compiler_optimized'], "optimized_cv.txt", "text/plain", use_container_width=True)
    
    # --- SECTION 2: Dual Optimization Dashboard ---
    st.markdown("---")
    st.subheader("2️⃣ Dual Optimization Dashboard")
    
    # Use stored JD if available, otherwise use current input
    jd_for_analysis = st.session_state.get('compiler_jd_stored', jd_text)
    
    if cv_text and jd_for_analysis:
        ats_score = calculate_ats_compliance(cv_text, jd_for_analysis)
        clarity_score = calculate_human_clarity(cv_text)
        
        col_ats, col_clarity = st.columns(2)
        
        with col_ats:
            delta_ats = "✅ Good!" if ats_score >= 70 else f"↑ Target: 95%"
            st.metric("ATS Compliance", f"{ats_score}%", delta=delta_ats)
            st.progress(ats_score / 100)
            if ats_score < 70:
                st.caption("💡 Tip: Add more keywords from the job description")
        
        with col_clarity:
            delta_clarity = "✅ Good!" if clarity_score >= 75 else f"↑ Target: 75%"
            st.metric("Human Clarity", f"{clarity_score}%", delta=delta_clarity)
            st.progress(clarity_score / 100)
            if clarity_score < 75:
                st.caption("💡 Tip: Use shorter sentences and add metrics")
    else:
        st.info("Upload a CV and paste a Job Description to see your optimization scores.")
        ats_score = 0
        clarity_score = 0
    
    # --- SECTION 3: Log Finalized Application ---
    st.markdown("---")
    st.subheader("3️⃣ Log Finalized Application")
    
    col_company, col_job, col_log = st.columns([2, 2, 1])
    company_name = col_company.text_input("Company Name", key="log_company")
    job_title = col_job.text_input("Job Title/ID", key="log_job")
    
    with col_log:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📝 Log Application", type="secondary", use_container_width=True):
            if company_name and job_title:
                if save_application(st.session_state.user_id, company_name, job_title, ats_score, clarity_score):
                    st.success("✅ Application logged!")
                    st.rerun()
                else:
                    st.error("Failed to save.")
            else:
                st.warning("Enter company and job title.")
    
    # --- SECTION 4: Application History Ledger ---
    st.markdown("---")
    st.subheader("4️⃣ Application History Ledger")
    
    df_ledger = fetch_application_ledger(st.session_state.user_id)
    
    if not df_ledger.empty:
        # Display table
        st.dataframe(
            df_ledger[['Company', 'JobID', 'Outcome', 'Compliance', 'Clarity']],
            use_container_width=True,
            hide_index=True
        )
        
        # Update outcome
        st.caption("Update Application Status")
        col_sel, col_status, col_update = st.columns([3, 2, 1])
        
        options = {f"{row['Company']} - {row['JobID']}": row['id'] for _, row in df_ledger.iterrows()}
        selected = col_sel.selectbox("Select Application", list(options.keys()), key="update_select")
        new_status = col_status.selectbox("New Status", ['Pending', 'Interview', 'Rejected', 'Offer'], key="update_status")
        
        with col_update:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Update", use_container_width=True):
                update_application_status(options[selected], new_status)
                st.success("Updated!")
                st.rerun()
    else:
        st.info("No applications logged yet. Start tracking your job applications above!")

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

    with st.sidebar:
        st.subheader(f"User: {st.session_state.user.split('@')[0]}")
        nav = st.radio("Menu", [
            "Dashboard", 
            "Instant Cover Letter", 
            "Voice Interview Sim",
            "⚙️ Account Settings"
        ])
        st.divider()
        if st.button("Logout"): logout()

    if nav == "Dashboard":
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
                            
                            # Save to Supabase
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
