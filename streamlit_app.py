import streamlit as st
from dotenv import load_dotenv
import os
import pypdf
from agent import JobSearchAgent  # <--- IMPORT THE NEW AGENT

# --- Config & Setup ---
load_dotenv()
st.set_page_config(page_title="Aequor Job Agent", layout="wide")

# Initialize Session State
if 'agent' not in st.session_state:
    st.session_state.agent = None

def init_agent():
    """Initializes the Agent only once using Secrets or Env Vars."""
    if st.session_state.agent is None:
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        q_host = st.secrets.get("QDRANT_HOST", os.environ.get("QDRANT_HOST"))
        q_key = st.secrets.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY"))
        
        if api_key and q_host:
            st.session_state.agent = JobSearchAgent(api_key, q_host, q_key)
        else:
            st.error("Missing Configuration. Please check .env or Streamlit Secrets.")

# --- Helper UI Functions ---
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

def render_dashboard(report):
    """Visualizes the JSON report from the Agent."""
    if not report or "error" in report: return
    
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Match Score", f"{report.get('predictive_score')}%")
    col2.error(f"Weakest Link: {report.get('weakest_link_skill')}")
    col3.info("Technical Depth: " + str(report.get('tech_score')))
    st.progress(report.get('predictive_score')/100)

# --- Main App Layout ---
def main():
    init_agent()
    
    st.title("AEQUOR: AI Job Strategy Agent")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        role_filter = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering", "HR"])
        st.info("Agent is Ready." if st.session_state.agent else "Agent Config Missing.")

    # Input
    uploaded_file = st.file_uploader("Upload CV (PDF/TXT)", type=["pdf", "txt"])
    
    if st.button("Generate Strategy", type="primary"):
        if not uploaded_file:
            st.warning("Please upload a CV first.")
            return
            
        if not st.session_state.agent:
            st.error("Agent not initialized.")
            return

        with st.spinner("Agent is analyzing 60,000+ resumes and searching the web..."):
            cv_text = extract_text(uploaded_file)
            
            # --- THE CLEAN CALL TO THE AGENT ---
            markdown, report, sources = st.session_state.agent.generate_strategy(cv_text, role_filter)
            
            # Save results to state
            st.session_state.results = {"md": markdown, "report": report, "sources": sources}

    # Display Results
    if "results" in st.session_state:
        res = st.session_state.results
        render_dashboard(res['report'])
        st.markdown(res['md'])
        
        if res['sources']:
            st.markdown("### Sources")
            for s in res['sources']:
                st.markdown(f"- [{s['title']}]({s['uri']})")

if __name__ == "__main__":
    main()
