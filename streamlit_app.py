import streamlit as st
import os
import pypdf
import json
import plotly.graph_objects as go
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

def page_skill_migration():
    st.header("📈 Skill Migration Analysis")
    
    # Try to get data from Session, otherwise fetch from DB
    report = None
    cv_text = st.session_state.get('last_cv_text', '')  # Get CV text if available
    
    if "results" in st.session_state and "rep" in st.session_state.results:
        report = st.session_state.results["rep"]
    elif supabase and st.session_state.user_id:
        try:
            # Fetch last analysis
            data = supabase.table("analyses").select("*").eq("user_id", st.session_state.user_id).order("created_at", desc=True).limit(1).execute()
            if data.data:
                # Handle potentially stringified JSON
                raw_json = data.data[0]['report_json']
                if isinstance(raw_json, str):
                    report = json.loads(raw_json)
                else:
                    report = raw_json
        except Exception as e:
            st.error(f"Could not load history: {e}")

    if report:
        c1, c2, c3 = st.columns(3)
        with c1:
            score = report.get('predictive_score', 0)
            st.metric("Predictive Match", f"{score}%")
            st.progress(score / 100)
        with c2:
            tech = report.get('tech_score', 0)
            st.metric("Skills Strength", f"{tech}%")
            st.progress(tech / 100)
        with c3:
            weakest = report.get('weakest_link_skill', 'N/A')
            st.error(f"Focus Area: {weakest}")
            st.caption("Prioritize improving this skill.")
        
        st.divider()
        
        # Dynamic Career Paths based on detected industry
        st.subheader("🎯 Career Trajectory Paths")
        
        # Detect industry from weakest_link_skill or other indicators
        weakest_lower = weakest.lower() if weakest else ""
        
        # Healthcare/Care Worker industry detection
        healthcare_keywords = ['care', 'patient', 'health', 'medical', 'nursing', 'clinical', 'empathy', 'compassion']
        tech_keywords = ['python', 'java', 'cloud', 'aws', 'coding', 'programming', 'software', 'data', 'machine learning']
        
        is_healthcare = any(kw in weakest_lower for kw in healthcare_keywords)
        is_tech = any(kw in weakest_lower for kw in tech_keywords)
        
        # Default to showing relevant career paths
        if is_healthcare or (not is_tech and 'care' in str(report).lower()):
            # Healthcare/Care Worker Career Paths
            st.markdown("### 🏥 Healthcare & Care Industry Paths")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #10B981, #059669); padding: 20px; border-radius: 12px; height: 200px;">
                    <h4 style="color: white; margin: 0;">Senior Care Worker</h4>
                    <p style="color: #D1FAE5; font-size: 0.9em;">→ Team Leader / Supervisor</p>
                    <p style="color: white; font-weight: bold;">85% success rate</p>
                    <p style="color: #D1FAE5; font-size: 0.8em;">~6-12 months</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #3B82F6, #1D4ED8); padding: 20px; border-radius: 12px; height: 200px;">
                    <h4 style="color: white; margin: 0;">Care Coordinator</h4>
                    <p style="color: #DBEAFE; font-size: 0.9em;">→ Care Manager / Director</p>
                    <p style="color: white; font-weight: bold;">70% success rate</p>
                    <p style="color: #DBEAFE; font-size: 0.8em;">~12-18 months</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #8B5CF6, #6D28D9); padding: 20px; border-radius: 12px; height: 200px;">
                    <h4 style="color: white; margin: 0;">Healthcare Assistant</h4>
                    <p style="color: #EDE9FE; font-size: 0.9em;">→ Registered Nurse (with training)</p>
                    <p style="color: white; font-weight: bold;">60% success rate</p>
                    <p style="color: #EDE9FE; font-size: 0.8em;">~2-3 years</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📊 Key Skills for Care Industry")
            
            skills_data = {
                'Skill': ['Patient Care', 'Communication', 'First Aid/CPR', 'Documentation', 'Empathy', 'Time Management'],
                'Market Demand': [90, 85, 80, 75, 95, 70],
                'Your Level': [report.get('tech_score', 50), 75, 60, 65, 80, 70]
            }
            
            fig = go.Figure(data=[
                go.Bar(name='Market Demand', x=skills_data['Skill'], y=skills_data['Market Demand'], marker_color='#00E0FF'),
                go.Bar(name='Your Level', x=skills_data['Skill'], y=skills_data['Your Level'], marker_color='#FF8C00')
            ])
            fig.update_layout(
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            # Tech/Software Industry Career Paths (original)
            st.markdown("### 💻 Technology Industry Paths")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #10B981, #059669); padding: 20px; border-radius: 12px; height: 200px;">
                    <h4 style="color: white; margin: 0;">Management Track</h4>
                    <p style="color: #D1FAE5; font-size: 0.9em;">→ Engineering Manager / Director</p>
                    <p style="color: white; font-weight: bold;">90% success rate</p>
                    <p style="color: #D1FAE5; font-size: 0.8em;">~8 months</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #3B82F6, #1D4ED8); padding: 20px; border-radius: 12px; height: 200px;">
                    <h4 style="color: white; margin: 0;">Technical Leadership</h4>
                    <p style="color: #DBEAFE; font-size: 0.9em;">→ Tech Lead / Principal Engineer</p>
                    <p style="color: white; font-weight: bold;">60% success rate</p>
                    <p style="color: #DBEAFE; font-size: 0.8em;">~10 months</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #8B5CF6, #6D28D9); padding: 20px; border-radius: 12px; height: 200px;">
                    <h4 style="color: white; margin: 0;">Domain Expert</h4>
                    <p style="color: #EDE9FE; font-size: 0.9em;">→ Consultant / Advisor</p>
                    <p style="color: white; font-weight: bold;">55% success rate</p>
                    <p style="color: #EDE9FE; font-size: 0.8em;">~12 months</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        st.info("💡 To generate a new analysis with different career paths, go to the Dashboard and upload a CV.")
    else:
        st.warning("No analysis found.")
        st.write("Go to the **Dashboard** and click 'Generate Strategy' to see your Skill Migration report.")

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
            "Skill Migration",
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
                
    elif nav == "Skill Migration": page_skill_migration()
    elif nav == "Instant Cover Letter": page_cover_letter()
    elif nav == "Voice Interview Sim": page_interview_sim()
    elif nav == "⚙️ Account Settings": page_delete_account()

if __name__ == "__main__":
    main()
