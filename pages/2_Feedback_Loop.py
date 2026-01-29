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

# --- PAGE CONFIG ---
st.set_page_config(page_title="Feedback Loop - Job-Search-Agent", page_icon="🔄", layout="wide")

# --- NEW ORANGE + GOLD NEON UI STYLING (HIDE SIDEBAR) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #0a0a0f !important;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* HIDE SIDEBAR */
    [data-testid="stSidebar"] { display: none !important; }
    button[kind="header"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"],
    div[data-testid="stExpanderDetails"],
    div[data-testid="stForm"] {
        background: rgba(255, 107, 53, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 107, 53, 0.15) !important;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        padding: 15px;
    }
    
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        color: #e2e8f0 !important;
        font-family: 'Outfit', sans-serif;
    }
    
    h1 {
        background: linear-gradient(90deg, #ff6b35, #f7c531);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    p, label, .stMarkdown { color: #e2e8f0 !important; }
    
    div[data-testid="stMetricValue"] { 
        color: #ff6b35 !important; 
        text-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
        font-weight: 700;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 107, 53, 0.08) !important;
        color: white !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
        border-radius: 10px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 35px rgba(255, 107, 53, 0.6);
    }
    
    .stSelectbox>div>div, .stFileUploader>div {
        background-color: rgba(255, 107, 53, 0.08) !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stProgress>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    hr { border-color: rgba(255, 107, 53, 0.2) !important; }
    
    /* Custom styles for feedback loop */
    .probability-circle {
        width: 150px; height: 150px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 2.5rem; font-weight: bold; margin: 20px auto;
        background: rgba(0,0,0,0.3);
    }
    .scan-area { padding: 15px; border-radius: 10px; margin: 10px 0; }
    .scan-high { background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10B981; }
    .scan-medium { background: rgba(245, 158, 11, 0.15); border-left: 4px solid #F59E0B; }
    .scan-low { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #EF4444; }
    .rejection-card { padding: 15px; border-radius: 10px; margin: 10px 0; }
    .rejection-high { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #EF4444; }
    .rejection-medium { background: rgba(245, 158, 11, 0.15); border-left: 4px solid #F59E0B; }
    .rejection-low { background: rgba(16, 185, 129, 0.15); border-left: 4px solid #10B981; }
    .persona-card { background: rgba(139, 92, 246, 0.1); border: 1px solid #8B5CF6; border-radius: 10px; padding: 20px; margin: 15px 0; }
    .winner-badge { background: linear-gradient(90deg, #ff6b35, #f7c531); color: black; padding: 10px 25px; border-radius: 25px; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- Configuration ---
ACCENT_ORANGE = "#ff6b35"
ACCENT_GOLD = "#f7c531"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
ACCENT_RED = "#EF4444"
ACCENT_PURPLE = "#8B5CF6"
ACCENT_CYAN = "#00E0FF"

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

try:
    supabase = init_supabase()
    groq_client = init_groq()
except:
    supabase = None
    groq_client = None

# --- Helper Functions ---

def extract_text_from_file(file):
    """Extract text from uploaded file"""
    if file is None: return ""
    try:
        if file.type == "application/pdf":
            import pypdf
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except:
        return ""

def analyze_cv_sections(cv_text):
    """Identify and score different CV sections"""
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
    """Simulate what a recruiter sees in 6 seconds"""
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
    
    attention_areas = {
        "header": {
            "text": first_impression,
            "attention": 95,
            "time_spent": "1.5s",
            "keywords_found": len([k for k in list(jd_keywords)[:10] if k in first_impression.lower()])
        },
        "skills": {
            "text": skills_text or "Not clearly defined",
            "attention": 85,
            "time_spent": "2s",
            "keywords_found": len([k for k in list(jd_keywords)[:15] if k in skills_text.lower()])
        },
        "recent_experience": {
            "text": recent_exp or "Not found",
            "attention": 75,
            "time_spent": "2s",
            "keywords_found": len([k for k in list(jd_keywords)[:15] if k in recent_exp.lower()])
        },
        "rest_of_cv": {
            "text": "Skimmed quickly",
            "attention": 20,
            "time_spent": "0.5s",
            "keywords_found": 0
        }
    }
    
    return attention_areas

def generate_rejection_reasons(cv_text, jd_text):
    """Predict specific rejection reasons"""
    reasons = []
    cv_lower = cv_text.lower()
    jd_lower = jd_text.lower()
    
    metrics = re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|months?|projects?|team|people|clients?)', cv_lower)
    if len(metrics) < 3:
        reasons.append({
            "reason": "No quantified achievements",
            "severity": "high",
            "fix": "Add metrics like '25% increase' or 'managed team of 8'"
        })
    
    years_required = re.findall(r'(\d+)\+?\s*years?', jd_lower)
    years_have = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|present)', cv_lower, re.IGNORECASE)
    
    if years_required and not years_have:
        reasons.append({
            "reason": "Experience timeline unclear",
            "severity": "medium",
            "fix": "Add clear date ranges to your work history"
        })
    
    required_skills = re.findall(r'required[:\s]+([^.]+)', jd_lower)
    if required_skills:
        req_text = required_skills[0]
        missing_count = sum(1 for word in req_text.split() if len(word) > 4 and word not in cv_lower)
        if missing_count > 3:
            reasons.append({
                "reason": f"Missing {missing_count} required skills",
                "severity": "high",
                "fix": "Add missing keywords from 'Required' section to your skills"
            })
    
    jd_titles = re.findall(r'(?:senior|junior|lead|principal|staff|manager|director|engineer|developer|analyst|specialist)\s+\w+', jd_lower)
    if jd_titles:
        title_match = any(title in cv_lower for title in jd_titles[:3])
        if not title_match:
            reasons.append({
                "reason": "Job title mismatch",
                "severity": "medium",
                "fix": f"Consider aligning your title closer to: {jd_titles[0].title()}"
            })
    
    if 'degree' in jd_lower or 'bachelor' in jd_lower or 'master' in jd_lower:
        if 'degree' not in cv_lower and 'bachelor' not in cv_lower and 'university' not in cv_lower:
            reasons.append({
                "reason": "Education requirement unclear",
                "severity": "medium",
                "fix": "Clearly list your educational qualifications"
            })
    
    if not reasons:
        reasons.append({
            "reason": "No major red flags detected",
            "severity": "low",
            "fix": "Focus on tailoring keywords for this specific role"
        })
    
    return reasons

def calculate_success_probability(cv_text, jd_text):
    """Calculate interview callback probability"""
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
    
    word_count = len(cv_text.split())
    if 300 <= word_count <= 800:
        score += 5
    
    return min(95, max(25, score))

def get_recruiter_persona_feedback(cv_text, jd_text, persona, groq_client):
    """Get feedback from different recruiter personas"""
    if not groq_client: return None
    
    persona_prompts = {
        'corporate_hr': "You are a strict Corporate HR manager at a Fortune 500 company. Focus on compliance, culture fit, and formal qualifications.",
        'startup_founder': "You are a fast-moving startup founder. Focus on adaptability, passion, and ability to wear multiple hats.",
        'ats_bot': "You are an ATS (Applicant Tracking System). Focus ONLY on keyword matches and formatting. Be robotic and precise."
    }
    
    try:
        prompt = f"""
        {persona_prompts[persona]}
        
        Review this CV for this job:
        CV: {cv_text[:1500]}
        Job: {jd_text[:1000]}
        
        Give your honest feedback in 3-4 bullet points. Be specific.
        """
        
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        return completion.choices[0].message.content
    except:
        return None

def predict_interview_questions(cv_text, jd_text, groq_client):
    """Predict likely interview questions based on gaps"""
    if not groq_client: return None
    
    try:
        prompt = f"""
        Analyze this CV against the Job Description and predict 5 tough interview questions.
        
        CV Summary: {cv_text[:2000]}
        Job Description: {jd_text[:1500]}
        
        Return as JSON:
        {{
            "questions": [
                {{"question": "...", "reason": "Why they'll ask this", "preparation_tip": "How to prepare"}}
            ]
        }}
        """
        
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        
        response = completion.choices[0].message.content
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    return None

def compare_cv_versions(cv1_text, cv2_text, jd_text):
    """A/B test two CV versions"""
    results = {
        "cv1": {"keyword_match": 0, "metrics_count": 0, "word_count": 0, "clarity_score": 0, "overall": 0},
        "cv2": {"keyword_match": 0, "metrics_count": 0, "word_count": 0, "clarity_score": 0, "overall": 0},
        "winner": "",
        "reasons": []
    }
    
    jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
    
    for cv_key, cv_text in [("cv1", cv1_text), ("cv2", cv2_text)]:
        cv_lower = cv_text.lower()
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_lower))
        
        overlap = len(jd_words.intersection(cv_words))
        results[cv_key]["keyword_match"] = overlap
        
        metrics = len(re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|projects?|team)', cv_lower))
        results[cv_key]["metrics_count"] = metrics
        results[cv_key]["word_count"] = len(cv_text.split())
        
        sentences = re.split(r'[.!?]', cv_text)
        avg_len = np.mean([len(s.split()) for s in sentences if s.strip()])
        results[cv_key]["clarity_score"] = max(0, 100 - int(avg_len * 3))
        
        results[cv_key]["overall"] = (
            results[cv_key]["keyword_match"] * 2 +
            results[cv_key]["metrics_count"] * 5 +
            results[cv_key]["clarity_score"]
        )
    
    if results["cv1"]["overall"] > results["cv2"]["overall"]:
        results["winner"] = "Version A"
    else:
        results["winner"] = "Version B"
    
    if results["cv1"]["keyword_match"] != results["cv2"]["keyword_match"]:
        better = "A" if results["cv1"]["keyword_match"] > results["cv2"]["keyword_match"] else "B"
        results["reasons"].append(f"Version {better} has better keyword alignment")
    
    if results["cv1"]["metrics_count"] != results["cv2"]["metrics_count"]:
        better = "A" if results["cv1"]["metrics_count"] > results["cv2"]["metrics_count"] else "B"
        results["reasons"].append(f"Version {better} has more quantified achievements")
    
    return results

# --- Main Page ---

def feedback_loop_page():
    # Back to Main Page button
    if st.button("← Back to Main Page", key="back_btn"):
        st.switch_page("Main_Page.py")
    
    st.markdown("---")
    
    st.markdown("""
    <h1 style="text-align: center; font-size: 2.5rem;">
        🔄 Recruiter Feedback Loop
    </h1>
    """, unsafe_allow_html=True)
    st.caption("Understand exactly why recruiters pass or proceed with your application")
    
    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to use Feedback Loop.")
        return
    
    st.markdown("---")
    
    # File Uploads
    col_cv, col_jd = st.columns(2)
    with col_cv:
        cv_file = st.file_uploader("📄 Upload your CV", type=['pdf', 'txt'], key="feedback_cv")
    with col_jd:
        jd_text = st.text_area("📋 Paste Job Description", height=150, key="feedback_jd")
    
    cv_text = ""
    if cv_file:
        cv_text = extract_text_from_file(cv_file)
    
    if not cv_text or not jd_text:
        st.info("👆 Upload your CV and paste the job description to get detailed feedback")
        return
    
    # SECTION 1: Interview Callback Probability
    st.markdown("---")
    st.subheader("1️⃣ Interview Callback Probability")
    
    probability = calculate_success_probability(cv_text, jd_text)
    
    col_prob, col_factors = st.columns([1, 2])
    
    with col_prob:
        if probability >= 70:
            color = ACCENT_GREEN
            status = "Strong Candidate"
        elif probability >= 50:
            color = ACCENT_YELLOW
            status = "Moderate Fit"
        else:
            color = ACCENT_RED
            status = "Needs Improvement"
        
        st.markdown(f"""
        <div class="probability-circle" style="border: 8px solid {color}; color: {color};">
            {probability}%
        </div>
        <p style="text-align: center; margin-top: 10px; color: {color}; font-weight: bold;">{status}</p>
        """, unsafe_allow_html=True)
    
    with col_factors:
        st.markdown("**Scoring Factors:**")
        
        jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_text.lower()))
        keyword_score = int(len(jd_words.intersection(cv_words)) / len(jd_words) * 100) if jd_words else 0
        
        metrics_count = len(re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|projects?)', cv_text.lower()))
        
        sections = analyze_cv_sections(cv_text)
        section_score = int(sum(1 for s in sections.values() if s['found']) / len(sections) * 100)
        
        st.progress(keyword_score / 100, text=f"Keyword Match: {keyword_score}%")
        st.progress(min(100, metrics_count * 15) / 100, text=f"Quantified Achievements: {metrics_count} found")
        st.progress(section_score / 100, text=f"CV Completeness: {section_score}%")

    # SECTION 2: 6-Second Scan
    st.markdown("---")
    st.subheader("2️⃣ The 6-Second Scan Simulation")
    st.caption("This is what a recruiter sees in their first pass")
    
    with st.empty():
        for i in range(6, 0, -1):
            st.markdown(f"<h3 style='text-align: center; color: {ACCENT_ORANGE};'>⏱️ {i} seconds...</h3>", unsafe_allow_html=True)
            time.sleep(0.3)
        st.markdown(f"<h3 style='text-align: center; color: {ACCENT_GREEN};'>✅ Scan Complete!</h3>", unsafe_allow_html=True)
    
    scan_results = simulate_6_second_scan(cv_text, jd_text)
    
    for area, data in scan_results.items():
        attention = data['attention']
        css_class = "scan-high" if attention >= 80 else "scan-medium" if attention >= 50 else "scan-low"
        
        st.markdown(f"""
        <div class="scan-area {css_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b>{area.replace('_', ' ').title()}</b>
                <span>👁️ {attention}% attention | ⏱️ {data['time_spent']}</span>
            </div>
            <p style="font-size: 0.85rem; color: #888; margin: 10px 0;">
                {str(data['text'])[:150]}{'...' if len(str(data['text'])) > 150 else ''}
            </p>
            <span style="color: {ACCENT_GOLD};">🎯 Keywords spotted: {data['keywords_found']}</span>
        </div>
        """, unsafe_allow_html=True)

    # SECTION 3: Rejection Reasons
    st.markdown("---")
    st.subheader("3️⃣ Rejection Reason Predictor")
    
    reasons = generate_rejection_reasons(cv_text, jd_text)
    
    for reason in reasons:
        css_class = f"rejection-{reason['severity']}"
        icon = "🔴" if reason['severity'] == 'high' else "🟡" if reason['severity'] == 'medium' else "🟢"
        
        st.markdown(f"""
        <div class="rejection-card {css_class}">
            <b>{icon} {reason['reason']}</b>
            <p style="margin: 10px 0 0 0; color: {ACCENT_GOLD};">💡 Fix: {reason['fix']}</p>
        </div>
        """, unsafe_allow_html=True)

    # SECTION 4: AI Recruiter Personas
    st.markdown("---")
    st.subheader("4️⃣ AI Recruiter Persona Simulator")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        if st.button("🏢 Corporate HR", use_container_width=True):
            st.session_state['selected_persona'] = 'corporate_hr'
    with col_p2:
        if st.button("🚀 Startup Founder", use_container_width=True):
            st.session_state['selected_persona'] = 'startup_founder'
    with col_p3:
        if st.button("🤖 ATS Bot", use_container_width=True):
            st.session_state['selected_persona'] = 'ats_bot'
    
    if 'selected_persona' in st.session_state and groq_client:
        persona = st.session_state['selected_persona']
        persona_names = {
            'corporate_hr': '🏢 Corporate HR Manager',
            'startup_founder': '🚀 Startup Founder',
            'ats_bot': '🤖 ATS Bot'
        }
        
        with st.spinner(f"Getting feedback from {persona_names[persona]}..."):
            feedback = get_recruiter_persona_feedback(cv_text, jd_text, persona, groq_client)
            
            if feedback:
                st.markdown(f"""
                <div class="persona-card">
                    <h4 style="color: {ACCENT_PURPLE};">{persona_names[persona]} Says:</h4>
                    <div style="white-space: pre-wrap;">{feedback}</div>
                </div>
                """, unsafe_allow_html=True)

    # SECTION 5: Interview Questions
    st.markdown("---")
    st.subheader("5️⃣ Predicted Interview Questions")
    
    if 'interview_questions' not in st.session_state:
        if st.button("🎯 Generate Predicted Questions", use_container_width=True):
            if groq_client:
                with st.spinner("AI is analyzing..."):
                    questions = predict_interview_questions(cv_text, jd_text, groq_client)
                    if questions:
                        st.session_state['interview_questions'] = questions
    
    if 'interview_questions' in st.session_state:
        questions = st.session_state['interview_questions']
        for i, q in enumerate(questions.get('questions', [])[:5], 1):
            with st.expander(f"❓ Question {i}: {q.get('question', 'N/A')}", expanded=(i==1)):
                st.warning(f"**Why they'll ask:** {q.get('reason', 'N/A')}")
                st.success(f"**Preparation tip:** {q.get('preparation_tip', 'N/A')}")

    st.markdown("---")
    st.caption("💡 Tip: Re-run analysis after making changes to track improvements")

# Run the page
feedback_loop_page()
