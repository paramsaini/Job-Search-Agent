import streamlit as st
import pandas as pd
import re
import numpy as np
from datetime import datetime

# --- Configuration (Copied from main app for consistency) ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Initialization ---
if 'ledger_data' not in st.session_state:
    st.session_state['ledger_data'] = pd.DataFrame(columns=['Date', 'Company', 'JobID', 'Compliance', 'Clarity', 'Outcome'])

# --- Core Logic: Compiler Simulation ---

def calculate_clarity(text):
    """
    Simulates Human Clarity Score (0-100) based on readability metrics.
    Focuses on conciseness and quantification.
    """
    if not text:
        return 0

    # 1. Active Voice & Quantification Check (Simulated)
    # Count of numbers (a proxy for quantification/metrics)
    metric_count = len(re.findall(r'\d[\d,\.]*', text)) 
    
    # 2. Readability (Flesch-Kincaid style, simplified)
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_words = len(re.findall(r'\b\w+\b', text))
    
    avg_words_per_sentence = total_words / len(sentences) if len(sentences) > 0 else 0

    # Weights: Low word count per sentence (concise) is good. High metric count is good.
    clarity_base = 50 
    
    # Boost for conciseness (max 20 points)
    if avg_words_per_sentence < 15 and avg_words_per_sentence > 0:
        clarity_base += (15 - avg_words_per_sentence) * 1.0

    # Boost for quantification (max 30 points)
    clarity_base += min(30, metric_count * 5)
    
    return int(np.clip(clarity_base, 40, 100))

def calculate_compliance(cv_text, jd_text):
    """
    Simulates ATS Compliance Score (0-100) based on keyword overlap.
    """
    if not cv_text or not jd_text:
        return 0

    cv_words = set(re.findall(r'\b\w{3,}\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w{3,}\b', jd_text.lower()))
    
    # Simple Jaccard Index (Intersection / Union) is a robust compliance measure
    intersection = len(cv_words.intersection(jd_words))
    union = len(cv_words.union(jd_words))
    
    compliance_score = (intersection / union) * 100 if union > 0 else 0
    
    return int(np.clip(compliance_score, 0, 100))

def get_missing_keywords(cv_text, jd_text):
    """Identifies top 5 critical keywords present in JD but missing from CV."""
    jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
    cv_words = set(re.findall(r'\b\w{4,}\b', cv_text.lower()))
    
    # Simple stop word list based on common resume filler
    stop_words = {'responsible', 'experience', 'ability', 'required', 'years', 'skills', 'level', 'knowledge', 'design', 'must', 'will', 'client', 'work', 'manage', 'team', 'project'}
    
    missing = list(jd_words - cv_words)
    
    # Filter out stop words and general terms
    missing = [w for w in missing if w not in stop_words and w.isalpha()]
    
    # Return top 5, capitalized
    return [w.capitalize() for w in missing[:5]]


def log_finalized_application(company, job_id, live_compliance, live_clarity):
    """Adds the final application version and score to the ledger."""
    new_entry = pd.DataFrame([{
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Company': company,
        'JobID': job_id,
        'Compliance': live_compliance,
        'Clarity': live_clarity,
        'Outcome': 'Pending'
    }])
    st.session_state['ledger_data'] = pd.concat([st.session_state['ledger_data'], new_entry], ignore_index=True)


# --- Page Render ---

def compiler_page():
    
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🤖 CV Confidence Compiler</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: {ACCENT_CYAN}; font-size: 1.1em; font-weight: 500; text-shadow: 0 0 2px {ACCENT_CYAN}40;">
        **Niche Solution: Algorithmic Black Box.** Measure the trade-off between **ATS Compliance** and **Human Clarity** in real-time before you apply.
    </p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Get required data from session state
    cv_text = st.session_state.get('cv_text_to_process', None)
    
    if not cv_text:
        st.error("⚠️ **PREREQUISITE:** Please run a full analysis on the Home Page first to load your processed CV content.")
        return

    st.subheader("1. Job Description Input")
    jd_input = st.text_area("Paste the Job Description (JD) here:", height=200, key="compiler_jd_input")
    
    # --- CALCULATE SCORES ---
    # Initial scores based on the master CV text
    initial_compliance_score = calculate_compliance(cv_text, jd_input)
    initial_clarity_score = calculate_clarity(cv_text)
    
    # --- Dual Meter Dashboard (Attractive Visualization) ---
    st.markdown("---")
    st.subheader("2. Dual Optimization Dashboard")
    
    col_comp, col_clarity, col_keywords = st.columns([1, 1, 2])

    # 1. Compliance Meter
    with col_comp:
        st.markdown(f'<p style="color: {ACCENT_CYAN}; font-weight: bold; margin-bottom: 0;">ATS Compliance</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #ccc; font-size: 0.8em; margin-bottom: 5px;">(Keyword Density)</p>', unsafe_allow_html=True)
        st.metric(label="Score", value=f"{initial_compliance_score}%", delta="Target: 95%")
        st.progress(initial_compliance_score / 100.0)
        
    # 2. Clarity Meter
    with col_clarity:
        st.markdown(f'<p style="color: {ACCENT_ORANGE}; font-weight: bold; margin-bottom: 0;">Human Clarity</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #ccc; font-size: 0.8em; margin-bottom: 5px;">(Readability/Metrics)</p>', unsafe_allow_html=True)
        st.metric(label="Score", value=f"{initial_clarity_score}%", delta="Target: 75%")
        st.progress(initial_clarity_score / 100.0)

    # 3. Missing Keywords
    with col_keywords:
        missing_kws = get_missing_keywords(cv_text, jd_input)
        st.markdown(f'<p style="color: {ACCENT_YELLOW}; font-weight: bold;">Top 5 Missing Critical Keywords</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="glass-card" style="border: 2px solid {ACCENT_YELLOW}40;">', unsafe_allow_html=True)
        
        if missing_kws:
            st.code(", ".join(missing_kws), language='markdown')
            st.caption("Inject these terms into your CV to boost Compliance.")
        else:
            st.success("Keywords look aligned!")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("3. Live-Edit Optimization Sandbox")
    st.markdown(f'<p style="color: {ACCENT_CYAN};">Edit your CV snapshot below to instantly see the Compliance and Clarity scores update. This is your safe space for optimizing.</p>', unsafe_allow_html=True)

    # Sandbox where users can paste/edit their CV text
    optimized_cv_text = st.text_area("Live CV Snapshot (Edit me!)", value=cv_text, height=400, key="live_edit_cv")
    
    # Re-calculate scores dynamically based on the edited text
    live_compliance = calculate_compliance(optimized_cv_text, jd_input)
    live_clarity = calculate_clarity(optimized_cv_text)
    
    # Update score display instantly
    st.markdown(f"""
    <div style='text-align: center; margin-top: 15px;'>
        <p style='font-size: 1.5rem; font-weight: bold; color: white;'>
            LIVE SCORE: 
            <span style='color: {ACCENT_CYAN};'>Compliance {live_compliance}%</span> | 
            <span style='color: {ACCENT_ORANGE};'>Clarity {live_clarity}%</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Application Version Ledger ---
    st.subheader("4. Finalize & Log Application")
    
    col_log_1, col_log_2, col_log_3 = st.columns(3)
    company = col_log_1.text_input("Company Name", key="log_company")
    job_id = col_log_2.text_input("Job ID/Title", key="log_jobid")
    
    if col_log_3.button("Log Finalized Application", type="secondary", use_container_width=True):
        if company and job_id:
            # Call the separate logging function
            log_finalized_application(company, job_id, live_compliance, live_clarity)
            st.rerun()
        else:
            st.warning("Please enter the Company Name and Job ID/Title.")

    st.markdown("---")
    st.subheader("Application History Ledger")
    
    # Ledger Update Mechanism
    if not st.session_state['ledger_data'].empty:
        df_ledger = st.session_state['ledger_data'].copy()
        df_ledger.index.name = 'Index'
        
        st.dataframe(df_ledger.style.applymap(
            lambda x: f'background-color: {ACCENT_GREEN}30' if x == 'Interview' or x == 'Offer' else (
                      f'background-color: {ACCENT_ORANGE}30' if x == 'Rejected' else ''))
                      .format({"Compliance": "{:.0f}%", "Clarity": "{:.0f}%"}), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Update Application Outcome")
        
        col_update_1, col_update_2, col_update_3 = st.columns([1, 1, 2])
        
        # 1. Select Index to Update
        entry_indices = df_ledger.index.tolist()
        # FIX: Ensure we only show available indices, and use a unique key
        if entry_indices:
            selected_index = col_update_1.selectbox("Select Entry Index to Update", entry_indices, key="select_index_update")
            
            # 2. Select New Outcome
            new_outcome = col_update_2.selectbox("Set Final Outcome", 
                                                ['Pending', 'Interview', 'Rejected', 'Offer'], key="select_outcome")
            
            # 3. Update Button
            if col_update_3.button("Apply Outcome Change", type="secondary", use_container_width=True):
                st.session_state['ledger_data'].loc[selected_index, 'Outcome'] = new_outcome
                st.success(f"Outcome for Index {selected_index} updated to {new_outcome}.")
                st.rerun() # Rerun to refresh the dataframe

compiler_page()
