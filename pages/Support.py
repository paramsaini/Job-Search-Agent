import streamlit as st
import os
from supabase import create_client

# --- PAGE CONFIG ---
st.set_page_config(page_title="Support - Job-Search-Agent", page_icon="💬", layout="wide")

# --- NEW ORANGE + GOLD NEON UI STYLING (HIDE SIDEBAR) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #0a0a0f !important;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* HIDE SIDEBAR */
    [data-testid="stSidebar"] { display: none !important; }
    button[kind="header"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"],
    div[data-testid="stExpanderDetails"],
    div[data-testid="stForm"] {
        background: rgba(255, 107, 53, 0.05) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 107, 53, 0.15) !important;
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        padding: 15px;
    }
    
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
        color: #e2e8f0 !important;
        font-family: 'Outfit', sans-serif;
    }
    
    h1 {
        background: linear-gradient(90deg, #ff6b35, #f7c531);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    p, label, .stMarkdown { color: #e2e8f0 !important; }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 107, 53, 0.08) !important;
        color: white !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
        border-radius: 10px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 35px rgba(255, 107, 53, 0.6);
    }
    
    .stSelectbox>div>div {
        background-color: rgba(255, 107, 53, 0.08) !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    hr { border-color: rgba(255, 107, 53, 0.2) !important; }
    
    .support-card {
        background: rgba(255, 107, 53, 0.08);
        border: 1px solid rgba(255, 107, 53, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }
    
    .faq-item {
        background: rgba(255, 107, 53, 0.05);
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Supabase Init ---
def get_secret(key):
    if key in os.environ:
        return os.environ[key]
    try:
        return st.secrets[key]
    except:
        return None

@st.cache_resource
def init_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

try:
    supabase = init_supabase()
except:
    supabase = None

# --- Back Button ---
st.page_link("Main_Page.py", label="← Back to Main Page", icon="🏠")

# Main Logo
st.markdown("""
<div style="text-align: center; margin: 10px 0;">
    <h1 style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2rem; font-style: italic; margin: 0;">
        🚀 Job-Search-Agent
    </h1>
    <p style="color: #888; margin: 5px 0 0 0; font-size: 0.9rem;">AI-Powered Career Guidance</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- HEADER ---
st.markdown("""
<h1 style="text-align: center; font-size: 2.5rem;">
    💬 Support Center
</h1>
""", unsafe_allow_html=True)
st.caption("Get help with your career journey")

st.markdown("---")

# --- CONTACT INFO ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📧 Contact Us")
    st.markdown("""
    <div class="support-card">
        <p><strong>Email Support:</strong></p>
        <p>📩 jobsearchagent26@gmail.com</p>
        <p style="color: #94a3b8; font-size: 0.9em;">Response time: Within 24-48 hours</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("🔗 Quick Links")
    st.markdown("""
    <div class="support-card">
        <p>📋 Frequently Asked Questions - <em>See below</em></p>
        <p>🔒 Privacy Policy - <em>See below</em></p>
        <p>📜 Terms of Service - <em>See below</em></p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- FAQ SECTION ---
st.subheader("❓ Frequently Asked Questions")

with st.expander("How do I create an account?"):
    st.write("""
    1. Open the Job-Search-Agent app
    2. Select "Sign Up" on the login screen
    3. Enter your email address and create a password
    4. Check your email for a confirmation link
    5. Click the link to verify your account
    6. Log in with your credentials
    """)

with st.expander("How does the Voice Interview Simulator work?"):
    st.write("""
    The Voice Interview Simulator helps you practice for job interviews:
    
    1. **Enter a job role** - Tell us what position you're applying for
    2. **AI generates a question** - Our AI creates realistic interview questions
    3. **Record your answer** - Use your microphone to practice your response
    4. **Get instant feedback** - AI analyzes your answer and provides improvement tips
    
    **Note:** Microphone access is required for this feature.
    """)

with st.expander("Why does the app need microphone access?"):
    st.write("""
    Job-Search-Agent uses your microphone **only** for the Voice Interview Simulator feature. 
    
    When you practice mock interviews:
    - Your voice is recorded temporarily
    - The audio is sent to our AI for transcription
    - You receive feedback on your interview answers
    - Recordings are processed in real-time and not stored
    """)

with st.expander("How do I delete my account?"):
    st.write("""
    To delete your Job-Search-Agent account:
    
    1. Log into the app
    2. Go to **⚙️ Account Settings** in the menu
    3. Scroll to "Delete Account" section
    4. Type "DELETE" to confirm
    5. Click the delete button
    
    **Warning:** This action permanently deletes all your data.
    """)

with st.expander("How do I reset my password?"):
    st.write("""
    If you've forgotten your password:
    
    1. Go to the login screen
    2. Click "🔑 Forgot Password?"
    3. Enter your email address
    4. Check your inbox for a reset link
    5. Click the link and enter your new password
    """)

with st.expander("What data does Job-Search-Agent collect?"):
    st.write("""
    **Account Data:**
    - Email address (for login)
    - Username (optional display name)
    
    **Usage Data:**
    - CV/resume text (for analysis - stored securely)
    - Job application tracking entries
    - Mood/emotional check-in logs
    
    **Temporary Data:**
    - Voice recordings (processed in real-time, not stored)
    
    We do not sell your data to third parties.
    """)

with st.expander("The app isn't working. What should I do?"):
    st.write("""
    Try these troubleshooting steps:
    
    1. **Refresh the app** - Pull down to refresh or close and reopen
    2. **Check your internet connection** - Job-Search-Agent requires an active connection
    3. **Update the app** - Make sure you have the latest version
    4. **Clear cache** - In your device settings, clear the app cache
    5. **Restart your device** - Sometimes a simple restart helps
    
    If problems persist, email us at jobsearchagent26@gmail.com
    """)

st.markdown("---")

# --- PRIVACY POLICY SUMMARY ---
st.subheader("🔒 Privacy Policy Summary")

st.markdown("""
<div class="support-card">
    <h4 style="color: #f7c531;">Your Privacy Matters</h4>
    <p>Job-Search-Agent is committed to protecting your personal information:</p>
    <ul>
        <li><strong>Data Collection:</strong> We collect only what's necessary to provide our services</li>
        <li><strong>Data Security:</strong> Your information is encrypted and stored securely</li>
        <li><strong>No Selling:</strong> We never sell your personal data to third parties</li>
        <li><strong>Your Control:</strong> You can delete your account and all data at any time</li>
        <li><strong>Microphone:</strong> Voice recordings are processed in real-time and not stored</li>
    </ul>
    <p style="color: #94a3b8; font-size: 0.9em;">Last updated: January 2026</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- TERMS SUMMARY ---
st.subheader("📜 Terms of Service Summary")

st.markdown("""
<div class="support-card">
    <h4 style="color: #f7c531;">Using Job-Search-Agent</h4>
    <p>By using Job-Search-Agent, you agree to:</p>
    <ul>
        <li>Use the app for legitimate job search and career development purposes</li>
        <li>Provide accurate information in your profile and applications</li>
        <li>Not misuse the AI features or attempt to circumvent security measures</li>
        <li>Respect intellectual property rights</li>
    </ul>
    <p><strong>AI-Generated Content:</strong> Job recommendations and interview feedback are AI-generated suggestions. Always verify information and use your own judgment.</p>
    <p style="color: #94a3b8; font-size: 0.9em;">Last updated: January 2026</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- FEEDBACK FORM ---
st.subheader("📝 Send Us Feedback")

with st.form("feedback_form"):
    feedback_type = st.selectbox("Feedback Type", ["Bug Report", "Feature Request", "General Feedback", "Other"])
    feedback_email = st.text_input("Your Email")
    feedback_message = st.text_area("Your Message", height=150)
    
    submitted = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)
    
    if submitted:
        if feedback_message.strip():
            if supabase:
                try:
                    supabase.table("feedback").insert({
                        "feedback_type": feedback_type,
                        "email": feedback_email if feedback_email.strip() else None,
                        "message": feedback_message.strip()
                    }).execute()
                    st.success("✅ Thank you for your feedback!")
                except Exception as e:
                    st.error(f"Failed to submit feedback. Please email us directly.")
            else:
                st.error("Database connection unavailable. Please email us at jobsearchagent26@gmail.com")
        else:
            st.warning("Please enter a message before submitting.")

st.markdown("---")

# --- FOOTER ---
st.markdown("""
<div style="text-align: center; color: #94a3b8; padding: 20px;">
    <p><strong style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Job-Search-Agent</strong> - AI-Powered Career Guidance</p>
    <p>Version 1.0 | © 2026 Job-Search-Agent</p>
    <p>📧 jobsearchagent26@gmail.com</p>
</div>
""", unsafe_allow_html=True)
