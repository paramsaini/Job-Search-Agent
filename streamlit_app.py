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
system_prompt = "" 

# --- RAG Configuration ---
COLLECTION_NAME = 'resume_knowledge_base'
RAG_K = 10 # Number of top documents to retrieve

# --- Holographic Theme Configuration (UPDATED for maximum effect and new colors) ---
BG_DARK = "#000000" # Pure black background for max contrast
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00" 
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
TEXT_HOLO = f"0 0 10px {ACCENT_CYAN}, 0 0 20px {ACCENT_ORANGE}90"
GRID_CYAN = "rgba(0, 255, 255, 0.6)" 
GRID_ORANGE = "rgba(255, 140, 0, 0.6)" 
GRID_GREEN = "rgba(16, 185, 129, 0.6)"

# ------------------------------------------------
# FIX: DEFINITION OF custom_css (Syntax Error Corrected)
# ------------------------------------------------
custom_css = f"""
<style>
/* Streamlit standard cleanup */
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* Base App Styling & Background */
.stApp {{
    background-color: {BG_DARK};
    color: white; /* Base text color */
}}

/* FIX FOR BLACK SCREEN: Ensure all primary text/input labels are white */
/* target the main content block and generic text elements */
section.main, body, p, label, div {{
    color: white !important;
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
    background-color: {ACCENT_ORANGE}; 
    border: 2px solid {ACCENT_ORANGE}; 
    border-radius: 12px;
    font-weight: bold;
    box-shadow: 0 0 10px {ACCENT_ORANGE}50, 0 0 20px {ACCENT_ORANGE}30; 
    transition: all 0.3s ease-in-out;
}}

/* Custom Card for Results/Reports */
.results-card, .glass-card {{
    padding: 20px;
    margin: 15px 0;
    border-radius: 15px;
    border: 2px solid {ACCENT_CYAN}40;
    background: rgba(16, 185, 129, 0.05);
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

/* Strategy Funnel CSS */
.funnel-step {{
    background-color: {ACCENT_CYAN}10;
    padding: 10px;
    margin-bottom: 5px;
    text-align: center;
    border-left: 5px solid {ACCENT_CYAN};
    font-weight: bold;
    color: {ACCENT_CYAN};
    border-radius: 4px;
}}
/* Custom Progress Bar Styling (to match theme) */
.stProgress > div > div > div > div {{
    background-color: {ACCENT_CYAN};
    animation: gradient 2s ease infinite;
}}
@keyframes gradient {{
    0% {{background-color: {ACCENT_CYAN};}}
    50% {{background-color: {ACCENT_ORANGE};}}
    100% {{background-color: {ACCENT_CYAN};}}
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
            "predictive_score": {"type": "INTEGER", "description": "Percentage score (0-100) comparing user
