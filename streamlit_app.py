import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv
import io
import pypdf

# Load environment variables from .env file for local development
load_dotenv() 

# --- Gemini API Configuration ---
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- PDF Extraction Function ---
def extract_text_from_pdf(uploaded_file):
    """Uses pypdf to extract text from a PDF file stream."""
    try:
        pdf_reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Failed to process PDF with pypdf. Error: {e}")
        return ""

# --- Core Gemini API Call Function ---

@st.cache_data(show_spinner=False)
def generate_job_strategy_from_gemini(cv_text):
    # (API call logic remains the same)
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
        "    a. The typical application steps (including necessary foreign credential evaluations). "
        "    b. The specific, relevant **visa category/code** (e.g., H-1B, Skilled Worker Visa, Blue Card). "
        "    c. Key **visa sponsorship requirements** for the employer and applicant, citing the search source."
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


# --- Streamlit UI and Execution ---

# Function to clear the state keys used by the input widgets
def clear_input_widgets_state():
    st.session_state['cv_input_paste'] = ""
    st.session_state['cv_input_upload'] = None 
    st.session_state['cv_text_to_process'] = ""
    st.session_state['run_search'] = False
    st.session_state['results_displayed'] = False

# Function to execute when the reset button is pressed
def handle_reset_click():
    clear_input_widgets_state()
    st.rerun()

def main():
    st.set_page_config(
        page_title="Gemini CV Job Strategy Generator",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # --- ABSOLUTE VISUALIZATION OVERHAUL (NEON BLUE / HIGH CONTRAST) ---
    st.markdown("""
    <style>
    /* Overall Background and Font - Studio Light (Bright and Clean) */
    .stApp {
        background-color: #f8faff; /* Very light, professional off-white */
        color: #1c2541; /* Dark professional text */
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3, h4, .main-header {
        color: #007bff; /* Bright, vibrant blue */
    }
    .main-header {
        text-align: center;
        font-size: 3.5rem; /* Larger Title */
        font-weight: 900;
        margin-bottom: 3rem;
        text-shadow: 0 5px 10px rgba(0, 123, 255, 0.4); /* Stronger blue glow */
    }
    
    /* Input Fields (Text Area) - Ultra Crisp */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff;
        color: #1c2541; 
        border-radius: 1.2rem; /* More rounded */
        border: 4px solid #007bff; /* Thick, pronounced blue border */
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.25); /* Max shadow */
        padding: 1.5rem;
    }
    
    /* FILE UPLOADER VISIBILITY FIX (Targets the file name/status display) */
    .stFileUploader>div>div {
        background-color: #ffffff;
        border: 4px dashed #007bff; 
        color: #1c2541;
        border-radius: 1.2rem;
        padding: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    }
    
    /* FIX: Ensure uploaded file name and status is highly visible */
    .stFileUploader span[data-testid="stFileUploaderFile"] {
        color: #007bff !important; /* Force NEON BLUE text */
        font-weight: 800;
        font-size: 1.1rem;
    }
    /* FIX: Eliminate dark strip (often caused by dropzone rendering) */
    .stFileUploader div[data-testid="stFileUploaderDropzone"] {
        background-color: #f8faff !important; /* Match app background */
        border: none !important;
        padding: 0 !important;
    }

    /* Tabs (Paste/Upload) Styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 1.3rem;
        font-weight: 900;
        color: #007bff; /* Make tabs bright */
    }
    
    /* Main Action Button - VIBRANT */
    .stButton>button {
        background-color: #28a745; 
        color: white;
        font-weight: 900;
        border-radius: 9999px; 
        padding: 1.5rem 4rem; /* Massive padding */
        transition: all 0.4s ease-in-out;
        box-shadow: 0 15px 40px rgba(40, 167, 69, 0.6); /* Maximum glow */
        border: none;
        font-size: 1.3rem;
    }
    .stButton>button:hover {
        background-color: #218838; 
        transform: scale(1.1); 
    }
    
    /* Results Card - Ultra Clean and Structured */
    .results-card {
        background-color: #ffffff;
        border-radius: 2rem; /* Extreme rounding */
        padding: 4rem;
        box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.3); /* The ultimate shadow */
        border: 2px solid #e0e0e0;
    }
    
    /* STRICT FIX FOR VISIBILITY OF WARNING/INFO STRIPS */
    div[data-testid="stAlert"] > div:first-child[style*="background-color: rgb(255, 240, 209)"] {
        background-color: #ffc107 !important; 
        color: #343a40 !important; 
        border: 2px solid #ff9800 !important;
        font-weight: 700;
        padding: 18px;
        margin-bottom: 15px;
        border-radius: 10px;
    }
    div[data-testid="stAlert"] > div:first-child[style*="background-color: rgb(230, 242, 255)"] {
        background-color: #007bff !important; 
        color: #ffffff !important; 
        border: 2px solid #0056b3 !important;
        font-weight: 700;
        padding: 18px;
        margin-bottom: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)


    st.markdown('<div class="main-header">✨ AI Job Search Consultant</div>', unsafe_allow_html=True)
    st.markdown("---")

    # --- Input Area ---
    st.container()
    st.subheader("📝 Step 1: Input Your Professional Profile")
    
    # Dual input for flexibility: Upload or Paste
    tab_paste, tab_upload = st.tabs(["Paste CV Content", "Upload CV File"])
    
    cv_text = ""
    
    with tab_paste:
        st.markdown(
            """
            <p style="color: #007bff;">
            **Pasting Tip:** If direct pasting is blocked, please try right-clicking the text box
            or use **Ctrl+Shift+V** (Windows) / **Cmd+Shift+V** (Mac).
            </p>
            """, unsafe_allow_html=True
        )
        st.session_state['cv_input_paste'] = st.text_area(
            "Paste CV Content Here",
            value=st.session_state['cv_input_paste'], 
            height=300,
            placeholder="Paste your resume content here...",
            key="cv_input_paste",
            label_visibility="hidden"
        )
        cv_text = st.session_state['cv_input_paste']

    with tab_upload:
        st.session_state['cv_input_upload'] = st.file_uploader(
            "Upload CV or Resume",
            type=["txt", "pdf"],
            key="cv_input_upload"
        )
        uploaded_file = st.session_state['cv_input_upload']

        if uploaded_file is not None:
            uploaded_file.seek(0) 
            
            if uploaded_file.type == "application/pdf":
                 st.warning("⚠️ **PDF Extraction:** Using dedicated PDF library (pypdf) for robust, cross-platform reading. If content remains incorrect, the file's text layer may be corrupted (e.g., image-only PDF).")
                 try:
                     cv_text = extract_text_from_pdf(uploaded_file)
                 except Exception as e:
                     st.error(f"Failed to read PDF. Ensure text is selectable. Error: {e}")
                     cv_text = ""
            
            else: # Handle TXT file types
                try:
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
        if st.button("Start New Search (Reset)", type="secondary", on_click=handle_reset_click):
            pass

    # --- Output Area ---
    st.markdown("---")
    st.subheader("🚀 Step 2: High-Definition Generated Strategy")
    
    # --- Processing and Output Logic ---
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
    # --- STRICT SESSION STATE INITIALIZATION ---
    if 'cv_input_paste' not in st.session_state:
        st.session_state['cv_input_paste'] = ""
    if 'cv_input_upload' not in st.session_state:
        st.session_state['cv_input_upload'] = None
    if 'run_search' not in st.session_state:
        st.session_state['run_search'] = False
    if 'results_displayed' not in st.session_state:
        st.session_state['results_displayed'] = False
    if 'cv_text_to_process' not in st.session_state:
        st.session_state['cv_text_to_process'] = ""
        
    main()
