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

# --- Configuration Placeholder ---
# FIX: Define system_prompt as an empty string to avoid NameError issues in the global scope.
system_prompt = "" 

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
    # The system_prompt is defined globally as an empty string now.
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
