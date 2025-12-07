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
from qdrant_client import QdrantClient, models # <-- Qdrant Client Import

# Load environment variables (for local testing)
load_dotenv()

# --- RAG Specific Function (FIXED: Defined in global scope) ---

def handle_reset_click():
    """Resets session state variables to restart the search process."""
    # Increment the reset counter to force the file_uploader to be recreated.
    st.session_state['reset_key_counter'] = st.session_state.get('reset_key_counter', 0) + 1
    
    # Reset input values and flow control flags
    st.session_state['cv_input_paste'] = ""
    st.session_state['cv_text_to_process'] = ""
    st.session_state['run_search'] = False
    st.session_state['results_displayed'] = False
    st.session_state['markdown_output'] = "" # Clear previous output
    st.session_state['skill_gap_report'] = None # CLEAR NEW REPORT
    
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
RAG_K = 10 # Number of top documents to retrieve

# --- Holographic Theme Configuration (UPDATED for maximum effect and new colors) ---
BG_DARK = "#000000" # Pure black background for max contrast
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00" # REPLACED PINK with ORANGE
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
TEXT_HOLO = f"0 0 10px {ACCENT_CYAN}, 0 0 20px {ACCENT_ORANGE}90" # Stronger glow using new color
GRID_CYAN = "rgba(0, 255, 255, 0.6)" # Brighter grid
GRID_ORANGE = "rgba(255, 140, 0, 0.6)" # NEW: Orange grid for the new plot axis
GRID_GREEN = "rgba(16, 185, 129, 0.6)"

# ------------------------------------------------
# FIX: DEFINITION OF custom_css
# ------------------------------------------------
custom_css = f"""
<style>
/* Streamlit standard cleanup */
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
.stApp {{
    background-color: {BG_DARK};
    color: white;
}}

/* Holographic Text Effect */
.holo-text {{
    color: {ACCENT_CYAN};
    text-shadow: {TEXT_HOLO};
    font-weight: 700;
    transition: all 0.3s ease-in-out;
}}

/* Custom Button Styling */
div.stButton > button {{
    color: {BG_DARK};
    background-color: {ACCENT_ORANGE}; /* REPLACED PINK */
    border: 2px solid {ACCENT_ORANGE}; /* REPLACED PINK */
    border-radius: 12px;
    font-weight: bold;
    box-shadow: 0 0 10px {ACCENT_ORANGE}50, 0 0 20px {ACCENT_ORANGE}30; /* REPLACED PINK */
    transition: all 0.3s ease-in-out;
}}

/* Custom Card for Results/Reports */
.results-card, .glass-card {{
    padding: 20px;
    margin: 15px 0;
    border-radius: 15px;
    border: 2px solid {ACCENT_CYAN}40;
    background: rgba(16, 185, 129, 0.05); /* Very light green/glass effect */
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
}}

/* Textarea color fix */
.stTextArea label, .stFileUploader label, .stMarkdown p {{
    color: white !important;
}}

/* Horizontal Rule Fix */
hr {{
    border-top: 2px solid {ACCENT_CYAN}50;
    margin: 1rem 0;
}}
</style>
"""
# ------------------------------------------------

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

# --- RAG Utility: Initialize Qdrant Client ---
@st.cache_resource
def get_qdrant_client():
    """Initializes and returns the Qdrant Client object."""
    if not QDRANT_API_KEY or not QDRANT_HOST:
        st.error("Qdrant configuration is missing. Please set QDRANT_HOST and QDRANT_API_KEY in secrets.")
        return None
        
    try:
        client = QdrantClient(
            # FIX: Use 'url' instead of 'host' for the full HTTPS protocol
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            prefer_grpc=True
        )
        # Verify collection exists (optional but recommended)
        client.get_collection(collection_name=COLLECTION_NAME) 
        return client
    except Exception as e:
        # NOTE: Error text changed to reflect 'url' usage
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
        
    # --- RAG STEP 1: Retrieval from Qdrant ---
    context_text = "No RAG context available."
    
    # FIX: Use a more specific variable name to avoid shadowing and ensure correct object type
    qdrant_client_instance = get_qdrant_client()
    
    if qdrant_client_instance:
        query_vector = get_user_embedding(cv_text)
        
        if query_vector:
            try:
                # Use the specific instance name
                search_result = qdrant_client_instance.search( 
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector, # Pass the vector here
                    limit=RAG_K,
                    with_payload=True 
                )
                
                # Format the retrieved documents into a single context string
                if search_result: # Search results are returned as a list of points
                    retrieved_docs = [hit.payload['text'] for hit in search_result]
                    context_text = "\n---\n".join(retrieved_docs)
                else:
                    context_text = "No relevant resumes found in the knowledge base."
            except Exception as e:
                context_text = f"Qdrant Query Error: {e}"
                st.error(f"Failed to query Qdrant: {e}")

    # --- RAG STEP 2: Augmented Prompt Construction ---
    # NEW: Define JSON schema for the predictive skill report
    json_schema = {
        "type": "OBJECT",
        "properties": {
            "predictive_score": {"type": "INTEGER", "description": "Percentage score (0-100) comparing user's profile to the elite RAG context (90-100)."},
            "weakest_link_skill": {"type": "STRING", "description": "The specific skill or competency (e.g., Data Modeling, Team Leadership) with the largest gap."},
            "learning_resource_1": {"type": "STRING", "description": "Specific, actionable resource to close the weakest link gap."},
            "learning_resource_2": {"type": "STRING", "description": "Second specific resource."},
        },
        "required": ["predictive_score", "weakest_link_skill", "learning_resource_1", "learning_resource_2"]
    }
    
    # NEW: First call to get the JSON report (Structured response)
    json_prompt = f"""
    Based on the following CV and the RAG Knowledge Base Context (1000 resumes), analyze the user's current professional trajectory relative to the elite profiles found in the context. 
    Generate a JSON object strictly following the provided schema. The 'predictive_score' should reflect the user's readiness for the next 5 years of market demands as seen in the RAG context.

    --- RETRIEVED KNOWLEDGE BASE CONTEXT ---
    {context_text}
    ---
    User CV: {cv_text}
    """
    
    # NEW: Second call for the main Markdown strategy (Text response)
    markdown_prompt = f"""
    You are a World-Class Job Search Consultant and Visa Immigration Analyst. Your primary goal is to generate the professional job strategy using Google Search for current data, and the RETRIEVED KNOWLEDGE BASE CONTEXT for grounding employer types.
    
    --- RETRIEVED KNOWLEDGE BASE CONTEXT (1000 Resumes) ---
    {context_text}
    --- END RETRIEVED CONTEXT ---

    Analyze the user's CV and generate the requested professional job strategy. The user's CV content is:
    ---
    {cv_text}
    ---
    MANDATORY OUTPUT REQUIREMENTS:
    1. HIGH-ACCURACY DOMESTIC EMPLOYERS: List 5 specific, high-profile employers in the user's current domestic location 
    (or related domestic hubs) that match the CV content (90%-100% suitability). For each, provide the name, location, a brief rationale, and the **[Direct Company Website Link](URL)**.
    2. HIGH-ACCURACY INTERNATIONAL EMPLOYERS: List 5 specific, high-profile employers globally, focusing on key immigration countries (US, UK, Canada, EU), that match the CV content (90%-100% suitability). For each, provide the name, location, a brief rationale, and the **[Direct Company Website Link](URL)**.
    3. DOMESTIC JOB STRATEGY: Provide 3 specific job titles matching the CV. For each title, give a step-by-step guide on how to apply.\n"
    4. INTERNATIONAL JOB STRATEGY: Provide 3 specific international job titles matching the CV. For each title/region, you MUST include: 
        a. The typical application steps (including necessary foreign credential evaluations). 
        b. The specific, relevant **visa category/code** (e.g., H-1B, Skilled Worker Visa, Blue Card). 
        c. Key **visa sponsorship requirements** for the employer and applicant, citing the search source.
    """
    
    # --- Execute two calls: one for structured data, one for text ---
    
    # CALL 1: Structured (JSON) Report
    json_payload = {
        "contents": [{ "parts": [{ "text": json_prompt }] }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": json_schema
        }
    }
    skill_gap_report = call_gemini_api(json_payload, structured=True)
    
    # CALL 2: Markdown Strategy (Text + Search Grounding)
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
                
                # Handle text output and sources
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


# --- Data Simulation for 3D Plotly (Remains Unchanged) ---
@st.cache_data
def load_3d_data_dummy():
    """Generates mock data for the 3D visualization when no results are available."""
    df_skills = pd.DataFrame({
        'X_Tech': [60], 'Y_Leader': [60], 'Z_Domain': [60], 'Overall_Match': [60],
        'Employer': ['Parsing Failed'], 'Country': ['N/A'], 'Type': ['Fallback']
    })
    return df_skills

def generate_dynamic_3d_data(markdown_output):
    """Parses the Markdown output to find specific employers, their countries, and assigns simulated skill scores."""
    
    employers_data = []
    
    # NEW ROBUST REGEX: Finds all [Name](URL) links in the entire output.
    # We strip out common non-link markdown formatting first.
    cleaned_output = markdown_output.replace('**', '').replace('*', '')

    # Pattern to find the link structure anywhere in the entire output.
    link_pattern = r'\[([^\]]+)\]\((https?:\/\/[^\)]+)\)'
    
    # Pattern to find country keywords near the link structure to guess location type.
    country_keywords = r'(US|USA|United States|UK|United Kingdom|Canada|Germany|France|Japan|Singapore|EU)'

    
    # 1. Capture ALL links globally
    all_links = list(re.finditer(link_pattern, cleaned_output))
    
    for link_match in all_links:
        full_match_text = link_match.group(0)
        name = link_match.group(1).strip()
        link_index = link_match.start()
        
        # --- Determine Domestic/International (Type) based on position ---
        
        # Check if the link falls within the "HIGH-ACCURACY DOMESTIC EMPLOYERS" section
        is_domestic = bool(re.search(r'HIGH-ACCURACY DOMESTIC EMPLOYERS:(.*?)(?=\d+\.|\Z)', cleaned_output[:link_index], re.DOTALL | re.IGNORECASE))
        
        if is_domestic:
            type_label = 'Domestic (High Match)'
            base_score = np.random.randint(90, 100)
        else:
            type_label = 'International (Key Market)'
            base_score = np.random.randint(80, 95)
            
        # --- Determine Country ---
        # Look for the country keyword in the 200 characters *before* the link for context
        context_start = max(0, link_index - 200)
        context = cleaned_output[context_start:link_index]
        
        location_match = re.search(country_keywords, context, re.IGNORECASE)
        
        if location_match:
            country = location_match.group(0).replace('United States', 'USA').replace('United Kingdom', 'UK')
        else:
            country = 'Domestic Hub' if is_domestic else 'International Market'
            
        
        employers_data.append({'Employer': name, 'Country': country, 'Type': type_label,
            'X_Tech': base_score + np.random.normal(0, 4), 
            'Y_Leader': base_score + np.random.normal(0, 4), 
            'Z_Domain': base_score + np.random.normal(0, 4), 
            'Overall_Match': base_score
        })
            
    if len(employers_data) < 5:
        # Fallback will only trigger if less than 5 valid links were successfully parsed.
        return load_3d_data_dummy()

    df = pd.DataFrame(employers_data)
    numeric_cols = ['X_Tech', 'Y_Leader', 'Z_Domain', 'Overall_Match']
    df[numeric_cols] = df[numeric_cols].clip(0, 100)
    
    return df

# --- NEW 2D RENDER FUNCTION ---
def render_2d_skill_match_plot(df_skills):
    """Renders a 2D Plotly Scatter Plot showing Technical Depth vs. Leadership Potential."""
    
    color_map = {
        'Domestic (High Match)': ACCENT_CYAN,
        'International (Key Market)': ACCENT_ORANGE, # Using new color
        'Fallback': ACCENT_YELLOW
    }

    st.markdown('<h2 class="holo-text" style="margin-top: 2rem;">2D Skill-Match Scatter Plot</h2>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #ccc;'>
    The plot visualizes your **top matched employers**. The X-axis represents **Technical Depth**, the Y-axis represents **Leadership Potential**. Point size indicates **Domain Expertise** (Overall Fit).
    </p>
    """, unsafe_allow_html=True)
    
    if len(df_skills) == 1 and df_skills['Type'].iloc[0] == 'Fallback':
          st.error("❌ **Data Parsing Failed:** Ensure the Gemini output includes at least 5 employers with the required Markdown link format: `[Employer Name](URL)`.")
          return

    # Use X_Tech and Y_Leader for 2D plot, use Z_Domain for size
    fig = px.scatter(
        df_skills, 
        x='X_Tech', 
        y='Y_Leader', 
        color='Type', 
        hover_name='Employer', 
        text='Country', 
        size='Z_Domain', # Use Domain Expertise for size to represent the third dimension
        size_max=30,
        color_discrete_map=color_map,
        title="Technical vs. Leadership Match",
        height=600
    )

    fig.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color="white"),
        # X-Axis configuration
        xaxis=dict(
            backgroundcolor="rgba(0,0,0,0)", gridcolor=GRID_CYAN, 
            title="Technical Depth (%)", title_font=dict(color=ACCENT_CYAN), 
            tickfont=dict(color="white"), range=[50, 100], 
            showbackground=False, showgrid=True, zeroline=True, gridwidth=2 
        ),
        # Y-Axis configuration
        yaxis=dict(
            backgroundcolor="rgba(0,0,0,0)", gridcolor=GRID_ORANGE, # Using new color
            title="Leadership Potential (%)", title_font=dict(color=ACCENT_ORANGE), # Using new color
            tickfont=dict(color="white"), range=[50, 100],
            showbackground=False, showgrid=True, zeroline=True, gridwidth=2
        ),
        legend_title_text='Match Type',
        hoverlabel=dict(bgcolor="#111111", font_size=14, font_color=ACCENT_CYAN, bordercolor=ACCENT_ORANGE) # Using new color
    )
    
    st.plotly_chart(fig, use_container_width=True)


# --- Main Application Logic (Unchanged) ---
def main():
    st.markdown(custom_css, unsafe_allow_html=True) # Apply CSS first
    
    st.markdown('<h1 class="holo-text" style="font-size: 3rem; margin-bottom: 0.5rem; text-align: center;">🤖 AI Recruitment Matrix V3.0</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.25rem; color: #9CA3AF; text-align: center;">Analyze your CV against global employers using grounded Gemini AI.</p>', unsafe_allow_html=True)
    st.markdown("---")

    # --- 0. Predictive Skill Health Card (NEW FEATURE DISPLAY) ---
    if st.session_state.get('skill_gap_report'):
        report = st.session_state['skill_gap_report']
        if not report.get('error'):
            st.markdown(f'<h2 class="holo-text" style="color:{ACCENT_ORANGE};">✨ Predictive Skill Health Score</h2>', unsafe_allow_html=True) # Changed color
            col_score, col_gap = st.columns([1, 2])
            
            with col_score:
                score = report.get('predictive_score', 0)
                score_color = ACCENT_GREEN if score >= 85 else (ACCENT_YELLOW if score >= 70 else ACCENT_ORANGE) # Changed color
                st.markdown(f"""
                    <div class="glass-card" style="border: 2px solid {score_color}; text-align: center; height: 100%;">
                        <p style="color: {score_color}; font-size: 1rem; margin-bottom: 0;">Trajectory Match</p>
                        <p style="color: white; font-size: 3rem; font-weight: bold; margin: 0; text-shadow: 0 0 10px {score_color}50;">{score}%</p>
                    </div>
                """, unsafe_allow_html=True)
                
            with col_gap:
                st.markdown(f"""
                    <div class="glass-card">
                        <p style="color: {ACCENT_ORANGE}; font-weight: bold; margin-bottom: 0.5rem;">Weakest Link Found: {report.get('weakest_link_skill', 'N/A')}</p>
                        <p style="color: #ccc; margin-bottom: 0.5rem; font-size: 0.9rem;">Recommended Action Plan (Informed by RAG):</p>
                        <ul style="color: {ACCENT_CYAN}; padding-left: 20px;">
                            <li>{report.get('learning_resource_1', 'Check report below.')}</li>
                            <li>{report.get('learning_resource_2', 'Check report below.')}</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("---")

    # --- 1. Conditional 2D Visualization (Updated) ---
    if st.session_state.get('results_displayed'):
        df_match = generate_dynamic_3d_data(st.session_state.get('markdown_output', ''))
        render_2d_skill_match_plot(df_match) # <-- NEW FUNCTION CALL
        st.markdown("---")
    
    st.subheader("📝 Step 2: Input Your Professional Profile")
    
    tab_paste, tab_upload = st.tabs(["Paste CV Content", "Upload CV File"])
    cv_text = ""
    
    with tab_paste:
        st.markdown(
            """
            <p style="color: #00E0FF;">
            **Pasting Tip:** If direct pasting is blocked, please try right-clicking the text box
            or use **Ctrl+Shift+V** (Windows) / **Cmd+Shift+V** (Mac).
            </p>
            """, unsafe_allow_html=True
        )
        st.text_area("Paste CV Content Here", value=st.session_state.get('cv_input_paste', ""), height=300,
            placeholder="Paste your resume content here...", key="cv_input_paste", label_visibility="hidden")
        cv_text = st.session_state.get('cv_input_paste', "")

    with tab_upload:
        uploaded_file_key = f"cv_input_upload_{st.session_state['reset_key_counter']}"
        uploaded_file = st.file_uploader("Upload CV or Resume", type=["txt", "pdf"], key=uploaded_file_key)

        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                st.warning("⚠️ **PDF Extraction:** Using dedicated PDF library (pypdf) for robust, cross-platform reading. If content remains incorrect, the file's text layer may be corrupted (e.g., image-only PDF).")
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
    
    if col2.button("Generate Comprehensive Job Strategy", use_container_width=True):
        if not cv_text.strip(): st.error("Please provide your CV content either by pasting or uploading a file to start the analysis.")
        else: st.session_state['cv_text_to_process'] = cv_text; st.session_state['run_search'] = True
            
    if st.session_state.get('results_displayed'):
        if st.button("Start New Search (Reset)", type="secondary", on_click=handle_reset_click): pass

    st.markdown("---")
    st.subheader("🚀 Step 3: High-Definition Generated Strategy")
    
    if st.session_state.get('run_search') and st.session_state.get('cv_text_to_process'):
        with st.container():
            st.markdown('<div class="results-card">', unsafe_allow_html=True)
            with st.spinner("Analyzing CV and Performing Real-Time Grounded Search..."):
                # Call the modified Gemini function that returns three values now
                markdown_output, skill_gap_report, citations = generate_job_strategy_from_gemini(st.session_state['cv_text_to_process'])

            st.session_state['markdown_output'] = markdown_output
            st.session_state['skill_gap_report'] = skill_gap_report
            
            st.markdown(markdown_output)

            if citations:
                st.markdown("---")
                st.markdown("#### 🔗 Grounding Sources (For Verification)")
                for i, source in enumerate(citations): st.markdown(f"**[{i+1}]** [{source.get('title')}]({source.get('uri')})")
            else: st.info("No explicit grounding sources were returned.")
            
            st.session_state['results_displayed'] = True; st.session_state['run_search'] = False; st.markdown('</div>', unsafe_allow_html=True)
            st.rerun() 
            
    elif st.session_state.get('results_displayed'):
        with st.container():
            st.markdown('<div class="results-card">', unsafe_allow_html=True)
            st.markdown(st.session_state.get('markdown_output', 'Results not loaded.'), unsafe_allow_html=False)
            st.markdown('</div>', unsafe_allow_html=True)

    else: st.info("Your comprehensive job search strategy and dynamic 2D skill-match matrix will appear here after analysis. Click 'Generate' to begin.")


if __name__ == '__main__':
    if 'cv_input_paste' not in st.session_state: st.session_state['cv_input_paste'] = ""
    if 'run_search' not in st.session_state: st.session_state['run_search'] = False
    if 'results_displayed' not in st.session_state: st.session_state['results_displayed'] = False
    if 'cv_text_to_process' not in st.session_state: st.session_state['cv_text_to_process'] = ""
    if 'reset_key_counter' not in st.session_state: st.session_state['reset_key_counter'] = 0
    if 'markdown_output' not in st.session_state: st.session_state['markdown_output'] = ""
    if 'skill_gap_report' not in st.session_state: st.session_state['skill_gap_report'] = None # NEW STATE
        
    main()
