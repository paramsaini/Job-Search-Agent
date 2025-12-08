# --- 2025-12-08_FINAL_ULTIMATE_STABILITY_V7_RESTORED_DESIGN ---
import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io
import pypdf
import re
from qdrant_client import QdrantClient, models 

# Load environment variables (for local testing)
load_dotenv()

# --- RAG Specific Function (FIXED: Defined in global scope) ---

def handle_reset_click():
    """Resets session state variables to restart the search process."""
    st.session_state['reset_key_counter'] = st.session_state.get('reset_key_counter', 0) + 1
    
    st.session_state['cv_input_paste'] = ""
    st.session_state['cv_text_to_process'] = ""
    st.session_state['run_search'] = False
    st.session_state['results_displayed'] = False
    st.session_state['markdown_output'] = ""
    st.session_state['skill_gap_report'] = None
    
# --- Gemini & Qdrant Configuration ---
# Uses st.secrets in Streamlit Cloud, falls back to os.environ locally
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
QDRANT_API_KEY = st.secrets.get("QDRANT_API_KEY", os.environ.get("QDRANT_API_KEY", "")) 
QDRANT_HOST = st.secrets.get("QDRANT_HOST", os.environ.get("QDRANT_HOST", "localhost"))

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={API_KEY}"

# --- RAG Configuration ---
COLLECTION_NAME = 'resume_knowledge_base'
RAG_K = 10 

# --- PDF Extraction Function (Kept) ---
def extract_text_from_pdf(uploaded_file):
    """Uses pypdf to extract text from a PDF file stream."""
    try:
        uploaded_file.seek(0)
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Failed to process PDF with pypdf. Error: {e}")
        return ""

# --- RAG Utility: Initialize Qdrant Client (FIXED SyntaxError) ---
@st.cache_resource
def get_qdrant_client():
    """Initializes and returns the Qdrant Client object."""
    if not QDRANT_API_KEY or not QDRANT_HOST: 
        st.error("Qdrant configuration is missing. Please set QDRANT_HOST and QDRANT_API_KEY in secrets.")
        return None
        
    try:
        client = QdrantClient(
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            prefer_grpc=True
        )
        client.get_collection(collection_name=COLLECTION_NAME) 
        return client
    except Exception as e:
        st.error(f"Qdrant Client Error: Ensure host/key are correct and collection '{COLLECTION_NAME}' exists. Error: {e}")
        return None

# --- RAG Utility: Embed User Query (Kept) ---
@st.cache_data(ttl=600)
def get_user_embedding(text):
    """Calls Gemini API to get a single embedding vector for the user's CV."""
    if not API_KEY: return None
    payload = { "model": EMBEDDING_MODEL, "content": { "parts": [{ "text": text }] } }
    try:
        response = requests.post(EMBEDDING_API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()['embedding']['values']
    except requests.exceptions.RequestException as e:
        st.error(f"Embedding API error during RAG retrieval: {e}")
        return None


# --- Core Gemini API Call Function (MODIFIED FOR RAG) ---
@st.cache_data(show_spinner=False, max_entries=10)
def generate_job_strategy_from_gemini(cv_text):
    if not API_KEY:
        return "Error: Gemini API Key not configured.", None, []
        
    context_text = "No RAG context available."
    qdrant_client_instance = get_qdrant_client()
    
    if qdrant_client_instance:
        query_vector = get_user_embedding(cv_text)
        
        if query_vector:
            try:
                search_result = qdrant_client_instance.search( 
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector, 
                    limit=RAG_K,
                    with_payload=True 
                )
                
                if search_result:
                    retrieved_docs = [hit.payload['text'] for hit in search_result]
                    context_text = "\n---\n".join(retrieved_docs)
                else:
                    context_text = "No relevant resumes found in the knowledge base."
            except Exception as e:
                context_text = f"Qdrant Query Error: {e}"
                st.error(f"Failed to query Qdrant: {e}")

    # --- RAG STEP 2: Augmented Prompt Construction (UNCHANGED) ---
    json_schema = {
        "type": "OBJECT",
        "properties": {
            "predictive_score": {"type": "INTEGER", "description": "Percentage score (0-100)..."},
            "weakest_link_skill": {"type": "STRING", "description": "The specific skill or competency..."},
            "learning_resource_1": {"type": "STRING", "description": "Specific, actionable resource..."},
            "learning_resource_2": {"type": "STRING", "description": "Second specific resource..."},
            "tech_score": {"type": "INTEGER", "description": "Simulated Technical Depth Score (0-100)."},
            "leader_score": {"type": "INTEGER", "description": "Simulated Leadership Potential Score (0-100)."},
            "domain_score": {"type": "INTEGER", "description": "Simulated Domain Expertise Score (0-100)."},
        },
        "required": ["predictive_score", "weakest_link_skill", "learning_resource_1", "learning_resource_2", "tech_score", "leader_score", "domain_score"]
    }
    
    json_prompt = f"""
    Based on the following CV and the RAG Knowledge Base Context (1000 resumes), analyze the user's current professional trajectory...
    --- RETRIEVED KNOWLEDGE BASE CONTEXT ---
    {context_text}
    ---
    User CV: {cv_text}
    """
    
    markdown_prompt = f"""
    You are a World-Class Job Search Consultant and Visa Immigration Analyst...
    --- RETRIEVED KNOWLEDGE BASE CONTEXT (1000 Resumes) ---
    {context_text}
    --- END RETRIEVED CONTEXT ---
    Analyze the user's CV and generate the requested professional job strategy...
    ---
    {cv_text}
    ---
    MANDATORY OUTPUT REQUIREMENTS:
    1. HIGH-ACCURACY DOMESTIC EMPLOYERS: List 5 specific, high-profile employers...
    2. HIGH-ACCURACY INTERNATIONAL EMPLOYERS: List 5 specific, high-profile employers...
    3. DOMESTIC JOB STRATEGY: Provide 3 specific job titles...
    4. INTERNATIONAL JOB STRATEGY: Provide 3 specific international job titles...
    """
    
    json_payload = {
        "contents": [{ "parts": [{ "text": json_prompt }] }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": json_schema
        }
    }
    skill_gap_report = call_gemini_api(json_payload, structured=True)
    
    markdown_payload = {
        "contents": [{ "parts": [{ "text": markdown_prompt }] }],
        "tools": [{ "google_search": {} }],
    }
    
    markdown_output, sources = call_gemini_api(markdown_payload, structured=False)
    
    return markdown_output, skill_gap_report, sources

def call_gemini_api(payload, structured=False):
    """Handles API calls with retries and response parsing for both JSON and Markdown."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            candidate = result.get('candidates', [{}])[0]
            
            if candidate and candidate.get('content') and candidate['content'].get('parts'):
                generated_text = candidate['content']['parts'][0]['text']
                
                if structured:
                    try:
                        return json.loads(generated_text)
                    except json.JSONDecodeError:
                        return {"error": "Failed to decode JSON report."}
                
                sources = []
                grounding_metadata = candidate.get('groundingMetadata')
                    
                if grounding_metadata and grounding_metadata.get('groundingAttributions'):
                    sources = [
                        {"uri": attr.get('web', {}).get('uri'), "title": attr.get('web', {}).get('title')}
                        for attr in grounding_metadata['groundingAttributions']
                        if attr.get('web', {}).get('uri') and attr.get('web', {}).get('title')
                    ]
                return generated_text, sources
            else:
                return ("Error: Model returned empty response.", []) if not structured else {"error": "Empty model response."}
                
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and attempt < 4:
                time.sleep(2 ** attempt)
            else:
                return (f"An HTTP error occurred: {e}", []) if not structured else {"error": str(e)}
        except requests.exceptions.RequestException as e:
            return (f"A network error occurred: {e}", []) if not structured else {"error": str(e)}

    return ("Error: Failed after retries.", []) if not structured else {"error": "Failed after retries."}

# --- Visualization Render (IMPROVED DESIGN) ---
def render_strategy_visualizations(report):
    """Renders the Strategy Funnel and Progress Meter Dashboard using dense data presentation."""
    
    st.header("🧠 Strategic Visualization Suite")
    
    score = report.get('predictive_score', 0)
    score_float = float(score) / 100.0 if score is not None else 0.0
    
    # --- 1. KPI Metrics (Denser presentation with st.metric) ---
    st.subheader("Key Predictive Metrics")
    
    col_kpi_1, col_kpi_2, col_kpi_3 = st.columns(3)
    
    # KPI 1: Overall Match Score
    with col_kpi_1:
        # Determine status for st.metric delta color (using default Streamlit values)
        if score >= 85:
            score_status = "normal"
        elif score >= 70:
            score_status = "off"
        else:
            score_status = "inverse"
        
        st.markdown(f"**Overall Predictive Match**")
        st.metric(label="Score", value=f"{score}%", delta_color=score_status)
        st.progress(score_float)
    
    # KPI 2: Weakest Link / Mitigation Focus
    with col_kpi_2:
        weak_link = report.get('weakest_link_skill', 'N/A')
        st.markdown(f"**Targeted Mitigation Focus**")
        st.error(f"**{weak_link}**")
        st.caption("*Highest priority for CV optimization.*")
        
    # KPI 3: Next Action Step
    with col_kpi_3:
        st.markdown(f"**Immediate Tactical Goal**")
        st.success(f"**Optimize CV in Compiler**")
        st.caption("*Test against a specific Job Description.*")

    st.markdown("---")

    # --- 2. Deep Dive: Predictive Skill Breakdown (More dense information) ---
    st.subheader("Deep Dive: Capability Breakdown")
    
    # Extract sub-scores safely, default to 0 if missing
    tech_score = report.get('tech_score', 0) / 100
    leader_score = report.get('leader_score', 0) / 100
    domain_score = report.get('domain_score', 0) / 100
    
    # Use columns to present the breakdown more densely
    col_skill_1, col_skill_2, col_skill_3 = st.columns(3)
    
    with col_skill_1:
        st.markdown("👨‍💻 **Technical Depth**")
        st.progress(tech_score, text=f"**{int(tech_score * 100)}%**")

    with col_skill_2:
        st.markdown("🤝 **Leadership Potential**")
        st.progress(leader_score, text=f"**{int(leader_score * 100)}%**")

    with col_skill_3:
        st.markdown("🌐 **Domain Expertise**")
        st.progress(domain_score, text=f"**{int(domain_score * 100)}%**")
    
    st.markdown("---")
    
    # --- 3. Action Strategy Pipeline (Restored structure) ---
    st.subheader("Action Strategy Pipeline")
    
    col_flow_1, col_flow_2, col_flow_3 = st.columns(3)
    
    with col_flow_1:
        st.container(border=True, height=150).markdown(f"**1. ANALYSIS**\n\nCV scanned against 1,000 elite profiles. Match Score established.")

    with col_flow_2:
        st.container(border=True, height=150).markdown(f"**2. OPTIMIZATION**\n\nUse Compiler to eliminate the Weakest Link and pass the ATS/Recruiter filters.")

    with col_flow_3:
        st.container(border=True, height=150).markdown(f"**3. EXECUTION**\n\nTarget employers and initiate the Visa Action Plan (see report below).")


# --- Main Application Logic (CLEANED OF CUSTOM STYLING) ---
def main():
    # NO CUSTOM STYLING: Relying on default Streamlit theme for stability
    
    st.title("Aequor")
    st.markdown("### The smooth, level pathway through the job market turbulence.")
    st.markdown("---")

    # --- Conditional Navigation Hub (CLEANED) ---
    st.header("🚀 Specialized Tools")
    
    col_nav_1, col_nav_2 = st.columns(2)
    
    with col_nav_1:
        st.page_link("pages/1_Emotional_Tracker.py", label="🧘 **Emotional Endurance**", icon="🧘", use_container_width=True)
    with col_nav_2:
        st.page_link("pages/3_Skill_Migration.py", label="🌍 **Skill Migration Map**", icon="🌍", use_container_width=True)
        
    st.markdown("---")
    # 👆 END MODIFIED NAVIGATION HUB

    # --- 0. Predictive Skill Health Card (CLEANED) ---
    if st.session_state.get('skill_gap_report'):
        report = st.session_state['skill_gap_report']
        if not report.get('error'):
            
            st.header("✨ Predictive Skill Health Score")
            
            col_advice, col_compiler_link = st.columns([2, 1])
            
            # Advice box using native st.container
            with col_advice:
                with st.container(border=True):
                    st.markdown(f"**Weakest Link Found: {report.get('weakest_link_skill', 'N/A')}**")
                    st.caption(f"Action: You must optimize your CV against target JDs to address this gap.")
                    st.markdown(f"* **Resource 1:** {report.get('learning_resource_1', 'Check report below.')}")
                    st.markdown(f"* **Resource 2:** {report.get('learning_resource_2', 'Check report below.')}")
            
            with col_compiler_link:
                st.markdown('**Immediate Optimization Tool:**')
                st.page_link("pages/4_CV_Compiler.py", label="🔄 **CV Compiler**", icon="🛠️", use_container_width=True)
                
            st.markdown("---")
            
            # --- RENDER VISUALIZATIONS ---
            render_strategy_visualizations(report)
    
    # --- Input Section (CLEANED) ---
    st.subheader("📝 Step 2: Input Your Professional Profile")
    
    tab_paste, tab_upload = st.tabs(["Paste CV Content", "Upload CV File"])
    cv_text = ""
    
    with tab_paste:
        st.caption("**Pasting Tip:** Use Ctrl+Shift+V or Cmd+Shift+V if direct pasting is difficult.")
        st.text_area("Paste CV Content Here", value=st.session_state.get('cv_input_paste', ""), height=300,
            placeholder="Paste your resume content here...", key="cv_input_paste", label_visibility="hidden")
        cv_text = st.session_state.get('cv_input_paste', "")

    with tab_upload:
        uploaded_file_key = f"cv_input_upload_{st.session_state['reset_key_counter']}"
        uploaded_file = st.file_uploader("Upload CV or Resume", type=["txt", "pdf"], key=uploaded_file_key)

        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                st.warning("⚠️ **PDF Extraction:** Using dedicated PDF library (pypdf) for robust reading.")
                try: cv_text = extract_text_from_pdf(uploaded_file)
                except Exception as e: st.error(f"Failed to read PDF. Error: {e}"); cv_text = ""
            else:
                try:
                    uploaded_file.seek(0)
                    raw_bytes = uploaded_file.read()
                    try: string_data = raw_bytes.decode('utf-8')
                    except UnicodeDecodeError: string_data = raw_bytes.decode('windows-1252', errors='replace')
                    cv_text = string_data
                except Exception as e: st.error(f"Error reading TXT file: {e}"); cv_text = ""
            
            if cv_text and len(cv_text.strip()) < 50: st.error("❌ **Reading Failure:** Extracted text is too short or empty."); cv_text = ""
                
        if not cv_text.strip() and st.session_state.get('run_search'):
            st.session_state['run_search'] = False; st.session_state['cv_text_to_process'] = ""; st.warning("Input cancelled due to empty CV content.")
            
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    if col2.button("Generate Comprehensive Job Strategy", type="primary", use_container_width=True):
        if not cv_text.strip(): st.error("Please provide your CV content either by pasting or uploading a file to start the analysis.")
        else: st.session_state['cv_text_to_process'] = cv_text; st.session_state['run_search'] = True
            
    if st.session_state.get('results_displayed'):
        if st.button("Start New Search (Reset)", type="secondary", on_click=handle_reset_click): pass

    st.markdown("---")
    st.subheader("🚀 Step 3: High-Definition Generated Strategy")
    
    if st.session_state.get('run_search') and st.session_state.get('cv_text_to_process'):
        with st.container():
            with st.spinner("Analyzing CV and Performing Real-Time Grounded Search..."):
                markdown_output, skill_gap_report, citations = generate_job_strategy_from_gemini(st.session_state['cv_text_to_process'])

            st.session_state['markdown_output'] = markdown_output
            st.session_state['skill_gap_report'] = skill_gap_report
            
            st.markdown(markdown_output)

            if citations:
                st.markdown("---")
                st.markdown("#### 🔗 Grounding Sources (For Verification)")
                for i, source in enumerate(citations): st.markdown(f"**[{i+1}]** [{source.get('title')}]({source.get('uri')})")
            else: st.info("No explicit grounding sources were returned.")
            
            st.session_state['results_displayed'] = True; st.session_state['run_search'] = False
            st.rerun() 
            
    elif st.session_state.get('results_displayed'):
        with st.container():
            st.markdown(st.session_state.get('markdown_output', 'Results not loaded.'), unsafe_allow_html=False)

    else: st.info("Your comprehensive job search strategy and dynamic skill-match matrix will appear here after analysis. Click 'Generate' to begin.")


if __name__ == '__main__':
    if 'cv_input_paste' not in st.session_state: st.session_state['cv_input_paste'] = ""
    if 'run_search' not in st.session_state: st.session_state['run_search'] = False
    if 'results_displayed' not in st.session_state: st.session_state['results_displayed'] = False
    if 'cv_text_to_process' not in st.session_state: st.session_state['cv_text_to_process'] = ""
    if 'reset_key_counter' not in st.session_state: st.session_state['reset_key_counter'] = 0
    if 'markdown_output' not in st.session_state: st.session_state['markdown_output'] = ""
    if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None 
        
    main()
