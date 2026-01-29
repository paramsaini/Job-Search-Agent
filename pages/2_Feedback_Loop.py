import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client
from groq import Groq
import os
import json
import re
import numpy as np
import time

# --- Configuration ---
st.set_page_config(page_title="Feedback Loop", page_icon="🔄", layout="wide")

BG_DARK = "#0f172a"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
ACCENT_RED = "#EF4444"
ACCENT_PURPLE = "#8B5CF6"

# --- Supabase & Groq Init ---
@st.cache_resource
def init_supabase():
    def get_secret(key):
        if key in os.environ: return os.environ[key]
        try: return st.secrets[key]
        except: return None
    url, key = get_secret("SUPABASE_URL"), get_secret("SUPABASE_KEY")
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

try: supabase = init_supabase()
except: supabase = None
try: groq_client = init_groq()
except: groq_client = None

# --- Helper Functions ---
def extract_text_from_file(file):
    if file is None: return ""
    try:
        if file.type == "application/pdf":
            import pypdf
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def analyze_cv_sections(cv_text):
    sections = {
        "contact": {"keywords": ["email", "phone", "linkedin", "address", "@"], "found": False, "importance": "high"},
        "summary": {"keywords": ["summary", "objective", "profile", "about"], "found": False, "importance": "high"},
        "experience": {"keywords": ["experience", "work history", "employment"], "found": False, "importance": "critical"},
        "education": {"keywords": ["education", "degree", "university", "college"], "found": False, "importance": "high"},
        "skills": {"keywords": ["skills", "technologies", "competencies", "tools"], "found": False, "importance": "critical"},
        "achievements": {"keywords": ["achievements", "awards", "accomplishments", "certifications"], "found": False, "importance": "medium"},
    }
    cv_lower = cv_text.lower()
    for section, data in sections.items():
        for keyword in data["keywords"]:
            if keyword in cv_lower:
                sections[section]["found"] = True
                break
    return sections

def simulate_6_second_scan(cv_text, jd_text):
    cv_lower = cv_text.lower()
    jd_lower = jd_text.lower()
    jd_keywords = set(re.findall(r'\b\w{4,}\b', jd_lower))
    stop_words = {'with', 'have', 'that', 'this', 'will', 'your', 'from', 'they', 'been', 'were', 'their', 'what', 'when', 'where', 'which', 'while', 'about', 'after', 'before', 'being', 'between', 'both', 'each', 'would', 'could', 'should', 'through'}
    jd_keywords = jd_keywords - stop_words
    first_impression = cv_text[:200]
    skills_match = re.search(r'skills?[:\s]+(.*?)(?:\n\n|\Z)', cv_text, re.IGNORECASE | re.DOTALL)
    skills_text = skills_match.group(1)[:300] if skills_match else ""
    exp_match = re.search(r'experience[:\s]+(.*?)(?:\n\n|\Z)', cv_text, re.IGNORECASE | re.DOTALL)
    recent_exp = exp_match.group(1)[:400] if exp_match else ""
    return {
        "header": {"text": first_impression, "attention": 95, "time_spent": "1.5s", "keywords_found": len([k for k in list(jd_keywords)[:10] if k in first_impression.lower()])},
        "skills": {"text": skills_text or "Not clearly defined", "attention": 85, "time_spent": "2s", "keywords_found": len([k for k in list(jd_keywords)[:15] if k in skills_text.lower()])},
        "recent_experience": {"text": recent_exp or "Not found", "attention": 75, "time_spent": "2s", "keywords_found": len([k for k in list(jd_keywords)[:15] if k in recent_exp.lower()])},
        "rest_of_cv": {"text": "Skimmed quickly", "attention": 20, "time_spent": "0.5s", "keywords_found": 0}
    }

def generate_rejection_reasons(cv_text, jd_text):
    reasons = []
    cv_lower = cv_text.lower()
    metrics = re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|months?|projects?|team|people|clients?)', cv_lower)
    if len(metrics) < 3:
        reasons.append({"reason": "No quantified achievements", "severity": "high", "fix": "Add metrics like '25% increase' or 'managed team of 8'"})
    years_have = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|present)', cv_lower, re.IGNORECASE)
    required_skills = re.findall(r'required[:\s]+([^.]+)', jd_text.lower())
    if required_skills:
        req_text = required_skills[0]
        missing_count = sum(1 for word in req_text.split() if len(word) > 4 and word not in cv_lower)
        if missing_count > 3:
            reasons.append({"reason": f"Missing {missing_count} required skills", "severity": "high", "fix": "Add missing keywords from 'Required' section"})
    if not reasons:
        reasons.append({"reason": "No major red flags detected", "severity": "low", "fix": "Focus on tailoring keywords for this specific role"})
    return reasons

def calculate_success_probability(cv_text, jd_text):
    score = 50
    cv_lower = cv_text.lower()
    jd_lower = jd_text.lower()
    jd_words = set(re.findall(r'\b\w{4,}\b', jd_lower))
    cv_words = set(re.findall(r'\b\w{4,}\b', cv_lower))
    overlap = len(jd_words.intersection(cv_words)) / len(jd_words) if jd_words else 0
    score += int(overlap * 30)
    metrics = len(re.findall(r'\d+%|\$\d+[KMB]?|\d+\s*(?:years?|projects?)', cv_lower))
    score += min(10, metrics * 2)
    sections = analyze_cv_sections(cv_text)
    complete_sections = sum(1 for s in sections.values() if s['found'])
    score += complete_sections * 2
    return min(95, max(25, score))

def get_recruiter_persona_feedback(cv_text, jd_text, persona, groq_client):
    if not groq_client: return None
    persona_prompts = {
        "corporate_hr": "You are a Corporate HR Manager at a Fortune 500 company. Formal, process-oriented.",
        "startup_founder": "You are a Startup Founder. Value hustle, skills, speed. Casual, direct.",
        "ats_bot": "You are an ATS. ONLY care about exact keyword matches and formatting."
    }
    try:
        prompt = f"""
        {persona_prompts.get(persona, persona_prompts['corporate_hr'])}
        Review this CV for the following role.
        JOB: {jd_text[:1000]}
        CV: {cv_text[:2500]}
        Provide: 1. Initial impression 2. Top 3 strengths 3. Top 3 concerns 4. Decision (Yes/No) 5. One tip.
        """
        completion = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        return completion.choices[0].message.content
    except: return None

# --- Page Styling ---
def inject_custom_css():
    st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(to bottom right, #0f172a, #1e1b4b); color: #e2e8f0; }}
    .scan-area {{ border: 2px solid {ACCENT_CYAN}40; border-radius: 8px; padding: 15px; margin: 10px 0; position: relative; }}
    .scan-high {{ border-color: {ACCENT_GREEN}; background: {ACCENT_GREEN}10; }}
    .scan-medium {{ border-color: {ACCENT_YELLOW}; background: {ACCENT_YELLOW}10; }}
    .scan-low {{ border-color: {ACCENT_RED}10; background: transparent; }}
    .rejection-card {{ border-left: 4px solid; border-radius: 8px; padding: 15px; margin: 10px 0; }}
    .rejection-high {{ border-color: {ACCENT_RED}; background: {ACCENT_RED}15; }}
    .rejection-medium {{ border-color: {ACCENT_YELLOW}; background: {ACCENT_YELLOW}15; }}
    .rejection-low {{ border-color: {ACCENT_GREEN}; background: {ACCENT_GREEN}15; }}
    .probability-circle {{ width: 150px; height: 150px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: bold; margin: 0 auto; }}
    .persona-card {{ background: {BG_DARK}; border: 1px solid {ACCENT_PURPLE}40; border-radius: 12px; padding: 15px; margin: 10px 0; }}
    </style>
    """, unsafe_allow_html=True)

# --- Main Page ---
def feedback_loop_page():
    inject_custom_css()
    
    # BACK BUTTON
    if st.button("← Back to Main Page"):
        st.switch_page("Main_Page.py")
        
    # CONSISTENT HEADER
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #FF8C00; margin-bottom: 0;">🚀 Job-Search-Agent</h1>
        <p style="color: #e2e8f0; font-size: 1.2rem; margin-top: 5px;">AI-Powered Career Guidance</p>
        <hr style="border-color: rgba(255, 140, 0, 0.3);">
    </div>
    """, unsafe_allow_html=True)

    st.subheader("🔄 Predictive Feedback Loop")
    st.caption("See Your CV Through a Recruiter's Eyes")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to access the Feedback Loop.")
        return

    st.subheader("📄 Upload Your Documents")
    col_cv, col_jd = st.columns(2)
    with col_cv:
        uploaded_cv = st.file_uploader("Upload CV (PDF/TXT)", type=["pdf", "txt"], key="feedback_cv")
        cv_text = ""
        if uploaded_cv:
            cv_text = extract_text_from_file(uploaded_cv)
            st.session_state['feedback_cv_text'] = cv_text
            st.success(f"✅ CV loaded ({len(cv_text.split())} words)")
        elif 'feedback_cv_text' in st.session_state:
            cv_text = st.session_state['feedback_cv_text']
    with col_jd:
        jd_text = st.text_area("Paste Job Description", height=200, key="feedback_jd")
        if jd_text: st.session_state['feedback_jd_text'] = jd_text

    if not cv_text or not jd_text:
        st.info("👆 Upload your CV and paste a Job Description to begin analysis")
        return

    if st.button("🔍 Run Complete Analysis", type="primary", use_container_width=True):
        st.session_state['run_feedback_analysis'] = True

    if not st.session_state.get('run_feedback_analysis'): return

    st.markdown("---")
    st.subheader("1️⃣ Interview Callback Probability")
    probability = calculate_success_probability(cv_text, jd_text)
    col_prob, col_factors = st.columns([1, 2])
    with col_prob:
        color = ACCENT_GREEN if probability >= 70 else ACCENT_YELLOW if probability >= 50 else ACCENT_RED
        status = "Strong Candidate" if probability >= 70 else "Competitive" if probability >= 50 else "Needs Improvement"
        st.markdown(f'<div class="probability-circle" style="border: 8px solid {color}; color: {color};">{probability}%</div>', unsafe_allow_html=True)
        st.markdown(f'<p style="text-align: center; margin-top: 10px; color: {color}; font-weight: bold;">{status}</p>', unsafe_allow_html=True)
    with col_factors:
        st.markdown("**Scoring Factors:**")
        jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_text.lower()))
        keyword_score = int(len(jd_words.intersection(cv_words)) / len(jd_words) * 100) if jd_words else 0
        st.progress(keyword_score / 100, text=f"Keyword Match: {keyword_score}%")

    st.markdown("---")
    st.subheader("2️⃣ The 6-Second Scan Simulation")
    with st.empty():
        for i in range(3, 0, -1):
            st.markdown(f"<h3 style='text-align: center; color: {ACCENT_ORANGE};'>⏱️ {i} seconds...</h3>", unsafe_allow_html=True)
            time.sleep(0.3)
        st.markdown(f"<h3 style='text-align: center; color: {ACCENT_GREEN};'>✅ Scan Complete!</h3>", unsafe_allow_html=True)
    scan_results = simulate_6_second_scan(cv_text, jd_text)
    for area, data in scan_results.items():
        css_class = "scan-high" if data['attention'] >= 80 else "scan-medium" if data['attention'] >= 50 else "scan-low"
        st.markdown(f'<div class="scan-area {css_class}"><b>{area.title()}</b> <span>👁️ {data["attention"]}%</span><p>{data["text"][:150]}...</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("3️⃣ Rejection Reason Predictor")
    reasons = generate_rejection_reasons(cv_text, jd_text)
    for reason in reasons:
        css_class = f"rejection-{reason['severity']}"
        icon = "🔴" if reason['severity'] == 'high' else "🟡"
        st.markdown(f'<div class="rejection-card {css_class}"><b>{icon} {reason["reason"]}</b><p style="color:{ACCENT_CYAN}">💡 Fix: {reason["fix"]}</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("4️⃣ AI Recruiter Persona Simulator")
    c1, c2, c3 = st.columns(3)
    if c1.button("🏢 Corporate HR"): st.session_state['selected_persona'] = 'corporate_hr'
    if c2.button("🚀 Startup Founder"): st.session_state['selected_persona'] = 'startup_founder'
    if c3.button("🤖 ATS Bot"): st.session_state['selected_persona'] = 'ats_bot'
    
    if 'selected_persona' in st.session_state and groq_client:
        with st.spinner("Getting feedback..."):
            feedback = get_recruiter_persona_feedback(cv_text, jd_text, st.session_state['selected_persona'], groq_client)
            if feedback: st.markdown(f'<div class="persona-card">{feedback}</div>', unsafe_allow_html=True)

feedback_loop_page()
