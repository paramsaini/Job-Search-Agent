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
        
    # 1. Define the System Instruction
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

# Function to reset the input fields
def reset_inputs():
    # Resetting the session states tied to the input widgets and process flow
    st.session_state['cv_input_paste'] = ""
    st.session_state['cv_input_upload'] = None # Clear file uploader
    st.session_state['run_search'] = False
    st.session_state['results_displayed'] = False
    st.session_state['cv_text_to_process'] = ""

def main():
    st.set_page_config(
        page_title="Gemini CV Job Strategy Generator",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # --- FINAL, STRICT VISUAL STYLING (STUDIO LIGHT / 8K LOOK) ---
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
        font-size: 3.2rem;
        font-weight: 900;
        margin-bottom: 2.5rem;
        text-shadow: 0 4px 8px rgba(0, 123, 255, 0.2); /* Soft blue shadow */
    }
    
    /* Input Fields (Text Area, File Uploader) - Crisp and Shadowed */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #ffffff;
        color: #1c2541; 
        border-radius: 1rem;
        border: 2px solid #007bff; /* Prominent blue border */
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15); 
        padding: 1rem;
    }
    .stFileUploader>div>div {
        background-color: #ffffff;
        border: 3px dashed #007bff; /* Even more prominent dashed border */
        color: #1c2541;
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Tabs (Paste/Upload) Styling */
    .stTabs [data-baseweb="tab"] {
        font-size: 1.25rem;
        font-weight: 700;
        color: #5a5a5a;
    }

    /* Main Action Button - VIBRANT */
    .stButton>button {
        background-color: #28a745; /* VIBRANT GREEN for Go/Generate */
        color: white;
        font-weight: 900;
        border-radius: 9999px; 
        padding: 1.2rem 3.5rem;
        transition: all 0.4s ease-in-out;
        box-shadow: 0 12px 30px rgba(40, 167, 69, 0.5); /* Glowing green shadow */
        border: none;
    }
    .stButton>button:hover {
        background-color: #218838; 
        transform: scale(1.1); 
    }
    
    /* Results Card - Ultra Clean and Structured */
    .results-card {
        background-color: #ffffff;
        border-radius: 1.5rem;
        padding: 3.5rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); /* Max depth shadow */
        border: 1px solid #f0f0f0;
    }
    
    /* Fix for warning/info strips (yellow/blue) to match theme */
    .stAlert {
        border-radius: 10px;
        font-size: 1.05rem;
        font-weight: 500;
    }
    /* Yellow/Warning Strip Fix */
    .stAlert[data-baseweb="notification"] > div:first-child[style*="rgb(255, 240, 209)"] {
        background-color: #fff3cd !important; 
        color: #856404 !important; /* Dark text on yellow */
        border: 1px solid #ffeeba !important;
    }
     /* Blue/Info Strip Fix */
    .stAlert[data-baseweb="notification"] > div:first-child[style*="rgb(230, 242, 255)"] {
        background-color: #cce5ff !important;
        color: #004085 !important; /* Dark text on blue */
        border: 1px solid #b8daff !important;
    }
    
    /* Markdown Links (Website URLs) in Results */
    .results-card a {
        color: #007bff; /* Bright blue for clickable links */
        font-weight: 600;
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
    
    # Use a common placeholder button for generation
    if col2.button("Generate Comprehensive Job Strategy", use_container_width=True):
        if not cv_text.strip():
            st.error("Please provide your CV content either by pasting or uploading a file to start the analysis.")
        else:
            st.session_state['cv_text_to_process'] = cv_text # Store content for processing
            st.session_state['run_search'] = True
            
    # Conditional Reset Button
    if st.session_state.get('results_displayed') and st.session_state['results_displayed']:
        if st.button("Start New Search (Reset)", type="secondary"):
            reset_inputs()
            # Must rerun to clear the main output area
            st.rerun()

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
            
            # Set flag to display reset button after successful generation
            st.session_state['results_displayed'] = True
            st.session_state['run_search'] = False 
            st.markdown('</div>', unsafe_allow_html=True)
    elif st.session_state.get('results_displayed'):
        # Keep output visible until explicitly reset
        pass 
    else:
        # Initial state message
        st.info("Your comprehensive job search strategy will appear here after analysis. Click 'Generate' to begin.")


if __name__ == '__main__':
    # Initialize session state variables
    if 'run_search' not in st.session_state:
        st.session_state['run_search'] = False
    if 'results_displayed' not in st.session_state:
        st.session_state['results_displayed'] = False
    if 'cv_text_to_process' not in st.session_state:
        st.session_state['cv_text_to_process'] = ""
        
    main()
