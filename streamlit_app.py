import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv
import io # Import for file handling

# Load environment variables from .env file for local development
load_dotenv() 

# --- Gemini API Configuration ---
# Priority: 1. Streamlit Secrets (for cloud) 2. OS Environment (for local)
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Core Gemini API Call Function ---

@st.cache_data(show_spinner=False)
def generate_job_strategy_from_gemini(cv_text):
    """
    Analyzes CV text, performs a grounded search for jobs, and generates
    a professional, detailed application strategy including visa requirements.
    """
    if not API_KEY:
        return "Error: Gemini API Key not configured. Please set your GEMINI_API_KEY in Streamlit Cloud secrets or locally in a .env file.", []
        
    # 1. Define the System Instruction (ENHANCED FOR LINKS AND STRUCTURE)
    system_prompt = (
        "You are a World-Class Job Search Consultant and Visa Immigration Analyst. "
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

    # 2. Define the User Query
    user_query = f"Analyze this CV and generate the requested professional job strategy. The CV content is:\n\n---\n{cv_text}\n---"

    # 3. Construct the API Payload with Grounding and System Instruction
    payload = {
        "contents": [{ "parts": [{ "text": user_query }] }],
        "tools": [{ "google_search": {} }],
        "systemInstruction": {
            "parts": [{ "text": system_prompt }]
        },
    }

    # Implement Exponential Backoff
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

def main():
    st.set_page_config(
        page_title="Gemini CV Job Strategy Generator",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # --- BOLDER, MORE PROFESSIONAL STYLING ---
    st.markdown("""
    <style>
    /* Overall Background and Font */
    .stApp {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); /* Lighter, but brighter blue gradient */
        color: #1a237e; /* Dark Blue Text */
    }
    
    /* Input Fields (Text Area, Upload Button) */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stFileUploader>div>div {
        background-color: #ffffff;
        border-radius: 0.75rem;
        border: 2px solid #64b5f6; /* Visible Blue Border */
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15); /* Stronger Shadow */
        color: #263238; /* Dark text for clarity */
    }
    
    /* Tabs (Paste/Upload) Styling for better visibility */
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a237e;
    }

    /* Main Action Button */
    .stButton>button {
        background-color: #0b50b7; /* Deep Blue */
        color: white;
        font-weight: 800;
        border-radius: 9999px; 
        padding: 0.8rem 2.5rem;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 8px 20px -5px rgba(11, 80, 183, 0.6); /* Bolder Shadow */
    }
    .stButton>button:hover {
        background-color: #1e40af; /* Darker Blue on hover */
        transform: scale(1.05); /* Slightly bigger effect */
    }
    
    /* Header and Card Styling */
    .main-header {
        text-align: center;
        color: #0d47a1; /* Even darker blue for emphasis */
        font-size: 2.8rem;
        font-weight: 900;
        margin-bottom: 1.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .results-card {
        background-color: #ffffff;
        border-radius: 1.2rem;
        padding: 2.5rem;
        box-shadow: 0 15px 25px -5px rgba(0, 0, 0, 0.2); /* Very prominent shadow */
    }
    /* Subheaders for generated content */
    .results-card h4 {
        color: #1a237e;
        border-bottom: 2px solid #e3f2fd;
        padding-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)


    st.markdown('<div class="main-header">✨ AI Job Search Consultant</div>', unsafe_allow_html=True)
    st.markdown("---")

    # --- Input Area (Clear Tab/Section) ---
    st.container()
    st.subheader("📝 Step 1: Input Your Professional Profile")
    
    # Dual input for flexibility: Upload or Paste
    tab_paste, tab_upload = st.tabs(["Paste CV Content (Recommended)", "Upload CV File (.txt / .pdf)"])
    
    cv_text = ""
    
    with tab_paste:
        st.markdown(
            """
            **Pasting Tip:** If direct pasting is blocked, please try right-clicking the text box
            or use **Ctrl+Shift+V** (Windows) / **Cmd+Shift+V** (Mac).
            """
        )
        cv_text = st.text_area(
            "Paste CV Content Here",
            height=300,
            placeholder="Paste your resume content here...",
            key="cv_input_paste",
            label_visibility="hidden"
        )

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload CV or Resume",
            type=["txt", "pdf"],
            key="cv_input_upload"
        )
        if uploaded_file is not None:
            
            if uploaded_file.type == "application/pdf":
                 st.warning("For PDF files, the app will attempt to read plain text, but complex formatting may be lost. Using .txt is recommended.")
                 
            try:
                # Robust Encoding Detection
                raw_bytes = uploaded_file.read()
                try:
                    string_data = raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    string_data = raw_bytes.decode('windows-1252', errors='replace')
                    st.info("File was read using a fallback encoding (Windows-1252). Please check for any strange characters.")
                    
                cv_text = string_data
                uploaded_file.seek(0)
                
            except Exception as e:
                st.error(f"Error reading file: {e}")
                cv_text = ""
                

    st.markdown("---")
    
    # Button in the center
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Generate Comprehensive Job Strategy", use_container_width=True):
            if not cv_text.strip():
                st.error("Please provide your CV content either by pasting or uploading a file to start the analysis.")
            else:
                st.session_state['run_search'] = True
                
    # --- Output Area (Clear Tab/Section) ---
    st.markdown("---")
    st.subheader("🚀 Step 2: High-Definition Generated Strategy")
    
    if st.session_state.get('run_search'):
        with st.container():
            st.markdown('<div class="results-card">', unsafe_allow_html=True)
            
            with st.spinner("Analyzing CV and Performing Real-Time Grounded Search (This may take up to 20 seconds for in-depth analysis and visa checks)..."):
                markdown_output, citations = generate_job_strategy_from_gemini(cv_text)

            st.markdown(markdown_output)

            if citations:
                st.markdown("---")
                st.markdown("#### 🔗 Grounding Sources (For Verification)")
                for i, source in enumerate(citations):
                    st.markdown(f"**[{i+1}]** [{source.get('title')}]({source.get('uri')})")
            else:
                st.info("No explicit grounding sources were returned. Output is based on broad knowledge and specific prompt instructions.")
            
            st.session_state['run_search'] = False 
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    if 'run_search' not in st.session_state:
        st.session_state['run_search'] = False
    main()
