import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
# This line does nothing on Streamlit Cloud but is useful for local testing
load_dotenv() 

# --- Gemini API Configuration ---
# Priority: 1. Streamlit Secrets (for cloud) 2. OS Environment (for local)
# This uses st.secrets.get for Streamlit Cloud and os.environ.get for local testing.
# The third argument is an empty string if neither is found.
API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

# --- Core Gemini API Call Function ---

@st.cache_data(show_spinner=False)
def generate_job_strategy_from_gemini(cv_text):
    """
    Analyzes CV text, performs a grounded search for jobs, and generates
    a professional, detailed application strategy including visa requirements.
    This function is wrapped in Streamlit's cache for efficiency if the same 
    input is provided multiple times.
    """
    if not API_KEY:
        # Check if key is available for API call
        return "Error: Gemini API Key not configured. Please set your GEMINI_API_KEY in Streamlit Cloud secrets or locally in a .env file.", []
        
    # 1. Define the System Instruction
    system_prompt = (
        "You are a World-Class Job Search Consultant and Visa Immigration Analyst. "
        "Your task is to analyze the provided CV content and generate a highly detailed, "
        "professionally formatted job search strategy. You must use the Google Search tool "
        "to find current, relevant job openings, application procedures, and up-to-date visa/immigration "
        "requirements for the specified roles/regions. "
        "Your response MUST be formatted strictly as a single Markdown document with three main sections: "
        "'Top Matched Employers (High-Accuracy)', 'Domestic Job Strategy', and 'International Job Strategy'.\n\n"
        "MANDATORY OUTPUT REQUIREMENTS:\n"
        "1. TOP MATCHED EMPLOYERS (High-Accuracy): List 5 specific, high-profile employers (company names) "
        "that match the user's CV content (90%-100% suitability based on skills like AWS, Python, Fintech). "
        "For each employer, provide a brief rationale (1-2 sentences) for the high match and their primary location (e.g., London, NYC, Remote).\n"
        "2. DOMESTIC JOB STRATEGY: Provide 3 specific job titles matching the CV. For each title, give a "
        "step-by-step guide on how to apply (e.g., where to search, keywords, required documents).\n"
        "3. INTERNATIONAL JOB STRATEGY: Provide 3 specific international job titles matching the CV. "
        "Focus on the US, UK, and Canada/EU region (if applicable). For each region, you MUST include: "
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

    # Custom styling for a professional look (using Streamlit's native components)
    st.markdown("""
    <style>
    .stApp {
        background-color: #f7f9fb;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 0.5rem;
        border: 1px solid #d1d5db;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        font-weight: 600;
        border-radius: 9999px; /* full rounded */
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)


    st.title("💼 Professional CV-to-Job Strategy Generator")
    st.markdown("Paste your CV content below to receive a hyper-accurate, **Gemini-grounded** job search and visa strategy.")

    # Input Area
    cv_text = st.text_area(
        "Paste CV Content Here (Required)",
        height=300,
        placeholder="Example: John Doe | Senior Software Engineer | Skills: Python, AWS, Fintech, etc.",
        key="cv_input"
    )

    # Button
    if st.button("Generate Job Strategy (Grounding Search Active)"):
        if not cv_text.strip():
            st.error("Please paste your CV content into the text area to start the analysis.")
        else:
            with st.spinner("Analyzing CV and Performing Real-Time Job Search (This may take up to 20 seconds for in-depth analysis and grounding)..."):
                # Call the core Gemini function
                markdown_output, citations = generate_job_strategy_from_gemini(cv_text)

            st.subheader("Generated Professional Strategy")
            
            # Display the result (Streamlit renders Markdown natively)
            st.markdown(markdown_output)

            # Display citations
            if citations:
                st.subheader("Grounding Sources (For Verification)")
                for i, source in enumerate(citations):
                    st.markdown(f"**[{i+1}]** [{source.get('title')}]({source.get('uri')})")
            elif "Error" in markdown_output:
                st.error("An error occurred during the API call. Please check your API key configuration or try again.")
            else:
                st.info("No explicit grounding sources were returned for the generated strategy.")


if __name__ == '__main__':
    main()
