import streamlit as st
import pandas as pd
import re
import numpy as np
import pypdf
from supabase import create_client
from groq import Groq
from fpdf import FPDF
import os

# --- Configuration ---
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Supabase & Groq Init ---
@st.cache_resource
def init_supabase():
    def get_secret(key):
        if key in os.environ: return os.environ[key]
        try: return st.secrets[key]
        except: return None
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

@st.cache_resource
def init_groq():
    def get_secret(key):
        if key in os.environ: return os.environ[key]
        try: return st.secrets[key]
        except: return None
    key = get_secret("GROQ_API_KEY")
    if key: return Groq(api_key=key)
    return None

try:
    supabase = init_supabase()
    groq_client = init_groq()
except:
    supabase = None
    groq_client = None

# --- Helper Functions ---

def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: 
        return ""

def create_pdf(text):
    """Safe PDF Generator"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=11)
        
        # Sanitize Text
        replacements = {
            ''': "'", ''': "'", '"': '"', '"': '"', '–': '-', '—': '-',
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

# --- Main Page ---

def compiler_page():
    st.markdown(f'<h1 style="color:{ACCENT_ORANGE}; text-align: center;">🤖 CV Compiler & Optimizer</h1>', unsafe_allow_html=True)
    st.caption("All-in-one: Optimize your CV, check ATS compliance, and track applications")
    st.markdown("---")

    # Auth Check
    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to access CV Compiler.")
        return

    # =====================================================
    # SECTION 1: Smart CV Tailor
    # =====================================================
    st.subheader("1️⃣ Smart CV Tailor")
    
    col_upload, col_jd = st.columns(2)
    with col_upload:
        uploaded_file = st.file_uploader("Upload your CV (PDF/TXT)", type=["pdf", "txt"], key="compiler_cv_upload")
    with col_jd:
        jd_text = st.text_area("Paste Job Description:", height=150, key="compiler_jd")
    
    # Extract CV text
    cv_text = ""
    if uploaded_file:
        cv_text = extract_text(uploaded_file)
        st.session_state['compiler_cv_text'] = cv_text
    elif 'compiler_cv_text' in st.session_state:
        cv_text = st.session_state['compiler_cv_text']
    
    # Optimize Bullets Button
    if st.button("🚀 Optimize Bullets", type="primary", use_container_width=True):
        if not groq_client:
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
                    
                    TASK: Rewrite the CV bullet points to include relevant keywords from the job description.
                    
                    IMPORTANT FORMATTING RULES:
                    - Output ONLY plain text bullet points
                    - Start each bullet with a dash (-) or bullet (•)
                    - DO NOT use any markdown formatting like ** or * or # or __
                    - DO NOT use bold, italic, or any special formatting
                    - Keep each bullet concise and professional
                    - Focus on action verbs and quantified achievements
                    
                    Output the optimized bullets now:
                    """
                    completion = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    if completion and completion.choices:
                        optimized = completion.choices[0].message.content
                        # Clean any remaining markdown formatting
                        optimized = optimized.replace('**', '').replace('__', '').replace('*', '•')
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
            st.text_area("", st.session_state['compiler_optimized'], height=300, disabled=True, label_visibility="collapsed")
        
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
    
    # =====================================================
    # SECTION 2: Dual Optimization Dashboard (NO Suggested Content)
    # =====================================================
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
    
    # =====================================================
    # SECTION 3: Log Finalized Application
    # =====================================================
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
    
    # =====================================================
    # SECTION 4: Application History Ledger
    # =====================================================
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

# Run the page
compiler_page()
