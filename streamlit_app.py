# --- 2025-12-08_FINAL_ULTIMATE_STABILITY_V11_POLISHED_FINAL ---
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
    Based on the following CV and the R
