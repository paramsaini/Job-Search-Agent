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
# FIX: DEFINITION OF custom_css (AGGRESSIVE VISIBILITY FIX)
# ------------------------------------------------
custom_css = f"""
<style>
/* Streamlit standard cleanup */
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* 1. MOVING BACKGROUND IMPLEMENTATION (OPTIMIZED) */
.stApp {{
    background-color: {BG_DARK}; 
    color: white; 
    position: relative; 
}}

/* Create a fixed, full-screen pseudo-element for the animated background */
.stApp::before {{
    content: '';
    position: fixed; 
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -100; 
    
    /* Load the background image/GIF/WebP (ensure this file is uploaded!) */
    background: url('aequor_background_loop.gif') no-repeat center center fixed; 
    background-size: cover; 
    
    /* Apply animation layer for dynamic feel */
    background-image: linear-gradient(45deg, rgba(0,0,0,0.8), rgba(0,0,0,0.7)),
                      radial-gradient(ellipse at bottom, {ACCENT_CYAN}40, {ACCENT_ORANGE}40, transparent);
    background-size: 400% 400%;
    
    animation: gradient-motion 30s ease infinite; 
    opacity: 0.85; 
}}

@keyframes gradient-motion {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}


/* --- VISIBILITY FIXES (Aggressively set all text to white) --- */
/* Target general text, titles, and labels */
section.main, body, p, label, div, h1, h2, h3, h4, span, ul, li {{
    color: white !important;
}}

/* Target specific input elements and their labels */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stFileUploader > label {{
    color: white !important;
    background-color: rgba(255, 255, 255, 0.05);
    border-color: {ACCENT_CYAN}50;
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
    position: relative; 
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
    if not QDRANT_API_KEY or not
