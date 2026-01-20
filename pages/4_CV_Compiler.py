import streamlit as st
import pandas as pd
import re
import numpy as np
import pypdf
from supabase import create_client

# --- Configuration ---
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

supabase = init_supabase()

# --- Logic: Calculation & DB ---

def calculate_clarity(text):
    if not text: return 0
    metric_count = len(re.findall(r'\d[\d,\.]*', text)) 
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_words = len(re.findall(r'\b\w+\b', text))
    avg_words_per_sentence = total_words / len(sentences) if len(sentences) > 0 else 0
    clarity_base = 50 
    if avg_words_per_sentence < 15 and avg_words_per_sentence > 0:
        clarity_base += (15 - avg_words_per_sentence) * 1.0
    clarity_base += min(30, metric_count * 5)
    return int(np.clip(clarity_base, 40, 100))

def calculate_compliance(cv_text, jd_text):
    if not cv_text or not jd_text: return 0
    cv_words = set(re.findall(r'\b\w{3,}\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w{3,}\b', jd_text.lower()))
    intersection = len(cv_words.intersection(jd_words))
    union = len(cv_words.union(jd_words))
    compliance_score = (intersection / union) * 100 if union > 0 else 0
    return int(np.clip(compliance_score, 0, 100))

def get_missing_keywords(cv_text, jd_text):
    jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
    cv_words = set(re.findall(r'\b\w{4,}\b', cv_text.lower()))
    stop_words = {'responsible', 'experience', 'ability', 'required', 'years', 'skills', 'level', 'knowledge', 'design', 'must', 'will', 'client', 'work', 'manage', 'team', 'project'}
    missing = list(jd_words - cv_words)
    missing = [w for w in missing if w not in stop_words and w.isalpha()]
    return [w.capitalize() for w in missing[:5]]

def fetch_ledger(user_id):
    """Fetches application history from Supabase."""
    if not supabase: return pd.DataFrame()
    res = supabase.table("applications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        # Rename for UI consistency
        df = df.rename(columns={
            "created_at": "Date", 
            "company_name": "Company", 
            "job_id": "JobID", 
            "compliance_score": "Compliance", 
            "clarity_score": "Clarity", 
            "outcome": "Outcome"
        })
        return df
    return pd.DataFrame()

def log_application(user_id, company, job_id, comp, clar):
    """Saves new application to DB."""
    if not supabase: return
    supabase.table("applications").insert({
        "user_id": user_id,
        "company_name": company,
        "job_id": job_id,
        "compliance_score": comp,
        "clarity_score": clar,
        "outcome": "Pending"
    }).execute()

def update_db_outcome(app_id, new_outcome):
    """Updates the status of an existing application."""
    if not supabase: return
    supabase.table("applications").update({"outcome": new_outcome}).eq("id", app_id).execute()

# --- Page Render ---

def compiler_page():
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🤖 Aequor: CV Confidence Compiler</h1>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to manage your application ledger.")
        return

    # 1. Inputs
    cv_text = st.session_state.get('cv_text_to_process', "")
    if not cv_text:
        uploaded_file = st.file_uploader("Upload CV (PDF/TXT):", type=["pdf", "txt"], key="compiler_up")
        if uploaded_file:
            try:
                reader = pypdf.PdfReader(uploaded_file)
                cv_text = "".join([p.extract_text() for p in reader.pages])
                st.session_state['cv_text_to_process'] = cv_text
            except: pass
    
    if not cv_text:
        st.info("Upload a CV to begin.")
        return

    jd_input = st.text_area("Paste Job Description (JD):", height=150)
    
    # 2. Real-time Analysis
    comp = calculate_compliance(cv_text, jd_input)
    clar = calculate_clarity(cv_text)
    
    # Dashboard
    st.subheader("2. Dual Optimization Dashboard")
    col_comp, col_clarity, col_keywords = st.columns([1, 1, 2])
    
    with col_comp:
        st.metric("ATS Compliance", f"{comp}%", delta="Target: 95%")
        st.progress(comp/100)
        
    with col_clarity:
        st.metric("Human Clarity", f"{clar}%", delta="Target: 75%")
        st.progress(clar/100)

    with col_keywords:
        missing_kws = get_missing_keywords(cv_text, jd_input)
        if missing_kws:
            st.warning(f"Missing: {', '.join(missing_kws)}")
        else:
            st.success("Keywords aligned!")
    
    # 3. Log Application
    st.markdown("---")
    st.subheader("Log Finalized Application")
    col_log_1, col_log_2, col_log_3 = st.columns(3)
    company = col_log_1.text_input("Company Name")
    job_id = col_log_2.text_input("Job Title/ID")
    
    if col_log_3.button("Log Finalized Application", type="secondary", use_container_width=True):
        if company and job_id:
            log_application(st.session_state.user_id, company, job_id, comp, clar)
            st.success("Application saved to database.")
            st.rerun()

    # 4. Ledger Management
    st.markdown("---")
    st.subheader("Application History Ledger")
    df_ledger = fetch_ledger(st.session_state.user_id)
    
    if not df_ledger.empty:
        # Show Table
        st.dataframe(df_ledger[['Company', 'JobID', 'Outcome', 'Compliance', 'Clarity']], use_container_width=True)
        
        # Update Outcome Interface
        st.subheader("Update Application Outcome")
        col_up_1, col_up_2, col_up_3 = st.columns([2, 1, 1])
        
        # Create a selection map (Display string -> ID)
        options = {f"{row['Company']} - {row['JobID']}": row['id'] for _, row in df_ledger.iterrows()}
        selected_label = col_up_1.selectbox("Select Application", options.keys())
        new_status = col_up_2.selectbox("New Status", ['Pending', 'Interview', 'Rejected', 'Offer'])
        
        if col_up_3.button("Update"):
            app_id = options[selected_label]
            update_db_outcome(app_id, new_status)
            st.success("Status Updated!")
            st.rerun()

compiler_page()
