import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
import os
import json
import pypdf
from groq import Groq

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

def get_secret(key):
    if key in os.environ: return os.environ[key]
    try: return st.secrets[key]
    except: return None

try:
    supabase = init_supabase()
except Exception as e:
    supabase = None

# Initialize Groq
if 'groq' not in st.session_state:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key:
        st.session_state.groq = Groq(api_key=groq_key)
    else:
        st.session_state.groq = None

# --- Helper Functions ---
def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

# --- Industry Detection ---
def detect_industry(report, cv_text=""):
    """Detect the industry from the CV analysis report"""
    
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
    
    report_text = str(report).lower() + " " + cv_text.lower()
    
    for industry, keywords in industries.items():
        if any(kw in report_text for kw in keywords):
            return industry
    
    return 'general'

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
    st.markdown(f'<h1 style="color:{ACCENT_ORANGE}; text-align: center;">🌐 Skill Migration Map</h1>', unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to view your skill migration map.")
        return

    # Initialize session states
    if 'selected_career_path' not in st.session_state:
        st.session_state.selected_career_path = None
    if 'sprint_generated' not in st.session_state:
        st.session_state.sprint_generated = False
    if 'sprint_plan' not in st.session_state:
        st.session_state.sprint_plan = None
    if 'completed_tasks' not in st.session_state:
        st.session_state.completed_tasks = set()
    if 'skill_migration_report' not in st.session_state:
        st.session_state.skill_migration_report = None

    # =======================================================
    # SECTION 1: ALWAYS VISIBLE - CV Upload Feature
    # =======================================================
    st.subheader("1️⃣ Upload Your Document")
    st.caption("Upload your CV to analyze your skills and generate personalized career paths")
    
    col_upload, col_buttons = st.columns([3, 1])
    
    with col_upload:
        uploaded_cv = st.file_uploader(
            "Upload your CV (PDF/TXT)", 
            type=["pdf", "txt"], 
            key="skill_migration_cv_upload",
            help="Supported formats: PDF, TXT"
        )
    
    with col_buttons:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Analyze CV Button
        analyze_disabled = uploaded_cv is None
        if st.button("🚀 Analyze CV", type="primary", use_container_width=True, disabled=analyze_disabled):
            if uploaded_cv:
                cv_text = extract_text(uploaded_cv)
                if cv_text:
                    # Check if agent exists in session state
                    if st.session_state.get('agent'):
                        with st.spinner("🔍 Analyzing your CV..."):
                            try:
                                md, rep, src = st.session_state.agent.generate_strategy(cv_text, "All")
                                st.session_state.skill_migration_report = rep
                                st.session_state.cv_text_for_migration = cv_text
                                
                                # Reset sprint and career path selections for fresh analysis
                                st.session_state.selected_career_path = None
                                st.session_state.sprint_generated = False
                                st.session_state.sprint_plan = None
                                st.session_state.completed_tasks = set()
                                
                                # Save to Supabase
                                if supabase and st.session_state.user_id:
                                    try:
                                        supabase.table("analyses").insert({
                                            "user_id": st.session_state.user_id,
                                            "report_json": rep
                                        }).execute()
                                    except: pass
                                
                                st.success("✅ CV analyzed successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                    else:
                        st.error("Analysis agent not available. Please check configuration.")
                else:
                    st.warning("Could not extract text from the uploaded file.")
        
        # Reset Button
        if st.button("🔄 Reset", use_container_width=True, help="Clear current analysis and start fresh"):
            st.session_state.skill_migration_report = None
            st.session_state.selected_career_path = None
            st.session_state.sprint_generated = False
            st.session_state.sprint_plan = None
            st.session_state.completed_tasks = set()
            if 'skill_migration_cv_upload' in st.session_state:
                del st.session_state['skill_migration_cv_upload']
            st.success("🔄 Reset complete! Upload a new CV to start fresh analysis.")
            st.rerun()
    
    if not uploaded_cv:
        st.info("👆 Upload your CV above to get started with your personalized skill migration analysis.")
    
    st.markdown("---")

    # =======================================================
    # Try to load existing report from session or database
    # =======================================================
    report = st.session_state.get('skill_migration_report')
    
    if not report:
        # Try to fetch from main app's session state
        if "results" in st.session_state and "rep" in st.session_state.results:
            report = st.session_state.results["rep"]
            st.session_state.skill_migration_report = report
        else:
            # Try to fetch from database
            with st.spinner("Loading your latest analysis..."):
                report = fetch_latest_report()
                if report:
                    st.session_state.skill_migration_report = report
    
    # =======================================================
    # Show message if no analysis exists yet
    # =======================================================
    if not report:
        st.markdown("""
        <div style="background: rgba(255, 140, 0, 0.1); border: 1px solid #FF8C00; border-radius: 12px; padding: 30px; text-align: center; margin: 20px 0;">
            <h3 style="color: #FF8C00;">📊 No Analysis Found</h3>
            <p style="color: #ccc;">Upload your CV above and click <strong>"Analyze CV"</strong> to see your personalized:</p>
            <ul style="text-align: left; color: #aaa; max-width: 400px; margin: 0 auto;">
                <li>Career trajectory recommendations</li>
                <li>90-day skill sprint plan</li>
                <li>Skill gap analysis</li>
                <li>Skill decay warnings</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        return

    # =======================================================
    # SECTION 2: Profile Scores
    # =======================================================
    st.subheader("2️⃣ Your Profile Scores")
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
        weakest_skill = report.get('weakest_link_skill', 'N/A')
        st.error(f"Focus Area: {weakest_skill}")
        st.caption("Prioritize improving this skill.")

    st.markdown("---")
    
    # =======================================================
    # SECTION 3: Interactive Career Path Visualizer (CLICKABLE)
    # =======================================================
    st.subheader("3️⃣ Interactive Career Path Visualizer")
    st.caption("👆 Click on a career path to see detailed requirements and timeline")
    
    # Define career paths with detailed data
    career_paths = {
        "Senior Specialist": {
            "color": "#10B981",
            "success_rate": 85,
            "timeline": "6-12 months",
            "target_role": "Team Lead / Senior Engineer",
            "required_skills": ["Advanced Technical Skills", "Project Management", "Mentoring"],
            "skill_gaps": [
                {"skill": "System Design", "gap": 25, "priority": "High"},
                {"skill": "Leadership", "gap": 30, "priority": "Medium"},
                {"skill": "Communication", "gap": 15, "priority": "Low"}
            ],
            "milestones": [
                {"month": "Month 1-2", "task": "Complete advanced certifications"},
                {"month": "Month 3-4", "task": "Lead a small project"},
                {"month": "Month 5-6", "task": "Mentor junior team members"},
                {"month": "Month 7-9", "task": "Take ownership of critical systems"},
                {"month": "Month 10-12", "task": "Apply for senior positions"}
            ]
        },
        "Management Track": {
            "color": "#3B82F6",
            "success_rate": 70,
            "timeline": "12-18 months",
            "target_role": "Engineering Manager / Director",
            "required_skills": ["People Management", "Strategic Planning", "Budget Management"],
            "skill_gaps": [
                {"skill": "People Management", "gap": 40, "priority": "High"},
                {"skill": "Strategic Thinking", "gap": 35, "priority": "High"},
                {"skill": "Stakeholder Management", "gap": 25, "priority": "Medium"}
            ],
            "milestones": [
                {"month": "Month 1-3", "task": "Leadership training courses"},
                {"month": "Month 4-6", "task": "Shadow current managers"},
                {"month": "Month 7-9", "task": "Lead cross-functional projects"},
                {"month": "Month 10-12", "task": "Manage a small team"},
                {"month": "Month 13-18", "task": "Transition to full management role"}
            ]
        },
        "Domain Expert": {
            "color": "#8B5CF6",
            "success_rate": 60,
            "timeline": "18-24 months",
            "target_role": "Consultant / Advisor / Architect",
            "required_skills": ["Deep Domain Knowledge", "Public Speaking", "Thought Leadership"],
            "skill_gaps": [
                {"skill": "Industry Expertise", "gap": 45, "priority": "High"},
                {"skill": "Public Speaking", "gap": 50, "priority": "High"},
                {"skill": "Writing/Content", "gap": 30, "priority": "Medium"}
            ],
            "milestones": [
                {"month": "Month 1-4", "task": "Earn industry certifications"},
                {"month": "Month 5-8", "task": "Publish articles/blog posts"},
                {"month": "Month 9-12", "task": "Speak at local meetups"},
                {"month": "Month 13-18", "task": "Build consulting portfolio"},
                {"month": "Month 19-24", "task": "Establish thought leadership"}
            ]
        }
    }
    
    # Display clickable career path cards
    cols = st.columns(3)
    for idx, (path_name, path_data) in enumerate(career_paths.items()):
        with cols[idx]:
            card_selected = st.session_state.selected_career_path == path_name
            border_width = "3px" if card_selected else "1px"
            opacity = "1" if card_selected else "0.5"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {path_data['color']}40, {path_data['color']}20); 
                        padding: 20px; border-radius: 12px; border: {border_width} solid {path_data['color']}; 
                        min-height: 180px; margin-bottom: 10px;">
                <h4 style="color: {path_data['color']}; margin: 0 0 8px 0;">{path_name}</h4>
                <p style="color: #ccc; font-size: 0.85em; margin: 8px 0;">→ {path_data['target_role']}</p>
                <p style="color: white; font-weight: bold; font-size: 1.3em; margin: 10px 0;">{path_data['success_rate']}% success rate</p>
                <p style="color: #aaa; font-size: 0.85em; margin: 0;">⏱️ {path_data['timeline']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            btn_type = "primary" if card_selected else "secondary"
            btn_label = "✓ Selected" if card_selected else "View Details"
            
            if st.button(btn_label, key=f"btn_{path_name}", type=btn_type, use_container_width=True):
                if st.session_state.selected_career_path == path_name:
                    st.session_state.selected_career_path = None
                else:
                    st.session_state.selected_career_path = path_name
                st.rerun()
    
    # =======================================================
    # Display selected career path details
    # =======================================================
    if st.session_state.selected_career_path:
        selected_path = career_paths[st.session_state.selected_career_path]
        
        st.markdown("---")
        st.markdown(f"""
        <div style="background: {selected_path['color']}15; border: 2px solid {selected_path['color']}; border-radius: 12px; padding: 20px; margin: 15px 0;">
            <h3 style="color: {selected_path['color']}; margin-top: 0;">📋 {st.session_state.selected_career_path} - Detailed View</h3>
        </div>
        """, unsafe_allow_html=True)
        
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.markdown("**🎯 Required Skill Gaps to Close:**")
            for gap in selected_path['skill_gaps']:
                if gap['priority'] == "High":
                    priority_color = "#ef4444"
                    priority_icon = "🔴"
                elif gap['priority'] == "Medium":
                    priority_color = "#f59e0b"
                    priority_icon = "🟡"
                else:
                    priority_color = "#10b981"
                    priority_icon = "🟢"
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid {priority_color};">
                    <strong>{gap['skill']}</strong>: {gap['gap']}% gap 
                    <span style="color: {priority_color}; font-size: 0.85em;">{priority_icon} {gap['priority']} Priority</span>
                </div>
                """, unsafe_allow_html=True)
        
        with detail_col2:
            st.markdown("**📅 Timeline & Milestones:**")
            for milestone in selected_path['milestones']:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <strong style="color: {selected_path['color']};">{milestone['month']}</strong><br>
                    <span style="color: #ccc;">✅ {milestone['task']}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    
    # =======================================================
    # SECTION 4: AI-Powered 90-Day Skill Sprint Generator
    # =======================================================
    st.subheader("4️⃣ AI-Powered 90-Day Skill Sprint Generator")
    st.caption(f"📚 Personalized learning plan based on your weakest skill: **{weakest_skill}**")
    
    col_generate, col_reset_sprint = st.columns([3, 1])
    
    with col_generate:
        if st.button("🚀 Generate 90-Day Sprint Plan", type="primary", use_container_width=True):
            with st.spinner("🤖 AI is creating your personalized learning plan..."):
                if st.session_state.get('groq'):
                    try:
                        prompt = f"""
                        Create a detailed 90-day skill sprint plan for someone who needs to improve their "{weakest_skill}" skill.
                        
                        Format the response EXACTLY as follows (use this exact structure):
                        
                        WEEK 1-2: Foundation
                        - Task: [Specific task]
                        - Resource: [Free course or resource with actual URL if possible]
                        - Project: [Small project to practice]
                        
                        WEEK 3-4: Building Blocks
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Project to build]
                        
                        WEEK 5-6: Intermediate Skills
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Project to build]
                        
                        WEEK 7-8: Advanced Concepts
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Project to build]
                        
                        WEEK 9-10: Real-World Application
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Portfolio project]
                        
                        WEEK 11-12: Certification & Portfolio
                        - Task: [Get certified]
                        - Certification: [Recommended certification]
                        - Final Project: [Capstone project]
                        
                        RECOMMENDED CERTIFICATIONS:
                        1. [Certification name and provider]
                        2. [Certification name and provider]
                        3. [Certification name and provider]
                        
                        Keep it practical with free resources from Coursera, YouTube, freeCodeCamp, etc.
                        """
                        
                        completion = st.session_state.groq.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        )
                        st.session_state.sprint_plan = completion.choices[0].message.content
                        st.session_state.sprint_generated = True
                        st.session_state.completed_tasks = set()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate plan: {e}")
                else:
                    # Fallback static plan
                    st.session_state.sprint_plan = f"""
WEEK 1-2: Foundation
- Task: Understand core concepts of {weakest_skill}
- Resource: YouTube - Search "{weakest_skill} for beginners"
- Project: Create a simple demo project

WEEK 3-4: Building Blocks
- Task: Learn intermediate techniques
- Resource: Coursera - Free courses on {weakest_skill}
- Project: Build a practical application

WEEK 5-6: Intermediate Skills
- Task: Deep dive into best practices
- Resource: freeCodeCamp tutorials
- Project: Contribute to open source

WEEK 7-8: Advanced Concepts
- Task: Master advanced patterns
- Resource: Official documentation
- Project: Complex real-world project

WEEK 9-10: Real-World Application
- Task: Apply skills in professional context
- Resource: Industry blogs and case studies
- Project: Portfolio-worthy project

WEEK 11-12: Certification & Portfolio
- Task: Get certified and polish portfolio
- Certification: Research top certifications for {weakest_skill}
- Final Project: Capstone demonstrating all skills

RECOMMENDED CERTIFICATIONS:
1. Check Coursera for {weakest_skill} certifications
2. LinkedIn Learning certificates
3. Industry-specific certifications
                    """
                    st.session_state.sprint_generated = True
                    st.session_state.completed_tasks = set()
                    st.rerun()
    
    with col_reset_sprint:
        if st.session_state.sprint_generated:
            if st.button("🔄 Reset Plan", use_container_width=True):
                st.session_state.sprint_generated = False
                st.session_state.sprint_plan = None
                st.session_state.completed_tasks = set()
                st.rerun()
    
    # Display generated sprint plan with progress tracker
    if st.session_state.sprint_generated and st.session_state.sprint_plan:
        st.markdown("---")
        st.markdown("### 📚 Your Personalized 90-Day Plan")
        
        # Parse and display with checkboxes
        plan_lines = st.session_state.sprint_plan.split('\n')
        current_week = ""
        task_count = 0
        
        for i, line in enumerate(plan_lines):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('**WEEK') or line.startswith('WEEK'):
                current_week = line.replace('**', '').replace('*', '')
                st.markdown(f"#### 📅 {current_week}")
            elif line.startswith('- ') or line.startswith('• '):
                task_key = f"sprint_task_{i}"
                task_text = line[2:].strip()
                task_count += 1
                
                # Checkbox for progress tracking
                completed = st.checkbox(
                    task_text, 
                    key=task_key,
                    value=task_key in st.session_state.completed_tasks
                )
                if completed:
                    st.session_state.completed_tasks.add(task_key)
                elif task_key in st.session_state.completed_tasks:
                    st.session_state.completed_tasks.remove(task_key)
                    
            elif line.startswith('**RECOMMENDED') or line.startswith('RECOMMENDED'):
                st.markdown(f"#### 🏆 {line.replace('**', '').replace(':', '')}")
            elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                st.markdown(f"  {line}")
        
        # Progress bar
        total_tasks = len([l for l in plan_lines if l.strip().startswith('- ') or l.strip().startswith('• ')])
        completed_count = len(st.session_state.completed_tasks)
        
        if total_tasks > 0:
            progress = completed_count / total_tasks
            st.markdown("---")
            
            progress_color = ACCENT_GREEN if progress >= 0.7 else ACCENT_ORANGE if progress >= 0.3 else "#ef4444"
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 10px 0;">
                <h4 style="color: {progress_color}; margin: 0;">📊 Overall Progress: {completed_count}/{total_tasks} tasks completed ({int(progress*100)}%)</h4>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress)

    st.markdown("---")
    
    # =======================================================
    # SECTION 5: Skill Decay Warning System
    # =======================================================
    st.subheader("5️⃣ Skill Decay Warning System")
    st.caption("⚠️ Track skills that may need refreshing based on industry trends")
    
    tech_score = report.get('tech_score', 50)
    
    # Generate skill decay data based on analysis
    skill_decay_data = [
        {
            "skill": weakest_skill, 
            "last_updated": "Recently analyzed", 
            "status": "current", 
            "decay_risk": "Low",
            "message": f"✅ Your {weakest_skill} knowledge is current based on recent analysis"
        },
        {
            "skill": "Core Technical Skills", 
            "last_updated": "3 months ago", 
            "status": "moderate", 
            "decay_risk": "Medium",
            "message": "⏰ Core technical skills could use a refresh - consider taking an updated course"
        },
        {
            "skill": "Industry Knowledge", 
            "last_updated": "6+ months ago", 
            "status": "outdated", 
            "decay_risk": "High",
            "message": "⚠️ Industry knowledge may be outdated - new trends and technologies have emerged"
        },
    ]
    
    for skill_data in skill_decay_data:
        if skill_data['status'] == 'outdated':
            color = "#ef4444"
            icon = "🔴"
            bg_color = "rgba(239, 68, 68, 0.1)"
        elif skill_data['status'] == 'moderate':
            color = "#f59e0b"
            icon = "🟡"
            bg_color = "rgba(245, 158, 11, 0.1)"
        else:
            color = "#10b981"
            icon = "🟢"
            bg_color = "rgba(16, 185, 129, 0.1)"
        
        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 4px solid {color}; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
            <strong style="color: white;">{icon} {skill_data['skill']}</strong><br>
            <span style="color: #ccc; font-size: 0.9em;">{skill_data['message']}</span><br>
            <span style="color: {color}; font-size: 0.85em; margin-top: 5px; display: inline-block;">
                Decay Risk: <strong>{skill_data['decay_risk']}</strong> | Last Updated: {skill_data['last_updated']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    # Refresh course suggestions
    with st.expander("📖 Suggested Refresh Courses", expanded=False):
        st.markdown("""
        **🎓 Free Resources to Keep Your Skills Sharp:**
        
        **Coursera** - Audit courses for free
        - [Browse all free courses](https://www.coursera.org/courses?query=free)
        
        **📺 YouTube Channels:**
        - Traversy Media (Web Development)
        - Tech With Tim (Python)
        - freeCodeCamp (Full tutorials)
        - NetworkChuck (IT & Networking)
        
        **📚 Other Free Resources:**
        - [freeCodeCamp](https://www.freecodecamp.org/)
        - [The Odin Project](https://www.theodinproject.com/)
        - [Khan Academy](https://www.khanacademy.org/)
        - [edX Free Courses](https://www.edx.org/search?tab=course)
        - [Codecademy Free Tier](https://www.codecademy.com/)
        """)

    st.markdown("---")
    
    # =======================================================
    # SECTION 6: Skill Gap Analysis Summary
    # =======================================================
    st.subheader("6️⃣ Skill Gap Analysis Summary")
    st.caption("📊 Visual breakdown of your skill levels vs. target requirements")
    
    # Create visual skill gap bars
    skills_to_analyze = [
        {"name": "Technical Foundation", "current": tech_score, "target": 90},
        {"name": "Leadership & Soft Skills", "current": report.get('leader_score', 50), "target": 80},
        {"name": weakest_skill, "current": max(20, tech_score - 30), "target": 85},
        {"name": "Industry Knowledge", "current": min(90, tech_score + 10), "target": 85},
    ]
    
    for skill in skills_to_analyze:
        gap = skill['target'] - skill['current']
        
        if gap > 30:
            gap_color = "#ef4444"
            urgency = "🔴 High Urgency"
        elif gap > 15:
            gap_color = "#f59e0b"
            urgency = "🟡 Medium Urgency"
        elif gap > 0:
            gap_color = "#10b981"
            urgency = "🟢 Low Urgency"
        else:
            gap_color = "#10b981"
            urgency = "✅ On Target"
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{skill['name']}**")
            st.progress(skill['current'] / 100)
        
        with col2:
            st.markdown(f"<span style='color: #888;'>Current: {skill['current']}%</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='color: #888;'>Target: {skill['target']}%</span>", unsafe_allow_html=True)
        
        with col3:
            if gap > 0:
                st.markdown(f"<span style='color: {gap_color}; font-weight: bold;'>Gap: {gap}%</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: {gap_color}; font-size: 0.8em;'>{urgency}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #10b981; font-weight: bold;'>✅ Exceeds!</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color: #10b981; font-size: 0.8em;'>+{abs(gap)}% above target</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detect and display industry
    cv_text = st.session_state.get('cv_text_for_migration', '')
    industry = detect_industry(report, cv_text)
    
    st.info(f"🔍 **Detected Industry:** {industry.title()} | 💡 Upload a new CV anytime to refresh your analysis and track your progress!")

skill_migration_page()
