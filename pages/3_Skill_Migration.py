import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import os
import json

# --- Configuration ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_PURPLE = "#8B5CF6"
ACCENT_BLUE = "#3B82F6"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    def get_secret(key):
        if key in os.environ:
            return os.environ[key]
        try:
            return st.secrets[key]
        except:
            return None

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key: return None
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    supabase = None

# --- Industry Detection ---
def detect_industry(report, cv_text=""):
    """Detect the industry from the CV analysis report"""
    
    # Keywords for different industries
    industries = {
        'healthcare': ['care', 'patient', 'health', 'medical', 'nursing', 'clinical', 'empathy', 
                      'compassion', 'carer', 'nurse', 'hospital', 'elderly', 'disability', 'support worker'],
        'technology': ['python', 'java', 'cloud', 'aws', 'coding', 'programming', 'software', 
                      'data', 'machine learning', 'developer', 'engineer', 'devops', 'api'],
        'finance': ['accounting', 'finance', 'banking', 'investment', 'audit', 'tax', 'financial'],
        'education': ['teacher', 'teaching', 'education', 'school', 'tutor', 'curriculum', 'student'],
        'retail': ['sales', 'retail', 'customer service', 'shop', 'store', 'merchandise'],
        'hospitality': ['hotel', 'restaurant', 'chef', 'hospitality', 'catering', 'tourism']
    }
    
    # Check weakest_link_skill and full report
    report_text = str(report).lower() + " " + cv_text.lower()
    
    for industry, keywords in industries.items():
        if any(kw in report_text for kw in keywords):
            return industry
    
    return 'general'

# --- Career Paths Data ---
def get_career_paths(industry):
    """Return career paths based on detected industry"""
    
    paths = {
        'healthcare': {
            'title': '🏥 Healthcare & Care Industry Paths',
            'careers': [
                {
                    'name': 'Senior Care Worker',
                    'target': 'Team Leader / Supervisor',
                    'success_rate': '85%',
                    'timeline': '~6-12 months',
                    'color': '#10B981'
                },
                {
                    'name': 'Care Coordinator',
                    'target': 'Care Manager / Director',
                    'success_rate': '70%',
                    'timeline': '~12-18 months',
                    'color': '#3B82F6'
                },
                {
                    'name': 'Healthcare Assistant',
                    'target': 'Registered Nurse (with training)',
                    'success_rate': '60%',
                    'timeline': '~2-3 years',
                    'color': '#8B5CF6'
                }
            ],
            'skills': ['Patient Care', 'Communication', 'First Aid/CPR', 'Documentation', 'Empathy', 'Time Management'],
            'demands': [90, 85, 80, 75, 95, 70]
        },
        'technology': {
            'title': '💻 Technology Industry Paths',
            'careers': [
                {
                    'name': 'Management Track',
                    'target': 'Engineering Manager / Director',
                    'success_rate': '90%',
                    'timeline': '~8 months',
                    'color': '#10B981'
                },
                {
                    'name': 'Technical Leadership',
                    'target': 'Tech Lead / Principal Engineer',
                    'success_rate': '60%',
                    'timeline': '~10 months',
                    'color': '#3B82F6'
                },
                {
                    'name': 'Domain Expert',
                    'target': 'Consultant / Advisor',
                    'success_rate': '55%',
                    'timeline': '~12 months',
                    'color': '#8B5CF6'
                }
            ],
            'skills': ['Python', 'Cloud/AWS', 'Machine Learning', 'Leadership', 'Communication', 'Agile/Scrum'],
            'demands': [90, 88, 85, 75, 80, 75]
        },
        'finance': {
            'title': '💰 Finance & Accounting Paths',
            'careers': [
                {
                    'name': 'Senior Accountant',
                    'target': 'Finance Manager',
                    'success_rate': '80%',
                    'timeline': '~12 months',
                    'color': '#10B981'
                },
                {
                    'name': 'Financial Analyst',
                    'target': 'Senior Analyst / Director',
                    'success_rate': '65%',
                    'timeline': '~18 months',
                    'color': '#3B82F6'
                },
                {
                    'name': 'Audit Associate',
                    'target': 'Audit Manager / Partner',
                    'success_rate': '55%',
                    'timeline': '~3-5 years',
                    'color': '#8B5CF6'
                }
            ],
            'skills': ['Financial Analysis', 'Excel/Modeling', 'Accounting Standards', 'Communication', 'Attention to Detail', 'Regulatory Knowledge'],
            'demands': [90, 85, 80, 75, 88, 70]
        },
        'education': {
            'title': '📚 Education Industry Paths',
            'careers': [
                {
                    'name': 'Senior Teacher',
                    'target': 'Head of Department',
                    'success_rate': '75%',
                    'timeline': '~2-3 years',
                    'color': '#10B981'
                },
                {
                    'name': 'Curriculum Specialist',
                    'target': 'Academic Director',
                    'success_rate': '60%',
                    'timeline': '~3-4 years',
                    'color': '#3B82F6'
                },
                {
                    'name': 'Education Coordinator',
                    'target': 'School Administrator',
                    'success_rate': '50%',
                    'timeline': '~4-5 years',
                    'color': '#8B5CF6'
                }
            ],
            'skills': ['Teaching Methods', 'Curriculum Design', 'Student Engagement', 'Communication', 'Technology Integration', 'Assessment'],
            'demands': [85, 80, 90, 85, 75, 70]
        },
        'general': {
            'title': '🎯 Career Progression Paths',
            'careers': [
                {
                    'name': 'Senior Role',
                    'target': 'Team Lead / Supervisor',
                    'success_rate': '80%',
                    'timeline': '~6-12 months',
                    'color': '#10B981'
                },
                {
                    'name': 'Specialist Track',
                    'target': 'Subject Matter Expert',
                    'success_rate': '65%',
                    'timeline': '~12-18 months',
                    'color': '#3B82F6'
                },
                {
                    'name': 'Management Track',
                    'target': 'Department Manager',
                    'success_rate': '55%',
                    'timeline': '~2-3 years',
                    'color': '#8B5CF6'
                }
            ],
            'skills': ['Communication', 'Leadership', 'Problem Solving', 'Time Management', 'Teamwork', 'Adaptability'],
            'demands': [85, 80, 90, 75, 85, 80]
        }
    }
    
    return paths.get(industry, paths['general'])

def fetch_latest_report():
    """Retrieves the latest analysis report from Supabase"""
    user_id = st.session_state.get('user_id')
    if not user_id or not supabase: return None
    try:
        response = supabase.table("analyses").select("report_json")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        if response.data:
            raw_json = response.data[0]['report_json']
            if isinstance(raw_json, str):
                return json.loads(raw_json)
            return raw_json
    except Exception as e:
        st.error(f"Database Error: {e}")
    return None

# --- Page Render ---
def skill_migration_page():
    st.markdown(f'<h1 style="color:{ACCENT_ORANGE}; text-align: center;">🌍 Skill Migration Map</h1>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to view your skill migration map.")
        return

    # Data Loading
    report = st.session_state.get('skill_gap_report')
    if not report:
        with st.spinner("Fetching latest profile data from cloud..."):
            report = fetch_latest_report()
            if report:
                st.session_state['skill_gap_report'] = report
    
    if not report:
        st.info("👋 No analysis found. Go to the Dashboard to run an analysis.")
        return

    # Detect Industry
    cv_text = st.session_state.get('cv_text_to_process', '')
    industry = detect_industry(report, cv_text)
    career_data = get_career_paths(industry)
    
    # --- Section 1: Score Overview ---
    st.subheader("1️⃣ Your Profile Scores")
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

    st.markdown("---")
    
    # --- Section 2: Career Trajectory Paths ---
    st.subheader(f"2️⃣ {career_data['title']}")
    st.caption("Click on paths to explore required skills and timelines")
    
    col1, col2, col3 = st.columns(3)
    
    for i, career in enumerate(career_data['careers']):
        with [col1, col2, col3][i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {career['color']}, {career['color']}99); 
                        padding: 20px; border-radius: 12px; height: 180px; margin-bottom: 10px;">
                <h4 style="color: white; margin: 0 0 10px 0;">{career['name']}</h4>
                <p style="color: rgba(255,255,255,0.8); font-size: 0.9em; margin: 5px 0;">→ {career['target']}</p>
                <p style="color: white; font-weight: bold; margin: 10px 0;">{career['success_rate']} success rate</p>
                <p style="color: rgba(255,255,255,0.7); font-size: 0.8em; margin: 0;">{career['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Section 3: Market Demand vs Your Skills ---
    st.subheader("3️⃣ Market Demand vs Your Skills")
    
    skills = career_data['skills']
    demands = career_data['demands']
    your_levels = [report.get('tech_score', 50) + (i * 5 - 10) for i in range(len(skills))]  # Simulated variation
    your_levels = [max(10, min(100, level)) for level in your_levels]  # Clamp values
    
    fig = go.Figure(data=[
        go.Bar(name='Market Demand', x=skills, y=demands, marker_color=ACCENT_CYAN),
        go.Bar(name='Your Level', x=skills, y=your_levels, marker_color=ACCENT_ORANGE)
    ])
    fig.update_layout(
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # --- Section 4: Skill Gap Analysis ---
    st.subheader("4️⃣ Skill Gap Analysis")
    
    for i, skill in enumerate(skills):
        gap = demands[i] - your_levels[i]
        if gap > 0:
            color = ACCENT_ORANGE if gap > 30 else ACCENT_GREEN
            st.markdown(f"""
            <div style="background: rgba(255,140,0,0.1); border-left: 4px solid {color}; 
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong>{skill}:</strong> {gap}% gap - {'High priority to improve ↑' if gap > 30 else 'Moderate gap'}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(16,185,129,0.1); border-left: 4px solid {ACCENT_GREEN}; 
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <span style="color: {ACCENT_GREEN};"><strong>{skill}:</strong> You exceed market demand! →</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info(f"🔍 **Detected Industry:** {industry.title()} | 💡 Upload a new CV on Dashboard for updated analysis")

skill_migration_page()
