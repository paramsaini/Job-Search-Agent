import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from groq import Groq
import os
import json
import numpy as np
from datetime import datetime, timedelta

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

def fetch_latest_report(user_id):
    """Fetch user's latest skill analysis from DB"""
    if not supabase or not user_id: return None
    try:
        response = supabase.table("analyses").select("report_json")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(1).execute()
        if response.data:
            raw = response.data[0]['report_json']
            return json.loads(raw) if isinstance(raw, str) else raw
    except: pass
    return None

def get_career_trajectories(current_tech, current_leader):
    """Generate possible career paths based on current scores"""
    trajectories = []
    
    # Technical Track
    if current_tech >= 60:
        trajectories.append({
            "path": "Technical Specialist",
            "target_role": "Senior Engineer / Architect",
            "tech_needed": 90, "leader_needed": 50,
            "probability": min(95, current_tech + 15),
            "time_months": max(6, (90 - current_tech) // 5),
            "color": ACCENT_CYAN
        })
    
    # Leadership Track
    if current_leader >= 50:
        trajectories.append({
            "path": "Management Track",
            "target_role": "Engineering Manager / Director",
            "tech_needed": 65, "leader_needed": 85,
            "probability": min(90, current_leader + 20),
            "time_months": max(8, (85 - current_leader) // 4),
            "color": ACCENT_GREEN
        })
    
    # Hybrid Track
    trajectories.append({
        "path": "Technical Leadership",
        "target_role": "Tech Lead / Principal Engineer",
        "tech_needed": 80, "leader_needed": 70,
        "probability": min(85, (current_tech + current_leader) // 2 + 10),
        "time_months": max(10, ((80 - current_tech) + (70 - current_leader)) // 6),
        "color": ACCENT_PURPLE
    })
    
    # Consulting Track
    trajectories.append({
        "path": "Domain Expert",
        "target_role": "Consultant / Advisor",
        "tech_needed": 75, "leader_needed": 75,
        "probability": min(80, (current_tech + current_leader) // 2 + 5),
        "time_months": max(12, ((75 - current_tech) + (75 - current_leader)) // 5),
        "color": ACCENT_ORANGE
    })
    
    return trajectories

def generate_90_day_plan(weakest_skill, groq_client):
    """Generate AI-powered 90-day learning sprint"""
    if not groq_client or not weakest_skill:
        return None
    
    try:
        prompt = f"""
        Create a 90-day skill development sprint for improving: {weakest_skill}
        
        Format your response as JSON with this exact structure:
        {{
            "skill": "{weakest_skill}",
            "weeks": [
                {{
                    "week": 1,
                    "theme": "Foundation",
                    "tasks": ["Task 1", "Task 2", "Task 3"],
                    "resources": ["Free resource link/name"],
                    "milestone": "What to achieve"
                }}
            ],
            "certifications": ["Relevant certification 1", "Certification 2"],
            "projects": ["Portfolio project idea 1", "Project idea 2"]
        }}
        
        Provide exactly 12 weeks (covering 90 days). Make tasks specific and actionable.
        Include real free resources like Coursera, YouTube channels, documentation.
        """
        
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        
        response_text = completion.choices[0].message.content
        # Extract JSON from response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response_text[start:end])
    except Exception as e:
        st.error(f"Plan generation error: {e}")
    return None

def get_market_demand_data(tech_score, leader_score):
    """Simulate market demand data based on skills"""
    skills_data = [
        {"skill": "Python", "demand": 92, "your_level": min(100, tech_score + 10), "trend": "↑"},
        {"skill": "Cloud/AWS", "demand": 88, "your_level": min(100, tech_score - 5), "trend": "↑"},
        {"skill": "Machine Learning", "demand": 85, "your_level": min(100, tech_score - 15), "trend": "↑"},
        {"skill": "Leadership", "demand": 78, "your_level": leader_score, "trend": "→"},
        {"skill": "Communication", "demand": 82, "your_level": min(100, leader_score + 5), "trend": "↑"},
        {"skill": "Agile/Scrum", "demand": 75, "your_level": min(100, (tech_score + leader_score) // 2), "trend": "→"},
    ]
    return pd.DataFrame(skills_data)

def get_peer_comparison(tech_score, leader_score):
    """Generate peer comparison percentiles"""
    # Simulate based on normal distribution assumptions
    tech_percentile = min(99, max(1, int(50 + (tech_score - 65) * 1.5)))
    leader_percentile = min(99, max(1, int(50 + (leader_score - 60) * 1.5)))
    overall_percentile = min(99, max(1, (tech_percentile + leader_percentile) // 2))
    
    return {
        "technical": tech_percentile,
        "leadership": leader_percentile,
        "overall": overall_percentile
    }

def get_skill_decay_warnings(report):
    """Identify skills that may need refreshing"""
    warnings = []
    tech_score = report.get('tech_score', 50)
    leader_score = report.get('leader_score', 50)
    
    if tech_score < 60:
        warnings.append({
            "skill": "Technical Foundations",
            "severity": "high" if tech_score < 45 else "medium",
            "message": "Your technical skills need immediate attention",
            "action": "Complete 2 coding challenges weekly"
        })
    
    if leader_score < 50:
        warnings.append({
            "skill": "Leadership & Communication",
            "severity": "medium",
            "message": "Leadership skills below market average",
            "action": "Lead a small project or mentor someone"
        })
    
    # Add weakest link warning
    weakest = report.get('weakest_link_skill', 'Unknown')
    if weakest and weakest != 'N/A':
        warnings.append({
            "skill": weakest,
            "severity": "high",
            "message": f"'{weakest}' identified as your critical gap",
            "action": "Prioritize this in your 90-day sprint"
        })
    
    return warnings

# --- Page Styling ---
def inject_custom_css():
    st.markdown(f"""
    <style>
    .metric-card {{
        background: linear-gradient(135deg, {BG_DARK}, #1e293b);
        border: 1px solid {ACCENT_CYAN}40;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 224, 255, 0.1);
    }}
    .trajectory-card {{
        background: linear-gradient(135deg, {BG_DARK}, #1e1b4b);
        border-left: 4px solid;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }}
    .warning-high {{ border-left: 4px solid {ACCENT_RED}; background: {ACCENT_RED}15; }}
    .warning-medium {{ border-left: 4px solid {ACCENT_YELLOW}; background: {ACCENT_YELLOW}15; }}
    .sprint-week {{
        background: {BG_DARK};
        border: 1px solid {ACCENT_PURPLE}40;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
    }}
    .percentile-badge {{
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1.1rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Main Page ---
def skill_migration_page():
    inject_custom_css()
    
    st.markdown(f'<h1 style="color:{ACCENT_ORANGE}; text-align: center;">🚀 Skill Migration Command Center</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; color: {ACCENT_CYAN};">Your AI-Powered Career Transformation Hub</p>', unsafe_allow_html=True)
    st.markdown("---")

    # Auth Check
    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to access your Skill Migration Center.")
        return

    # Load Data
    report = st.session_state.get('skill_gap_report') or fetch_latest_report(st.session_state.user_id)
    
    if not report:
        st.info("👋 No analysis found. Go to Dashboard and run 'Generate Strategy' first.")
        return
    
    # Store for other components
    st.session_state['skill_gap_report'] = report
    
    tech_score = report.get('tech_score', 50)
    leader_score = report.get('leader_score', 50)
    predictive_score = report.get('predictive_score', 60)
    weakest_skill = report.get('weakest_link_skill', 'Unknown')

    # =====================================================
    # SECTION 1: Current Status Dashboard
    # =====================================================
    st.subheader("1️⃣ Current Skill Profile")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 Predictive Match", f"{predictive_score}%", 
                  delta="Good" if predictive_score >= 70 else "Needs Work")
        st.progress(predictive_score / 100)
    
    with col2:
        st.metric("💻 Technical Depth", f"{tech_score}%",
                  delta="Strong" if tech_score >= 70 else "Build Up")
        st.progress(tech_score / 100)
    
    with col3:
        st.metric("👥 Leadership Score", f"{leader_score}%",
                  delta="Solid" if leader_score >= 60 else "Develop")
        st.progress(leader_score / 100)
    
    with col4:
        st.error(f"⚠️ Weakest Link")
        st.markdown(f"**{weakest_skill}**")
        st.caption("Focus your learning here")

    # =====================================================
    # SECTION 2: Career Trajectory Visualizer
    # =====================================================
    st.markdown("---")
    st.subheader("2️⃣ Career Trajectory Paths")
    st.caption("Click on paths to explore required skills and timelines")
    
    trajectories = get_career_trajectories(tech_score, leader_score)
    
    # Sankey Diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20,
            line=dict(color="black", width=0.5),
            label=["Your Current Profile", "Technical Track", "Leadership Track", 
                   "Hybrid Track", "Consulting Track",
                   "Senior Engineer", "Engineering Manager", 
                   "Tech Lead", "Consultant"],
            color=[ACCENT_CYAN, ACCENT_CYAN, ACCENT_GREEN, 
                   ACCENT_PURPLE, ACCENT_ORANGE,
                   ACCENT_CYAN, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE]
        ),
        link=dict(
            source=[0, 0, 0, 0, 1, 2, 3, 4],
            target=[1, 2, 3, 4, 5, 6, 7, 8],
            value=[tech_score, leader_score, (tech_score+leader_score)//2, 
                   (tech_score+leader_score)//2, tech_score, leader_score,
                   (tech_score+leader_score)//2, (tech_score+leader_score)//2],
            color=["rgba(0, 224, 255, 0.4)", "rgba(16, 185, 129, 0.4)", 
                   "rgba(139, 92, 246, 0.4)", "rgba(255, 140, 0, 0.4)",
                   "rgba(0, 224, 255, 0.25)", "rgba(16, 185, 129, 0.25)",
                   "rgba(139, 92, 246, 0.25)", "rgba(255, 140, 0, 0.25)"]
        )
    )])
    fig_sankey.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', size=12),
        height=350,
        margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)
    
    # Trajectory Cards
    cols = st.columns(len(trajectories))
    for i, traj in enumerate(trajectories):
        with cols[i]:
            st.markdown(f"""
            <div class="trajectory-card" style="border-color: {traj['color']};">
                <h4 style="color: {traj['color']}; margin: 0;">{traj['path']}</h4>
                <p style="margin: 5px 0; font-size: 0.9rem;">→ {traj['target_role']}</p>
                <p style="margin: 5px 0;"><b>{traj['probability']}%</b> success rate</p>
                <p style="margin: 0; font-size: 0.85rem; color: #888;">~{traj['time_months']} months</p>
            </div>
            """, unsafe_allow_html=True)

    # =====================================================
    # SECTION 3: Peer Comparison
    # =====================================================
    st.markdown("---")
    st.subheader("3️⃣ Peer Comparison (Anonymous)")
    
    peer_data = get_peer_comparison(tech_score, leader_score)
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    with col_p1:
        color = ACCENT_GREEN if peer_data['technical'] >= 60 else ACCENT_YELLOW
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="margin: 0; color: #888;">Technical Skills</p>
            <span class="percentile-badge" style="background: {color}30; color: {color};">
                Top {100 - peer_data['technical']}%
            </span>
            <p style="margin-top: 5px; font-size: 0.85rem;">You're ahead of <b>{peer_data['technical']}%</b> of users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_p2:
        color = ACCENT_GREEN if peer_data['leadership'] >= 60 else ACCENT_YELLOW
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="margin: 0; color: #888;">Leadership Skills</p>
            <span class="percentile-badge" style="background: {color}30; color: {color};">
                Top {100 - peer_data['leadership']}%
            </span>
            <p style="margin-top: 5px; font-size: 0.85rem;">You're ahead of <b>{peer_data['leadership']}%</b> of users</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_p3:
        color = ACCENT_GREEN if peer_data['overall'] >= 60 else ACCENT_YELLOW
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="margin: 0; color: #888;">Overall Profile</p>
            <span class="percentile-badge" style="background: {color}30; color: {color};">
                Top {100 - peer_data['overall']}%
            </span>
            <p style="margin-top: 5px; font-size: 0.85rem;">Combined percentile ranking</p>
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # SECTION 4: Market Demand Heat Map
    # =====================================================
    st.markdown("---")
    st.subheader("4️⃣ Market Demand vs Your Skills")
    
    market_df = get_market_demand_data(tech_score, leader_score)
    
    fig_market = go.Figure()
    
    fig_market.add_trace(go.Bar(
        name='Market Demand',
        x=market_df['skill'],
        y=market_df['demand'],
        marker_color=ACCENT_CYAN,
        opacity=0.7
    ))
    
    fig_market.add_trace(go.Bar(
        name='Your Level',
        x=market_df['skill'],
        y=market_df['your_level'],
        marker_color=ACCENT_ORANGE,
        opacity=0.7
    ))
    
    fig_market.update_layout(
        barmode='group',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=350,
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )
    st.plotly_chart(fig_market, use_container_width=True)
    
    # Gap Analysis
    st.caption("📊 Skill Gap Analysis")
    for _, row in market_df.iterrows():
        gap = row['demand'] - row['your_level']
        if gap > 10:
            st.warning(f"**{row['skill']}**: {gap}% gap - High priority to improve {row['trend']}")
        elif gap > 0:
            st.info(f"**{row['skill']}**: {gap}% gap - Moderate attention needed {row['trend']}")
        else:
            st.success(f"**{row['skill']}**: You exceed market demand! {row['trend']}")

    # =====================================================
    # SECTION 5: Skill Decay Warnings
    # =====================================================
    st.markdown("---")
    st.subheader("5️⃣ Skill Decay Warnings")
    
    warnings = get_skill_decay_warnings(report)
    
    if warnings:
        for warn in warnings:
            css_class = "warning-high" if warn['severity'] == 'high' else "warning-medium"
            icon = "🔴" if warn['severity'] == 'high' else "🟡"
            st.markdown(f"""
            <div class="{css_class}" style="padding: 15px; border-radius: 8px; margin: 10px 0;">
                <b>{icon} {warn['skill']}</b>
                <p style="margin: 5px 0;">{warn['message']}</p>
                <p style="margin: 0; color: {ACCENT_CYAN};">💡 Action: {warn['action']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No critical skill decay detected. Keep up the momentum!")

    # =====================================================
    # SECTION 6: 90-Day Skill Sprint Generator
    # =====================================================
    st.markdown("---")
    st.subheader("6️⃣ AI-Powered 90-Day Skill Sprint")
    
    if 'learning_plan' not in st.session_state:
        st.session_state.learning_plan = None
    
    col_gen, col_skill = st.columns([1, 2])
    with col_gen:
        if st.button("🚀 Generate My 90-Day Plan", type="primary", use_container_width=True):
            if groq_client:
                with st.spinner("AI is crafting your personalized learning sprint..."):
                    plan = generate_90_day_plan(weakest_skill, groq_client)
                    if plan:
                        st.session_state.learning_plan = plan
            else:
                st.error("AI service unavailable.")
    
    with col_skill:
        st.info(f"📌 Focus Skill: **{weakest_skill}**")
    
    # Display Plan
    if st.session_state.learning_plan:
        plan = st.session_state.learning_plan
        
        # Certifications & Projects
        col_cert, col_proj = st.columns(2)
        with col_cert:
            st.markdown(f"**🏆 Target Certifications:**")
            for cert in plan.get('certifications', [])[:3]:
                st.markdown(f"- {cert}")
        
        with col_proj:
            st.markdown(f"**🛠️ Portfolio Projects:**")
            for proj in plan.get('projects', [])[:3]:
                st.markdown(f"- {proj}")
        
        # Weekly Breakdown
        st.markdown("---")
        st.markdown("**📅 Weekly Breakdown:**")
        
        weeks = plan.get('weeks', [])[:12]
        
        # Show in expandable sections (3 months)
        for month in range(3):
            with st.expander(f"📆 Month {month + 1} (Weeks {month*4 + 1}-{month*4 + 4})", expanded=(month == 0)):
                month_weeks = weeks[month*4:(month+1)*4]
                for week in month_weeks:
                    st.markdown(f"""
                    <div class="sprint-week">
                        <b>Week {week.get('week', '?')}: {week.get('theme', 'Focus')}</b>
                        <ul style="margin: 5px 0;">
                    """, unsafe_allow_html=True)
                    
                    for task in week.get('tasks', []):
                        st.markdown(f"- {task}")
                    
                    st.caption(f"🎯 Milestone: {week.get('milestone', 'Complete weekly tasks')}")
                    
                    resources = week.get('resources', [])
                    if resources:
                        st.caption(f"📚 Resources: {', '.join(resources[:2])}")

    st.markdown("---")
    st.caption("💡 Tip: Run a new analysis from Dashboard to refresh your skill profile")

# Run the page
skill_migration_page()
