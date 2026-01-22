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
    
    # Extract key JD requirements
    jd_keywords = set(re.findall(r'\b\w{4,}\b', jd_lower))
    stop_words = {'with', 'have', 'that', 'this', 'will', 'your', 'from', 'they', 'been', 'were', 'their', 'what', 'when', 'where', 'which', 'while', 'about', 'after', 'before', 'being', 'between', 'both', 'each', 'would', 'could', 'should', 'through'}
    jd_keywords = jd_keywords - stop_words
    
    # First 200 chars (name, title area)
    first_impression = cv_text[:200]
    
    # Skills section detection
    skills_match = re.search(r'skills?[:\s]+(.*?)(?:\n\n|\Z)', cv_text, re.IGNORECASE | re.DOTALL)
    skills_text = skills_match.group(1)[:300] if skills_match else ""
    
    # Recent experience (first job)
    exp_match = re.search(r'experience[:\s]+(.*?)(?:\n\n|\Z)', cv_text, re.IGNORECASE | re.DOTALL)
    recent_exp = exp_match.group(1)[:400] if exp_match else ""
    
    # Calculate attention scores
    attention_areas = {
        "header": {
            "text": first_impression,
            "attention": 95,  # Always looked at
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
    
    # 1. Check for quantified achievements
    metrics = re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|months?|projects?|team|people|clients?)', cv_lower)
    if len(metrics) < 3:
        reasons.append({
            "reason": "No quantified achievements",
            "severity": "high",
            "fix": "Add metrics like '25% increase' or 'managed team of 8'"
        })
    
    # 2. Check years of experience
    years_required = re.findall(r'(\d+)\+?\s*years?', jd_lower)
    years_have = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|present)', cv_lower, re.IGNORECASE)
    
    if years_required and not years_have:
        reasons.append({
            "reason": "Experience timeline unclear",
            "severity": "medium",
            "fix": "Add clear date ranges to your work history"
        })
    
    # 3. Check for required skills
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
    
    # 4. Job title mismatch
    jd_titles = re.findall(r'(?:senior|junior|lead|principal|staff|manager|director|engineer|developer|analyst|specialist)\s+\w+', jd_lower)
    if jd_titles:
        title_match = any(title in cv_lower for title in jd_titles[:3])
        if not title_match:
            reasons.append({
                "reason": "Job title mismatch",
                "severity": "medium",
                "fix": f"Consider aligning your title closer to: {jd_titles[0].title()}"
            })
    
    # 5. Education check
    if 'degree' in jd_lower or 'bachelor' in jd_lower or 'master' in jd_lower:
        if 'degree' not in cv_lower and 'bachelor' not in cv_lower and 'university' not in cv_lower:
            reasons.append({
                "reason": "Education requirement unclear",
                "severity": "medium",
                "fix": "Clearly list your educational qualifications"
            })
    
    # 6. Employment gaps
    # Simplified check
    if 'gap' in cv_lower or len(years_have) > 0:
        for i in range(len(years_have) - 1):
            try:
                end_year = int(years_have[i][1]) if years_have[i][1].lower() != 'present' else 2026
                start_next = int(years_have[i+1][0])
                if start_next - end_year > 1:
                    reasons.append({
                        "reason": f"Employment gap detected (~{start_next - end_year} years)",
                        "severity": "medium",
                        "fix": "Add explanation for career breaks (education, freelance, etc.)"
                    })
                    break
            except:
                pass
    
    if not reasons:
        reasons.append({
            "reason": "No major red flags detected",
            "severity": "low",
            "fix": "Focus on tailoring keywords for this specific role"
        })
    
    return reasons

def calculate_success_probability(cv_text, jd_text):
    """Calculate interview callback probability"""
    score = 50  # Base score
    
    cv_lower = cv_text.lower()
    jd_lower = jd_text.lower()
    
    # Keyword match
    jd_words = set(re.findall(r'\b\w{4,}\b', jd_lower))
    cv_words = set(re.findall(r'\b\w{4,}\b', cv_lower))
    overlap = len(jd_words.intersection(cv_words)) / len(jd_words) if jd_words else 0
    score += int(overlap * 30)
    
    # Metrics presence
    metrics = len(re.findall(r'\d+%|\$\d+[KMB]?|\d+\s*(?:years?|projects?)', cv_lower))
    score += min(10, metrics * 2)
    
    # Section completeness
    sections = analyze_cv_sections(cv_text)
    complete_sections = sum(1 for s in sections.values() if s['found'])
    score += complete_sections * 2
    
    # Length check (not too short, not too long)
    word_count = len(cv_text.split())
    if 300 <= word_count <= 800:
        score += 5
    
    return min(95, max(25, score))

def predict_interview_questions(cv_text, jd_text, groq_client):
    """Predict likely interview questions based on gaps"""
    if not groq_client:
        return None
    
    try:
        prompt = f"""
        Analyze this CV against the Job Description and predict 5 tough interview questions 
        the recruiter will likely ask based on gaps or weak areas.
        
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
        "cv1": {
            "keyword_match": 0,
            "metrics_count": 0,
            "word_count": 0,
            "clarity_score": 0,
            "overall": 0
        },
        "cv2": {
            "keyword_match": 0,
            "metrics_count": 0,
            "word_count": 0,
            "clarity_score": 0,
            "overall": 0
        },
        "winner": "",
        "reasons": []
    }
    
    jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
    
    for cv_key, cv_text in [("cv1", cv1_text), ("cv2", cv2_text)]:
        cv_lower = cv_text.lower()
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_lower))
        
        # Keyword match
        overlap = len(jd_words.intersection(cv_words))
        results[cv_key]["keyword_match"] = overlap
        
        # Metrics
        metrics = len(re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|projects?|team)', cv_lower))
        results[cv_key]["metrics_count"] = metrics
        
        # Word count
        results[cv_key]["word_count"] = len(cv_text.split())
        
        # Simple clarity (shorter sentences = clearer)
        sentences = re.split(r'[.!?]', cv_text)
        avg_len = np.mean([len(s.split()) for s in sentences if s.strip()])
        results[cv_key]["clarity_score"] = max(0, 100 - int(avg_len * 3))
        
        # Overall
        results[cv_key]["overall"] = (
            results[cv_key]["keyword_match"] * 2 +
            results[cv_key]["metrics_count"] * 5 +
            results[cv_key]["clarity_score"]
        )
    
    # Determine winner
    if results["cv1"]["overall"] > results["cv2"]["overall"]:
        results["winner"] = "Version A"
        diff = results["cv1"]["overall"] - results["cv2"]["overall"]
    else:
        results["winner"] = "Version B"
        diff = results["cv2"]["overall"] - results["cv1"]["overall"]
    
    # Generate reasons
    if results["cv1"]["keyword_match"] != results["cv2"]["keyword_match"]:
        better = "A" if results["cv1"]["keyword_match"] > results["cv2"]["keyword_match"] else "B"
        results["reasons"].append(f"Version {better} has better keyword alignment")
    
    if results["cv1"]["metrics_count"] != results["cv2"]["metrics_count"]:
        better = "A" if results["cv1"]["metrics_count"] > results["cv2"]["metrics_count"] else "B"
        results["reasons"].append(f"Version {better} has more quantified achievements")
    
    if abs(results["cv1"]["clarity_score"] - results["cv2"]["clarity_score"]) > 10:
        better = "A" if results["cv1"]["clarity_score"] > results["cv2"]["clarity_score"] else "B"
        results["reasons"].append(f"Version {better} is more readable")
    
    return results

def get_recruiter_persona_feedback(cv_text, jd_text, persona, groq_client):
    """Get feedback from different recruiter personas"""
    if not groq_client:
        return None
    
    persona_prompts = {
        "corporate_hr": """
            You are a Corporate HR Manager at a Fortune 500 company. You value:
            - Structured career progression
            - Formal qualifications and certifications
            - Stable employment history
            - Cultural fit indicators
            Be formal and process-oriented in your feedback.
        """,
        "startup_founder": """
            You are a Startup Founder/CEO. You value:
            - Hustle and side projects
            - Diverse skill sets
            - Speed of learning
            - Cultural energy and passion
            Be casual, direct, and focus on potential over credentials.
        """,
        "ats_bot": """
            You are an Applicant Tracking System (ATS). You ONLY care about:
            - Exact keyword matches from the job description
            - Standard formatting
            - Specific technical skills mentioned
            Be robotic and purely data-driven. List match percentages.
        """
    }
    
    try:
        prompt = f"""
        {persona_prompts.get(persona, persona_prompts['corporate_hr'])}
        
        Review this CV for the following role and provide your honest assessment.
        
        JOB: {jd_text[:1000]}
        
        CV: {cv_text[:2500]}
        
        Provide:
        1. Your initial impression (2 sentences)
        2. Top 3 strengths you noticed
        3. Top 3 concerns/red flags
        4. Would you move forward? (Yes/Maybe/No) and why
        5. One specific tip to improve
        
        Stay in character throughout.
        """
        
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        
        return completion.choices[0].message.content
    except:
        return None

# --- Page Styling ---
def inject_custom_css():
    st.markdown(f"""
    <style>
    .scan-area {{
        border: 2px solid {ACCENT_CYAN}40;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        position: relative;
    }}
    .scan-high {{ border-color: {ACCENT_GREEN}; background: {ACCENT_GREEN}10; }}
    .scan-medium {{ border-color: {ACCENT_YELLOW}; background: {ACCENT_YELLOW}10; }}
    .scan-low {{ border-color: {ACCENT_RED}10; background: transparent; }}
    .rejection-card {{
        border-left: 4px solid;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }}
    .rejection-high {{ border-color: {ACCENT_RED}; background: {ACCENT_RED}15; }}
    .rejection-medium {{ border-color: {ACCENT_YELLOW}; background: {ACCENT_YELLOW}15; }}
    .rejection-low {{ border-color: {ACCENT_GREEN}; background: {ACCENT_GREEN}15; }}
    .probability-circle {{
        width: 150px;
        height: 150px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0 auto;
    }}
    .persona-card {{
        background: {BG_DARK};
        border: 1px solid {ACCENT_PURPLE}40;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
    }}
    .winner-badge {{
        background: linear-gradient(135deg, {ACCENT_GREEN}, {ACCENT_CYAN});
        color: black;
        padding: 5px 20px;
        border-radius: 20px;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Main Page ---
def feedback_loop_page():
    inject_custom_css()
    
    st.markdown(f'<h1 style="color:{ACCENT_ORANGE}; text-align: center;">🔄 Predictive Feedback Loop</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; color: {ACCENT_CYAN};">See Your CV Through a Recruiter\'s Eyes</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Auth Check
    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to access the Feedback Loop.")
        return

    # =====================================================
    # INPUT SECTION
    # =====================================================
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
        if jd_text:
            st.session_state['feedback_jd_text'] = jd_text

    if not cv_text or not jd_text:
        st.info("👆 Upload your CV and paste a Job Description to begin analysis")
        return

    # Run Analysis Button
    if st.button("🔍 Run Complete Analysis", type="primary", use_container_width=True):
        st.session_state['run_feedback_analysis'] = True

    if not st.session_state.get('run_feedback_analysis'):
        return

    st.markdown("---")

    # =====================================================
    # SECTION 1: Success Probability
    # =====================================================
    st.subheader("1️⃣ Interview Callback Probability")
    
    probability = calculate_success_probability(cv_text, jd_text)
    
    col_prob, col_factors = st.columns([1, 2])
    
    with col_prob:
        if probability >= 70:
            color = ACCENT_GREEN
            status = "Strong Candidate"
        elif probability >= 50:
            color = ACCENT_YELLOW
            status = "Competitive"
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
        
        # Calculate individual factors
        jd_words = set(re.findall(r'\b\w{4,}\b', jd_text.lower()))
        cv_words = set(re.findall(r'\b\w{4,}\b', cv_text.lower()))
        keyword_score = int(len(jd_words.intersection(cv_words)) / len(jd_words) * 100) if jd_words else 0
        
        metrics_count = len(re.findall(r'\d+%|\$\d+|\d+\s*(?:years?|projects?)', cv_text.lower()))
        
        sections = analyze_cv_sections(cv_text)
        section_score = int(sum(1 for s in sections.values() if s['found']) / len(sections) * 100)
        
        st.progress(keyword_score / 100, text=f"Keyword Match: {keyword_score}%")
        st.progress(min(100, metrics_count * 15) / 100, text=f"Quantified Achievements: {metrics_count} found")
        st.progress(section_score / 100, text=f"CV Completeness: {section_score}%")

    # =====================================================
    # SECTION 2: 6-Second Scan Simulation
    # =====================================================
    st.markdown("---")
    st.subheader("2️⃣ The 6-Second Scan Simulation")
    st.caption("This is what a recruiter sees in their first pass of your CV")
    
    # Animated countdown
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
                {data['text'][:150]}{'...' if len(str(data['text'])) > 150 else ''}
            </p>
            <span style="color: {ACCENT_CYAN};">🎯 Keywords spotted: {data['keywords_found']}</span>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # SECTION 3: Rejection Reason Predictor
    # =====================================================
    st.markdown("---")
    st.subheader("3️⃣ Rejection Reason Predictor")
    st.caption("Common reasons recruiters might pass on your application")
    
    reasons = generate_rejection_reasons(cv_text, jd_text)
    
    for reason in reasons:
        css_class = f"rejection-{reason['severity']}"
        icon = "🔴" if reason['severity'] == 'high' else "🟡" if reason['severity'] == 'medium' else "🟢"
        
        st.markdown(f"""
        <div class="rejection-card {css_class}">
            <b>{icon} {reason['reason']}</b>
            <p style="margin: 10px 0 0 0; color: {ACCENT_CYAN};">💡 Fix: {reason['fix']}</p>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # SECTION 4: AI Recruiter Personas
    # =====================================================
    st.markdown("---")
    st.subheader("4️⃣ AI Recruiter Persona Simulator")
    st.caption("Get feedback from different recruiter perspectives")
    
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

    # =====================================================
    # SECTION 5: Interview Question Predictor
    # =====================================================
    st.markdown("---")
    st.subheader("5️⃣ Predicted Interview Questions")
    st.caption("Based on gaps between your CV and the job requirements")
    
    if 'interview_questions' not in st.session_state:
        if st.button("🎯 Generate Predicted Questions", use_container_width=True):
            if groq_client:
                with st.spinner("AI is analyzing potential interview questions..."):
                    questions = predict_interview_questions(cv_text, jd_text, groq_client)
                    if questions:
                        st.session_state['interview_questions'] = questions
    
    if 'interview_questions' in st.session_state:
        questions = st.session_state['interview_questions']
        for i, q in enumerate(questions.get('questions', [])[:5], 1):
            with st.expander(f"❓ Question {i}: {q.get('question', 'N/A')}", expanded=(i==1)):
                st.warning(f"**Why they'll ask:** {q.get('reason', 'N/A')}")
                st.success(f"**Preparation tip:** {q.get('preparation_tip', 'N/A')}")

    # =====================================================
    # SECTION 6: A/B CV Tester
    # =====================================================
    st.markdown("---")
    st.subheader("6️⃣ A/B CV Version Tester")
    st.caption("Compare two versions of your CV to find the winner")
    
    with st.expander("📊 Open A/B Tester", expanded=False):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("**Version A (Current)**")
            cv_a = st.text_area("Paste CV Version A", value=cv_text[:1500], height=200, key="cv_version_a")
        
        with col_b:
            st.markdown("**Version B (Alternative)**")
            cv_b = st.text_area("Paste CV Version B", height=200, key="cv_version_b")
        
        if st.button("⚔️ Compare Versions", use_container_width=True):
            if cv_a and cv_b:
                comparison = compare_cv_versions(cv_a, cv_b, jd_text)
                
                st.markdown(f"""
                <div style="text-align: center; margin: 20px 0;">
                    <span class="winner-badge">🏆 Winner: {comparison['winner']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col_res_a, col_res_b = st.columns(2)
                
                with col_res_a:
                    st.metric("Version A Score", comparison['cv1']['overall'])
                    st.caption(f"Keywords: {comparison['cv1']['keyword_match']} | Metrics: {comparison['cv1']['metrics_count']}")
                
                with col_res_b:
                    st.metric("Version B Score", comparison['cv2']['overall'])
                    st.caption(f"Keywords: {comparison['cv2']['keyword_match']} | Metrics: {comparison['cv2']['metrics_count']}")
                
                if comparison['reasons']:
                    st.markdown("**Why this version won:**")
                    for reason in comparison['reasons']:
                        st.markdown(f"- {reason}")
            else:
                st.warning("Please paste both CV versions")

    st.markdown("---")
    st.caption("💡 Tip: Re-run analysis after making changes to track improvements")

# Run the page
feedback_loop_page()
