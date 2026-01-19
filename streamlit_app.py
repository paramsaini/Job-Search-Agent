import streamlit as st
import os
import pypdf
from dotenv import load_dotenv
from agent import JobSearchAgent

# --- 1. PAGE CONFIGURATION & "STUDIO" STYLING ---
st.set_page_config(
    page_title="AEQUOR",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional "Studio" Look
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
    }
    
    /* Studio Card Styling (Glassmorphism) */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1d222a;
        border: 1px solid #2b313e;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #FFD700 !important; /* Gold Accent */
    }
    
    /* Header Gradients */
    h1, h2, h3 {
        background: -webkit-linear-gradient(eee, #999);
        -webkit-background-clip: text;
        -webkit-text-fill-color: #ffffff;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #FFD700;
        color: #000000;
        border: none;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. SESSION STATE MANAGEMENT (The Fix for Skill Migration) ---
if 'agent' not in st.session_state:
    # Initialize Agent
    api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
    q_host = st.secrets.get("QDRANT_HOST", os.environ.get("QDRANT_HOST"))
    q_key = st.secrets.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY"))
    
    if api_key and q_host:
        st.session_state.agent = JobSearchAgent(api_key, q_host, q_key)
    else:
        st.session_state.agent = None

# Ensure these keys exist so other pages don't crash
if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None
if 'markdown_output' not in st.session_state: st.session_state['markdown_output'] = ""
if 'cv_text_to_process' not in st.session_state: st.session_state['cv_text_to_process'] = ""

# --- 3. HELPER FUNCTIONS ---
def extract_text(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            return "".join([page.extract_text() for page in reader.pages])
        else:
            return uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

def render_kpi_dashboard(report):
    """Renders the sleek top-level metrics."""
    if not report or "error" in report: return

    st.markdown("### 📊 Predictive Candidate Analysis")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        with st.container(border=True):
            st.metric("Global Match Score", f"{report.get('predictive_score', 0)}%")
            st.progress(report.get('predictive_score', 0) / 100)
    
    with kpi2:
        with st.container(border=True):
            st.metric("Technical Depth", f"{report.get('tech_score', 0)}%")
            st.progress(report.get('tech_score', 0) / 100)
            
    with kpi3:
        with st.container(border=True):
            st.metric("Leadership Potential", f"{report.get('leader_score', 0)}%")
            st.progress(report.get('leader_score', 0) / 100)

    st.info(f"🚨 **Critical Weakness Detected:** {report.get('weakest_link_skill', 'None')} — *Optimize this before applying.*")

# --- 4. MAIN APP LAYOUT ---
def main():
    # --- HEADER & NAVIGATION ---
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image("aequor_logo_placeholder.png", width=80) # Ensure this file exists or comment out
    with col_title:
        st.title("AEQUOR")
        st.caption("The smooth, level pathway through job market turbulence.")

    # --- SPECIALIZED TOOLS (Now with 3 Columns) ---
    st.divider()
    st.markdown("### 🛠️ Specialized Tools")
    
    tool1, tool2, tool3 = st.columns(3)
    
    with tool1:
        with st.container(border=True):
            st.markdown("#### 🧘 Emotional Tracker")
            st.caption("Track burnout & resilience.")
            st.page_link("pages/1_Emotional_Tracker.py", label="Open Tracker", icon="🧘")

    with tool2:
        with st.container(border=True):
            st.markdown("#### 🌍 Skill Migration")
            st.caption("Map skills to visa routes.")
            if st.session_state['skill_gap_report']:
                st.page_link("pages/3_Skill_Migration.py", label="Open Map", icon="🌍")
            else:
                st.markdown("*Run Analysis below first*")

    with tool3:
        with st.container(border=True):
            st.markdown("#### 📝 CV Compiler")
            st.caption("Optimize for ATS & Clarity.")
            st.page_link("pages/4_CV_Compiler.py", label="Open Compiler", icon="⚡")

    st.divider()

    # --- INPUT SECTION ---
    with st.sidebar:
        st.header("🔍 Analysis Filters")
        role_filter = st.selectbox(
            "Target Role Context", 
            ["All", "Data Science", "Project Management", "Engineering", "Sales", "HR"],
            help="Filters the 60,000+ resume database to compare you against specific peers."
        )
        st.success("System Status: Online 🟢")

    st.markdown("### 📄 Profile Injection")
    
    uploaded_file = st.file_uploader("Upload CV / Resume (PDF or TXT)", type=["pdf", "txt"])
    
    if st.button("🚀 Generate Comprehensive Strategy", type="primary", use_container_width=True):
        if not uploaded_file:
            st.warning("Please upload a document to begin.")
            return
            
        if not st.session_state.agent:
            st.error("❌ Agent Connection Failed. Check API Keys.")
            return

        with st.spinner("🤖 Agent is analyzing your profile against 60,000+ global candidates..."):
            # 1. Extract Text
            cv_text = extract_text(uploaded_file)
            st.session_state['cv_text_to_process'] = cv_text # Save for other pages
            
            # 2. Agent Logic
            markdown_out, report, sources = st.session_state.agent.generate_strategy(cv_text, role_filter)
            
            # 3. SAVE TO STATE (This fixes the Skill Migration Page)
            st.session_state['skill_gap_report'] = report
            st.session_state['markdown_output'] = markdown_out
            
            st.rerun() # Refresh to show results

    # --- RESULTS DASHBOARD ---
    if st.session_state['skill_gap_report']:
        render_kpi_dashboard(st.session_state['skill_gap_report'])
        
        st.markdown("---")
        st.markdown("### 🧠 Strategic Report")
        with st.container(border=True):
            st.markdown(st.session_state['markdown_output'])
            
            # Sources
            if 'sources' in locals() and sources: # Handle sources if available
                 st.markdown("#### 🔗 Verified Sources")
                 for s in sources:
                     st.markdown(f"- [{s['title']}]({s['uri']})")
    
    elif not uploaded_file:
        st.info("👋 Welcome. Upload your CV above to unlock the Strategic Dashboard and Skill Migration Map.")

if __name__ == "__main__":
    main()
