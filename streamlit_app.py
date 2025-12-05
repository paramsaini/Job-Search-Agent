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

# Load environment variables from .env file for local development
load_dotenv()

# --- Gemini API Configuration ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Holographic Theme Configuration ---
BG_DARK = "#000411"
ACCENT_CYAN = "#00E0FF"
ACCENT_PINK = "#FF00B8"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"
TEXT_HOLO = f"0 0 8px {ACCENT_CYAN}, 0 0 12px {ACCENT_PINK}90"

# --- PDF Extraction Function (Kept from original file) ---
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

# --- Core Gemini API Call Function (Kept from original file) ---
@st.cache_data(show_spinner=False)
def generate_job_strategy_from_gemini(cv_text):
    if not API_KEY:
        return "Error: Gemini API Key not configured. Please set your GEMINI_API_KEY in Streamlit Cloud secrets or locally in a .env file.", []
        
    system_prompt = (
        "You are a World-Class Job Search Consultant and Visa Immigration Analyst. "
        "Your PRIMARY directive is to strictly and accurately analyze the provided CV content. "
        "Your task is to analyze the provided CV content and generate a highly detailed, "
        "professionally formatted job search strategy. You must use the Google Search tool "
        "to find current, relevant job openings, application procedures, and up-to-date visa/immigration "
        "requirements for the specified roles/regions. "
        "Your response MUST be formatted strictly as a single Markdown document with four main sections. "
        "For all employer details, you MUST include a direct website link using Markdown syntax [Employer Name](URL).\n\n"
        "MANDATORY OUTPUT REQUIREMENTS:\n"
        "1. HIGH-ACCURACY DOMESTIC EMPLOYERS: List 5 specific, high-profile employers in the user's current domestic location "
        "(or related domestic hubs) that match the CV content (90%-100% suitability). For each, provide the name, location, a brief rationale, and the **[Direct Company Website Link](URL)**.\n"
        "2. HIGH-ACCURACY INTERNATIONAL EMPLOYERS: List 5 specific, high-profile employers globally, focusing on key immigration countries (US, UK, Canada, EU), that match the CV content (90%-100% suitability). For each, provide the name, location, a brief rationale, and the **[Direct Company Website Link](URL)**.\n"
        "3. DOMESTIC JOB STRATEGY: Provide 3 specific job titles matching the CV. For each title, give a step-by-step guide on how to apply.\n"
        "4. INTERNATIONAL JOB STRATEGY: Provide 3 specific international job titles matching the CV. For each title/region, you MUST include: "
        "     a. The typical application steps (including necessary foreign credential evaluations). "
        "     b. The specific, relevant **visa category/code** (e.g., H-1B, Skilled Worker Visa, Blue Card). "
        "     c. Key **visa sponsorship requirements** for the employer and applicant, citing the search source."
    )

    user_query = f"Analyze this CV and generate the requested professional job strategy. The CV content is:\n\n---\n{cv_text}\n---"
    payload = {
        "contents": [{ "parts": [{ "text": user_query }] }],
        "tools": [{ "google_search": {} }],
        "systemInstruction": {
            "parts": [{ "text": system_prompt }]
        },
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(
                API_URL,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
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
                return "Error: The model returned an empty or malformed response. Please try again.", []

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                return f"An HTTP error occurred: {e}. Status Code: {response.status_code}", []
        except requests.exceptions.RequestException as e:
            return f"A network error occurred: {e}", []

    return "Error: Failed to get a response after multiple retries.", []


# --- 4. Data Simulation for 3D Plotly (Inserted) ---
@st.cache_data
def load_3d_data():
    """Generates mock data for the 3D visualization and match list."""
    # 3D Skill Data
    n_points = 50
    df_skills = pd.DataFrame({
        'X_Tech': np.random.normal(90, 10, n_points),
        'Y_Leader': np.random.normal(75, 15, n_points),
        'Z_Domain': np.random.normal(85, 8, n_points),
        'Score': np.random.randint(60, 100, n_points),
        'Skill_Type': np.random.choice(['Python', 'SQL', 'AWS', 'Soft Skill'], n_points)
    })
    df_skills = df_skills.clip(0, 100) # Ensure scores are within 0-100 range
    
    return df_skills

df_skills = load_3d_data()

# --- Custom CSS Injection (Holographic / Glassmorphism) ---
custom_css = f"""
<style>
/* Global Body and Text Styles */
.stApp {{
    background-color: {BG_DARK};
    color: white;
}}
/* Injecting the complex background texture for an 8K feel */
body {{
    background-image: 
        radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
        radial-gradient(circle at 0% 0%, rgba(0, 224, 255, 0.15), transparent 50%),
        radial-gradient(circle at 100% 100%, rgba(255, 0, 184, 0.15), transparent 50%);
    background-size: 20px 20px, 100% 100%, 100% 100%;
    background-color: {BG_DARK} !important;
}}

/* Holographic / Neon Text Effect */
.holo-text {{
    text-shadow: {TEXT_HOLO};
    font-weight: 800;
}}

/* Glassmorphism Card Style */
.glass-card {{
    background-color: rgba(255, 255, 255, 0.05); /* Translucent White */
    backdrop-filter: blur(10px) saturate(180%);
    -webkit-backdrop-filter: blur(10px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.125);
    border-radius: 1rem;
    padding: 1rem;
    transition: all 0.3s ease-in-out;
}}

.glass-card:hover {{
    border-color: {ACCENT_CYAN}90;
    box-shadow: 0 0 20px {ACCENT_CYAN}40;
}}

/* Metric Card Overrides */
div[data-testid="stMetric"] > div[data-testid="stVerticalBlock"] {{
    padding: 1.5rem 0;
    border-radius: 1rem;
    text-align: center;
    background-color: rgba(255, 255, 255, 0.05); 
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}}

/* Custom button style for high-contrast CTA */
.stButton>button {{
    background-image: linear-gradient(90deg, {ACCENT_CYAN} 0%, {ACCENT_PINK} 100%);
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 0.75rem;
    box-shadow: 0 0 15px {ACCENT_CYAN}80;
    transition: all 0.2s ease-in-out;
}}
.stButton>button:hover {{
    opacity: 0.9;
    box-shadow: 0 0 20px {ACCENT_PINK};
}}

/* Target the main button specifically for high visibility */
/* The main "Generate" button */
.stButton>button:not([type="secondary"]) {{ 
    background-image: linear-gradient(90deg, {ACCENT_CYAN} 0%, {ACCENT_PINK} 100%);
    box-shadow: 0 0 25px {ACCENT_CYAN}AA; 
    padding: 1.5rem 4rem; 
    font-size: 1.3rem;
}}
.stButton>button:hover:not([type="secondary"]) {{
    transform: scale(1.05);
}}


/* General Font Color Fix */
h1, h2, h3, h4, .stMarkdown, .stMetric > div, .css-1d391kg {{
    color: white !important;
}}

/* Fix for markdown output background */
div[data-testid="stMarkdownContainer"] {{
    color: white !important;
}}

/* Results Card Styling (Simplified for dark mode) */
.results-card {{
    background-color: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 2rem;
    padding: 4rem;
    box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.5);
    border: 2px solid rgba(0, 224, 255, 0.3);
}}

/* STRICT FIX FOR VISIBILITY OF WARNING/INFO STRIPS (Maximum Contrast) */
/* Yellow/Warning Strip Fix */
div[data-testid="stAlert"] > div:first-child[style*="background-color: rgb(255, 240, 209)"] {{
    background-color: {ACCENT_YELLOW} !important;
    color: {BG_DARK} !important; 
    border: 2px solid {ACCENT_YELLOW} !important;
    font-weight: 700;
    padding: 18px;
    margin-bottom: 15px;
    border-radius: 10px;
}}
/* Blue/Info Strip Fix */
div[data-testid="stAlert"] > div:first-child[style*="background-color: rgb(230, 242, 255)"] {{
    background-color: {ACCENT_CYAN} !important;
    color: {BG_DARK} !important; 
    border: 2px solid {ACCENT_CYAN} !important;
    font-weight: 700;
    padding: 18px;
    margin-bottom: 15px;
    border-radius: 10px;
}}
/* Text Area Fixes for dark mode */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {{
    background-color: rgba(0, 0, 0, 0.4);
    color: white;
    border: 2px solid {ACCENT_CYAN}80;
    border-radius: 1rem;
    box-shadow: 0 0 15px {ACCENT_CYAN}20;
}}
/* File Uploader Fixes for dark mode */
.stFileUploader>div>div {{
    background-color: rgba(0, 0, 0, 0.4);
    border: 2px dashed {ACCENT_PINK}80;
    color: white;
    border-radius: 1rem;
}}

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# --- Streamlit UI and Execution ---

# Function to execute when the reset button is pressed (Kept from original file)
def handle_reset_click():
    # STRICT FIX: Increment the reset counter to force the file_uploader to be recreated.
    st.session_state['reset_key_counter'] += 1
    
    # Reset input values and flow control flags
    st.session_state['cv_input_paste'] = ""
    st.session_state['cv_text_to_process'] = ""
    st.session_state['run_search'] = False
    st.session_state['results_displayed'] = False
    
    # st.rerun() is implicitly called by the state change

def main():
    # --- UI Header ---
    st.markdown('<h1 class="holo-text" style="font-size: 3rem; margin-bottom: 0.5rem; text-align: center;">🤖 AI Recruitment Matrix V3.0</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.25rem; color: #9CA3AF; text-align: center;">Analyze your CV against global employers using grounded Gemini AI.</p>', unsafe_allow_html=True)
    st.markdown("---")

    # --- 1. 3D Visualization (The Centerpiece) ---
    st.markdown('<h2 class="holo-text" style="margin-top: 2rem;">3D Skill Matrix Projection</h2>', unsafe_allow_html=True)
    st.markdown("""
    <p style='color: #ccc;'>
        The interactive 3D plot visualizes your skill profile across core dimensions: 
        <span style='color: #FF00B8; font-weight: bold;'>Technical Depth (X)</span>, 
        <span style='color: #00E0FF; font-weight: bold;'>Leadership Potential (Y)</span>, and 
        <span style='color: #10B981; font-weight: bold;'>Domain Expertise (Z)</span>. 
        Clusters represent highly compatible job roles.
    </p>
    """, unsafe_allow_html=True)

    # Create 3D Plotly Scatter Plot
    fig = px.scatter_3d(
        df_skills, 
        x='X_Tech', 
        y='Y_Leader', 
        z='Z_Domain',
        color='Skill_Type',
        size='Score',
        color_discrete_map={
            'Python': ACCENT_CYAN,
            'SQL': ACCENT_PINK,
            'AWS': ACCENT_GREEN,
            'Soft Skill': ACCENT_YELLOW
        },
        title="Holographic Skill Data Cloud",
        height=700
    )

    # Apply 3D Holographic Styling to Plotly
    fig.update_layout(
        plot_bgcolor=BG_DARK,
        paper_bgcolor=BG_DARK,
        font=dict(color="white"),
        scene=dict(
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=ACCENT_CYAN + "40", title_font=dict(color=ACCENT_CYAN), tickfont=dict(color="white")),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=ACCENT_PINK + "40", title_font=dict(color=ACCENT_PINK), tickfont=dict(color="white")),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=ACCENT_GREEN + "40", title_font=dict(color=ACCENT_GREEN), tickfont=dict(color="white")),
            aspectmode='cube'
        ),
        legend_title_text='Skill Clusters',
        hoverlabel=dict(bgcolor="black", font_size=16, font_color="white")
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    # --- 2. Input Area (Kept from original file) ---
    st.subheader("📝 Step 2: Input Your Professional Profile")
    
    # Dual input for flexibility: Upload or Paste
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
        
        # 1. Define Paste Widget (Safe state setting)
        st.text_area(
            "Paste CV Content Here",
            value=st.session_state.get('cv_input_paste', ""),  # Corrected to use safe get
            height=300,
            placeholder="Paste your resume content here...",
            key="cv_input_paste",
            label_visibility="hidden"
        )
        
        # Read Paste input from state
        cv_text = st.session_state.get('cv_input_paste', "")

    with tab_upload:
        # 2. Define Upload Widget (Safe state setting using dynamic key)
        uploaded_file_key = f"cv_input_upload_{st.session_state['reset_key_counter']}"
        st.file_uploader(
            "Upload CV or Resume",
            type=["txt", "pdf"],
            # Use dynamic key for graceful reset
            key=uploaded_file_key
        )
        
        # Read Upload input from state
        uploaded_file = st.session_state.get(uploaded_file_key, None)

        if uploaded_file is not None:
            # If a file is uploaded, process it and overwrite cv_text
            
            if uploaded_file.type == "application/pdf":
                st.warning("⚠️ **PDF Extraction:** Using dedicated PDF library (pypdf) for robust, cross-platform reading. If content remains incorrect, the file's text layer may be corrupted (e.g., image-only PDF).")
                try:
                    cv_text = extract_text_from_pdf(uploaded_file)
                except Exception as e:
                    st.error(f"Failed to read PDF. Ensure text is selectable. Error: {e}")
                    cv_text = ""
            
            else: # Handle TXT file types
                try:
                    uploaded_file.seek(0)
                    raw_bytes = uploaded_file.read()
                    try:
                        string_data = raw_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        string_data = raw_bytes.decode('windows-1252', errors='replace')
                        st.info("File encoding resolved using fallback (Windows-1252). Please check characters.")
                        
                    cv_text = string_data
                except Exception as e:
                    st.error(f"Error reading TXT file: {e}")
                    cv_text = ""
            
            # --- Strict Accuracy Check ---
            if cv_text and len(cv_text.strip()) < 50: 
                st.error("❌ **Reading Failure:** Extracted text is too short or empty. This will cause the AI to generate completely false information. Please ensure the file contains readable text.")
                cv_text = ""
                
        # --- Strict Error Fix: Resetting State if Input Failed ---
        if not cv_text.strip() and st.session_state.get('run_search'):
            st.session_state['run_search'] = False
            st.session_state['cv_text_to_process'] = ""
            st.warning("Input cancelled due to empty CV content.")
            
    st.markdown("---")
    
    # Button in the center
    col1, col2, col3 = st.columns([1, 2, 1])
    
    if col2.button("Generate Comprehensive Job Strategy", use_container_width=True):
        if not cv_text.strip():
            st.error("Please provide your CV content either by pasting or uploading a file to start the analysis.")
        else:
            st.session_state['cv_text_to_process'] = cv_text 
            st.session_state['run_search'] = True
            
    # Conditional Reset Button
    if st.session_state.get('results_displayed'):
        # Pass the callback function directly to on_click
        if st.button("Start New Search (Reset)", type="secondary", on_click=handle_reset_click):
            pass

    # --- Output Area ---
    st.markdown("---")
    st.subheader("🚀 Step 3: High-Definition Generated Strategy")
    
    # --- Processing and Output Logic (Kept from original file) ---
    if st.session_state.get('run_search') and st.session_state.get('cv_text_to_process'):
        with st.container():
            st.markdown('<div class="results-card">', unsafe_allow_html=True)
            
            with st.spinner("Analyzing CV and Performing Real-Time Grounded Search (This may take up to 20 seconds for in-depth analysis and visa checks)..."):
                markdown_output, citations = generate_job_strategy_from_gemini(st.session_state['cv_text_to_process'])

            st.markdown(markdown_output)

            if citations:
                st.markdown("---")
                st.markdown("#### 🔗 Grounding Sources (For Verification)")
                for i, source in enumerate(citations):
                    st.markdown(f"**[{i+1}]** [{source.get('title')}]({source.get('uri')})")
            else:
                st.info("No explicit grounding sources were returned. Output is based on broad knowledge and specific prompt instructions.")
            
            st.session_state['results_displayed'] = True
            st.session_state['run_search'] = False 
            st.markdown('</div>', unsafe_allow_html=True)
    elif st.session_state.get('results_displayed'):
        pass 
    else:
        st.info("Your comprehensive job search strategy will appear here after analysis. Click 'Generate' to begin.")


if __name__ == '__main__':
    # --- STRICT SESSION STATE INITIALIZATION (Kept from original file) ---
    if 'cv_input_paste' not in st.session_state:
        st.session_state['cv_input_paste'] = ""
    if 'run_search' not in st.session_state:
        st.session_state['run_search'] = False
    if 'results_displayed' not in st.session_state:
        st.session_state['results_displayed'] = False
    if 'cv_text_to_process' not in st.session_state:
        st.session_state['cv_text_to_process'] = ""
    if 'reset_key_counter' not in st.session_state:
        st.session_state['reset_key_counter'] = 0
        
    main()
