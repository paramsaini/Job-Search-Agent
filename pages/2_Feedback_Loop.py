import streamlit as st
import pandas as pd
import re
from datetime import datetime # Necessary for logging functions if used here
import numpy as np # <--- FIX: Added missing import

# --- Configuration (Copied from main app for consistency) ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Logic: Mock Comparison ---

def analyze_friction(cv_text, jd_text, predictive_score):
    """
    Simulates recruiter friction by comparing keyword density and seniority.
    The output is heavily weighted by the overall predictive score from Gemini.
    """
    if not cv_text or not jd_text:
        return 0, "No data provided.", ACCENT_YELLOW
    
    cv_words = set(re.findall(r'\b\w+\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
    
    # 1. Keyword Overlap
    overlap = len(cv_words.intersection(jd_words))
    jd_length = len(jd_words)
    keyword_match_percent = (overlap / jd_length) * 100 if jd_length > 0 else 0
    
    # 2. Seniority Match (Mock logic using common keywords)
    seniority_keywords = {'senior', 'lead', 'principal', 'manager', 'director'}
    cv_seniority = any(word in cv_words for word in seniority_keywords)
    jd_seniority = any(word in jd_words for word in seniority_keywords)
    
    # 3. Friction Calculation (Higher score = Lower Friction, i.e., good match)
    # Start base score high and deduct points for friction.
    base_match = (keyword_match_percent * 0.5) + (predictive_score * 0.5)
    friction_score = base_match
    
    objection = "Perfect match! Proceed with application."
    friction_level = "Low"
    color = ACCENT_GREEN
    
    # Deduct points if Gemini score is low or seniority mismatch is present
    if predictive_score < 70:
        friction_score -= 10
        objection = "General profile mismatch. The role requires a stronger foundation in core skills."
        friction_level = "High"
        color = ACCENT_ORANGE
    elif (cv_seniority != jd_seniority):
        friction_score -= 5
        objection = "Seniority mismatch detected. Re-tailor your summary to emphasize scope/impact if aiming higher, or specific execution if aiming lower."
        friction_level = "Medium"
        color = ACCENT_YELLOW
        
    final_score = int(np.clip(friction_score, 40, 100)) # FIX: np is now defined
    
    return final_score, objection, color, keyword_match_percent

# --- Page Render ---

def feedback_loop_page():
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🔄 Predictive Feedback Loop</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: {ACCENT_CYAN}; font-size: 1.1em; font-weight: 500; text-shadow: 0 0 2px {ACCENT_CYAN}40;">
        **Niche Solution: Opaque Feedback.** Instantly simulate a recruiter's first impression by comparing your CV to a Job Description (JD). Eliminate wasted time on low-probability applications.
    </p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Get CV text from session state (prerequisite)
    cv_text = st.session_state.get('cv_text_to_process', None)
    predictive_score = st.session_state.get('skill_gap_report', {}).get('predictive_score', 75)

    if not cv_text:
        st.error("⚠️ **PREREQUISITE:** Please run a full analysis on the Home Page first to load your processed CV content.")
        return

    st.subheader("1. Paste Job Description (JD)")
    jd_input = st.text_area("Paste the Job Description (JD) here:", height=300, key="jd_input_area")
    
    if st.button("Simulate Recruiter Sentiment", type="primary", use_container_width=True):
        if not jd_input:
            st.warning("Please paste the JD text to begin the simulation.")
            return

        final_score, objection, color, kw_match = analyze_friction(cv_text, jd_input, predictive_score)
        
        st.session_state['friction_score'] = final_score
        st.session_state['recruiter_objection'] = objection
        st.session_state['friction_color'] = color
        st.session_state['kw_match'] = kw_match

    if 'friction_score' in st.session_state:
        st.markdown("---")
        st.subheader("2. Simulation Results")
        
        col_gauge, col_objection = st.columns([1, 2])
        
        with col_gauge:
            st.markdown(f'<p style="color: {st.session_state["friction_color"]}; font-weight: bold;">JD Match Score</p>', unsafe_allow_html=True)
            st.metric(label="Match Score (0-100)", 
                      value=f"{st.session_state['friction_score']}%", 
                      delta=f"Keywords: {st.session_state['kw_match']:.1f}%")
            
        with col_objection:
            st.markdown(f'<p style="color: {ACCENT_CYAN}; font-weight: bold;">Recruiter Sentiment (The Truth)</p>', unsafe_allow_html=True)
            st.warning(f'**Simulated Objection:** {st.session_state["recruiter_objection"]}')
            
            st.markdown(f"""
            <div style='color: {ACCENT_YELLOW}; font-size: 0.9rem; margin-top: 15px;'>
                *Action: Edit your CV's summary/skills to directly address the objection above.*
            </div>
            """, unsafe_allow_html=True)
            
feedback_loop_page()
