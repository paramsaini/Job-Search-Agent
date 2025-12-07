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
# FIX: DEFINITION OF custom_css (Black screen fix included)
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
