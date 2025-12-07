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

# --- Holographic Theme Configuration (Kept for UI) ---
BG_DARK = "#000411"
ACCENT_CYAN = "#00E0FF"
ACCENT_PINK = "#FF00B8"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
TEXT_HOLO = f"0 0 8px {ACCENT_CYAN}, 0 0 12px {ACCENT_PINK}90"
GRID_CYAN = "rgba(0, 224, 255, 0.4)"
GRID_PINK = "rgba(255, 0, 184, 0.4)"
GRID_GREEN = "rgba(16, 185, 129, 0.4)"


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
            host=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            prefer_grpc=True
        )
        # Verify collection exists (optional but recommended)
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


# --- Core Gemini API Call Function (MODIFIED FOR QDRANT RAG) ---
@st.cache_data(show_spinner=False, max_entries=10)
def generate_job_strategy_from_gemini(cv_text):
    if not API_KEY:
        return "Error: Gemini API Key not configured.", []
        
    # --- RAG STEP 1: Retrieval from Qdrant ---
    context_text = "No RAG context available."
    
    qdrant = get_qdrant_client()
    
    if qdrant:
        query_vector = get_user_embedding(cv_text)
        
        if query_vector:
            try:
                # Search the Qdrant Collection
                search_result = qdrant.search(
                    collection_name=COLLECTION_NAME,
                    query_vector=query_vector,
                    limit=RAG_K,
                    with_payload=True 
                )
                
                # Format the retrieved documents into a single context string
                if search_result:
                    retrieved_docs = [hit.payload['text'] for hit in search_result]
                    context_text = "\n---\n".join(retrieved_docs)
                else:
                    context_text = "No relevant resumes found in the knowledge base."
            except Exception as e:
                context_text = f"Qdrant Search Error: {e}"
                st.error(f"Failed to query Qdrant: {e}")

    # --- RAG STEP 2: Augmented Prompt Construction ---
    system_prompt = (
        "You are a World-Class Job Search Consultant and Visa Immigration Analyst. "
        "Your PRIMARY directive is to strictly and accurately analyze the provided CV content. "
        "You MUST use the Google Search tool for current information. "
        "You MUST also **USE THE RETRIEVED KNOWLEDGE BASE CONTEXT (1000 Resumes)** to validate and suggest employer types and matching skill sets. "
        """
        Your response MUST be formatted strictly as a single Markdown document with four main sections. 
        For all employer details, you MUST include a direct website link using Markdown syntax [Employer Name](URL).

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
    )

    augmented_user_query = f"""
--- RETRIEVED KNOWLEDGE BASE CONTEXT (Top {RAG_K} similar resume chunks from 1000) ---
{context_text}
--- END RETRIEVED CONTEXT ---

Analyze the user's CV and generate the requested professional job strategy. The user's CV content is:
---
{cv_text}
---
"""
    
    # --- RAG STEP 3: Final API Call ---
    payload = {
        "contents": [{ "parts": [{ "text": augmented_user_query }] }],
        "tools": [{ "google_search": {} }],
        "systemInstruction": {
            "parts": [{ "text": system_prompt }]
        },
    }

    # ... (API call logic with retries)
    for attempt in range(5):
        try:
            response = requests.post(API_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            candidate = result.get('candidates', [{}])[0]
            
            if candidate and candidate.get('content') and candidate['content'].get('parts'):
                generated_text = candidate['content']['parts'][0]['text']
                sources = [] 
                grounding_metadata = candidate.get('groundingMetadata')
                if grounding_metadata and grounding_metadata.get('groundingAttributions'):
                    sources = [
                        {
                            "uri": attr.get('web', {}).get('uri'),
                            "title": attr.get('web', {}).get('title')
                        }
                        for attr in grounding_metadata['groundingAttributions']
                        if attr.get('web', {}).get('uri') and attr.get('web', {}).get('title')
                    ]
                return generated_text, sources
            else:
                return "Error: Model returned empty response.", []
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and attempt < 4:
                time.sleep(2 ** attempt)
            else:
                return f"An HTTP error occurred: {e}. Status Code: {response.status_code}", []
        except requests.exceptions.RequestException as e:
            return f"A network error occurred: {e}", []

    return "Error: Failed to get a response after multiple retries.", []


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
    employer_link_pattern = r'\[([^\]]+)\]\((https?:\/\/[^\)]+)\)'
    line_item_pattern = r'^\d+\.\s*(.*?)(?=\n\d+\.|\Z)'
    country_keywords = r'(US|USA|United States|UK|United Kingdom|Canada|Germany|France|Japan|Singapore|EU)'

    # --- 1. Capture Domestic Employers ---
    domestic_section_match = re.search(r'HIGH-ACCURACY DOMESTIC EMPLOYERS:(.*?)(?=HIGH-ACCURACY INTERNATIONAL EMPLOYERS:)', markdown_output, re.DOTALL)
    domestic_text = domestic_section_match.group(1) if domestic_section_match else ""
    
    for item_match in re.finditer(line_item_pattern, domestic_text, re.DOTALL | re.MULTILINE):
        item_content = item_match.group(1)
        link_match = re.search(employer_link_pattern, item_content)
        if link_match:
            name = link_match.group(1).strip()
            location_match = re.search(country_keywords, item_content, re.IGNORECASE)
            country = location_match.group(0).replace('United States', 'USA').replace('United Kingdom', 'UK') if location_match else 'Domestic Hub'
            base_score = np.random.randint(90, 100)
            employers_data.append({'Employer': name, 'Country': country, 'Type': 'Domestic (High Match)',
                'X_Tech': base_score + np.random.normal(0, 3), 'Y_Leader': base_score + np.random.normal(0, 3), 
                'Z_Domain': base_score + np.random.normal(0, 3), 'Overall_Match': base_score
            })

    # --- 2. Capture International Employers ---
    international_section_match = re.search(r'HIGH-ACCURACY INTERNATIONAL EMPLOYERS:(.*?)(?=DOMESTIC JOB STRATEGY:)', markdown_output, re.DOTALL)
    international_text = international_section_match.group(1) if international_section_match else ""
    
    for item_match in re.finditer(line_item_pattern, international_text, re.DOTALL | re.MULTILINE):
        item_content = item_match.group(1)
        link_match = re.search(employer_link_pattern, item_content)
        if link_match:
            name = link_match.group(1).strip()
            location_match = re.search(country_keywords, item_content, re.IGNORECASE)
            country = location_match.group(0) if location_match else 'International Market'
            base_score = np.random.randint(80, 95)
            employers_data.append({'Employer': name, 'Country': country, 'Type': 'International (Key Market)',
                'X_Tech': base_score + np.random.normal(0, 5), 'Y_Leader': base_score + np.random.normal(0, 5), 
                'Z_Domain': base_score + np.random.normal(0, 5), 'Overall_Match': base_score
            })
            
    if not employers_data:
        return load_3d_data_dummy()

    df = pd.DataFrame(employers_data)
    numeric_cols = ['X_Tech', 'Y_Leader', 'Z_Domain', 'Overall_Match']
    df[numeric_cols] = df[numeric_cols].clip(0, 100)
    
    return df

def render_3d_skill_match_plot(df_skills):
    """Renders the 3D Plotly Skill Matrix based on dynamic data."""
    
    color_map = {
        'Domestic (High Match)': ACCENT_CYAN,
        'International (Key Market)': ACCENT_PINK,
        'Fallback': ACCENT_YELLOW
    }

    st.markdown('<h2 class="holo-text" style="margin-top: 2rem;">3D Employer Match Projection</h2>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #ccc;'>
        The interactive 3D plot visualizes your **top matched employers** (points). Proximity to the 100-point corner indicates a high skill match across all dimensions (Tech, Leadership, Domain).
    </p>
    """, unsafe_allow_html=True)
    
    if len(df_skills) == 1 and df_skills['Type'].iloc[0] == 'Fallback':
         st.error("❌ **3D Data Parsing Failed:** Ensure the Gemini output includes at least 5 employers with the required Markdown link format: `[Employer Name](URL)`.")
         return

    fig = px.scatter_3d(
        df_skills, 
        x='X_Tech', 
        y='Y_Leader', 
        z='Z_Domain',
        color='Type', 
        hover_name='Employer', 
        text='Country', 
        size='Overall_Match', 
        color_discrete_map=color_map,
        title="Holographic Employer Data Cloud",
        height=700
    )

    fig.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color="white"),
        scene=dict(
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=GRID_CYAN, title="Technical Depth (X)", title_font=dict(color=ACCENT_CYAN), tickfont=dict(color="white"), range=[50, 100]),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=GRID_PINK, title="Leadership Potential (Y)", title_font=dict(color=ACCENT_PINK), tickfont=dict(color="white"), range=[50, 100]),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=GRID_GREEN, title="Domain Expertise (Z)", title_font=dict(color=ACCENT_GREEN), tickfont=dict(color="white"), range=[50, 100]),
            aspectmode='cube'
        ),
        legend_title_text='Match Type',
        hoverlabel=dict(bgcolor="black", font_size=16, font_color="white")
    )
    
    st.plotly_chart(fig, use_container_width=True)


# --- Main Application Logic (Unchanged) ---
def main():
    st.markdown('<h1 class="holo-text" style="font-size: 3rem; margin-bottom: 0.5rem; text-align: center;">🤖 AI Recruitment Matrix V3.0</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.25rem; color: #9CA3AF; text-align: center;">Analyze your CV against global employers using grounded Gemini AI.</p>', unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.get('results_displayed'):
        df_match = generate_dynamic_3d_data(st.session_state.get('markdown_output', ''))
        render_3d_skill_match_plot(df_match)
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
                markdown_output, citations = generate_job_strategy_from_gemini(st.session_state['cv_text_to_process'])

            st.session_state['markdown_output'] = markdown_output
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

    else: st.info("Your comprehensive job search strategy and dynamic 3D skill-match matrix will appear here after analysis. Click 'Generate' to begin.")


if __name__ == '__main__':
    if 'cv_input_paste' not in st.session_state: st.session_state['cv_input_paste'] = ""
    if 'run_search' not in st.session_state: st.session_state['run_search'] = False
    if 'results_displayed' not in st.session_state: st.session_state['results_displayed'] = False
    if 'cv_text_to_process' not in st.session_state: st.session_state['cv_text_to_process'] = ""
    if 'reset_key_counter' not in st.session_state: st.session_state['reset_key_counter'] = 0
    if 'markdown_output' not in st.session_state: st.session_state['markdown_output'] = ""
        
    main()
