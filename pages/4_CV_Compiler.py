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

def calculate_metrics(cv_text, jd_text):
    """Calculates mock Compliance and Clarity scores."""
    if not cv_text: return 0, 0
    
    # Compliance (Keyword Jaccard)
    cv_words = set(re.findall(r'\b\w{3,}\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w{3,}\b', jd_text.lower())) if jd_text else set()
    intersection = len(cv_words.intersection(jd_words))
    union = len(cv_words.union(jd_words))
    compliance = (intersection / union) * 100 if union > 0 else 0
    
    # Clarity (Readability Proxy)
    sentences = [s for s in re.split(r'[.!?]', cv_text) if s.strip()]
    avg_len = len(cv_text.split()) / len(sentences) if sentences else 0
    clarity = 100 - min(50, avg_len) # Simple proxy: shorter sentences = higher clarity
    
    return int(np.clip(compliance, 10, 100)), int(np.clip(clarity, 40, 100))

def fetch_ledger(user_id):
    """Fetches application history from Supabase."""
    if not supabase: return pd.DataFrame()
    res = supabase.table("applications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

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
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🤖 CV Confidence Compiler</h1>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to manage your application ledger.")
        return

    # 1. Inputs
    cv_text = st.session_state.get('cv_text_to_process', "")
    if not cv_text:
        uploaded_file = st.file_uploader("Upload CV (PDF/TXT):", type=["pdf", "txt"])
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
    comp, clar = calculate_metrics(cv_text, jd_input)
    
    c1, c2 = st.columns(2)
    c1.metric("ATS Compliance", f"{comp}%", delta="Target: 95%")
    c2.metric("Human Clarity", f"{clar}%", delta="Target: 75%")
    
    st.progress(comp/100)
    
    # 3. Log Application
    st.markdown("---")
    st.subheader("Log Finalized Application")
    with st.form("log_app"):
        col_log_1, col_log_2 = st.columns(2)
        company = col_log_1.text_input("Company Name")
        job_id = col_log_2.text_input("Job Title/ID")
        
        if st.form_submit_button("Save to Ledger", type="secondary"):
            if company and job_id:
                log_application(st.session_state.user_id, company, job_id, comp, clar)
                st.success("Application saved to database.")
                st.rerun()

    # 4. Ledger Management
    st.markdown("---")
    st.subheader("Application History")
    df_ledger = fetch_ledger(st.session_state.user_id)
    
    if not df_ledger.empty:
        # Show Table
        st.dataframe(df_ledger[['company_name', 'job_id', 'outcome', 'compliance_score', 'clarity_score']], use_container_width=True)
        
        # Update Outcome Interface
        st.caption("Update Application Status:")
        col_up_1, col_up_2, col_up_3 = st.columns([2, 1, 1])
        
        # Create a selection map (Display string -> ID)
        options = {f"{row['company_name']} - {row['job_id']}": row['id'] for _, row in df_ledger.iterrows()}
        selected_label = col_up_1.selectbox("Select Application", options.keys())
        new_status = col_up_2.selectbox("New Status", ['Pending', 'Interview', 'Rejected', 'Offer'])
        
        if col_up_3.button("Update"):
            app_id = options[selected_label]
            update_db_outcome(app_id, new_status)
            st.success("Status Updated!")
            st.rerun()

compiler_page()
