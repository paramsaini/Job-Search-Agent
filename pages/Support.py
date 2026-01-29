import streamlit as st

st.set_page_config(page_title="Support - Job-Search-Agent", page_icon="💬", layout="wide")

# Apply consistent styling with main app
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
        background-attachment: fixed;
        color: #e2e8f0;
    }
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"],
    div[data-testid="stExpanderDetails"],
    div[data-testid="stForm"],
    [data-testid="stSidebar"] > div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(88, 116, 176, 0.2) !important;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        padding: 15px;
    }
    h1, h2, h3, p, label, .stMarkdown { color: #e2e8f0 !important; }
    div[data-testid="stMetricValue"] { color: #00e0ff !important; text-shadow: 0 0 10px rgba(0, 224, 255, 0.6); }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: white !important;
        border: 1px solid rgba(88, 116, 176, 0.3) !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #0062ff, #00c6ff);
        color: white !important;
        border: none;
        box-shadow: 0 0 10px rgba(0, 98, 255, 0.5);
    }
    .support-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(88, 116, 176, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }
    .faq-item {
        background: rgba(30, 41, 59, 0.6);
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("💬 Job-Search-Agent Support Center")
st.caption("Get help with your career journey")

st.markdown("---")

# --- CONTACT INFO ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📧 Contact Us")
    st.markdown("""
    <div class="support-card">
        <p><strong>Email Support:</strong></p>
        <p>📩 support@job-search-agent.app</p>
        <p style="color: #94a3b8; font-size: 0.9em;">Response time: Within 24-48 hours</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("🔗 Quick Links")
    st.markdown("""
    <div class="support-card">
        <p>📋 <a href="#faq" style="color: #00c6ff;">Frequently Asked Questions</a></p>
        <p>🔒 <a href="#privacy" style="color: #00c6ff;">Privacy Policy</a></p>
        <p>📜 <a href="#terms" style="color: #00c6ff;">Terms of Service</a></p>
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
    
    **Note:** Microphone access is required for this feature. Your voice recordings are processed in real-time and are not stored permanently.
    """)

with st.expander("Why does the app need microphone access?"):
    st.write("""
    Job-Search-Agent uses your microphone **only** for the Voice Interview Simulator feature. 
    
    When you practice mock interviews:
    - Your voice is recorded temporarily
    - The audio is sent to our AI for transcription
    - You receive feedback on your interview answers
    - Recordings are processed in real-time and not stored
    
    You can use all other features of Job-Search-Agent without enabling microphone access.
    """)

with st.expander("How do I delete my account?"):
    st.write("""
    To delete your Job-Search-Agent account:
    
    1. Log into the app
    2. Go to **⚙️ Account Settings** in the menu
    3. Scroll to "Delete Account" section
    4. Type "DELETE" to confirm
    5. Click the delete button
    
    **Warning:** This action permanently deletes all your data including:
    - Your profile information
    - Saved analyses and reports
    - Application tracking history
    - Mood/emotional tracking logs
    
    This cannot be undone.
    """)

with st.expander("How do I reset my password?"):
    st.write("""
    If you've forgotten your password:
    
    1. Go to the login screen
    2. Click "🔑 Forgot Password?"
    3. Enter your email address
    4. Check your inbox for a reset link
    5. Click the link and enter your new password
    
    If you don't receive the email, check your spam folder.
    """)

with st.expander("What data does Job-Search-Agent collect?"):
    st.write("""
    Job-Search-Agent collects only the data necessary to provide our services:
    
    **Account Data:**
    - Email address (for login)
    - Username (optional display name)
    
    **Usage Data:**
    - CV/resume text (for analysis - stored securely)
    - Job application tracking entries
    - Mood/emotional check-in logs
    
    **Temporary Data:**
    - Voice recordings (processed in real-time, not stored)
    
    We do not sell your data to third parties. See our Privacy Policy for full details.
    """)

with st.expander("The app isn't working. What should I do?"):
    st.write("""
    Try these troubleshooting steps:
    
    1. **Refresh the app** - Pull down to refresh or close and reopen
    2. **Check your internet connection** - Job-Search-Agent requires an active connection
    3. **Update the app** - Make sure you have the latest version
    4. **Clear cache** - In your device settings, clear the app cache
    5. **Restart your device** - Sometimes a simple restart helps
    
    If problems persist, email us at support@job-search-agent.app with:
    - Your device type (iPhone/iPad/Android)
    - A description of the issue
    - Screenshots if possible
    """)

st.markdown("---")

# --- PRIVACY POLICY SUMMARY ---
st.subheader("🔒 Privacy Policy Summary")

st.markdown("""
<div class="support-card">
    <h4>Your Privacy Matters</h4>
    <p>Job-Search-Agent is committed to protecting your personal information. Here's what you need to know:</p>
    <ul>
        <li><strong>Data Collection:</strong> We collect only what's necessary to provide our services</li>
        <li><strong>Data Security:</strong> Your information is encrypted and stored securely</li>
        <li><strong>No Selling:</strong> We never sell your personal data to third parties</li>
        <li><strong>Your Control:</strong> You can delete your account and all data at any time</li>
        <li><strong>Microphone:</strong> Voice recordings are processed in real-time and not permanently stored</li>
    </ul>
    <p style="color: #94a3b8; font-size: 0.9em;">Last updated: January 2026</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- TERMS SUMMARY ---
st.subheader("📜 Terms of Service Summary")

st.markdown("""
<div class="support-card">
    <h4>Using Job-Search-Agent</h4>
    <p>By using Job-Search-Agent, you agree to:</p>
    <ul>
        <li>Use the app for legitimate job search and career development purposes</li>
        <li>Provide accurate information in your profile and applications</li>
        <li>Not misuse the AI features or attempt to circumvent security measures</li>
        <li>Respect intellectual property rights</li>
    </ul>
    <p><strong>AI-Generated Content:</strong> Job recommendations and interview feedback are AI-generated suggestions. Always verify information and use your own judgment when making career decisions.</p>
    <p style="color: #94a3b8; font-size: 0.9em;">Last updated: January 2026</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- FEEDBACK FORM ---
st.subheader("📝 Send Us Feedback")

with st.form("feedback_form"):
    feedback_type = st.selectbox("Feedback Type", ["Bug Report", "Feature Request", "General Feedback", "Other"])
    feedback_email = st.text_input("Your Email (optional)")
    feedback_message = st.text_area("Your Message", height=150)
    
    submitted = st.form_submit_button("Submit Feedback", type="primary", use_container_width=True)
    
    if submitted:
        if feedback_message.strip():
            st.success("✅ Thank you for your feedback! We'll review it and get back to you if needed.")
        else:
            st.warning("Please enter a message before submitting.")

st.markdown("---")

# --- FOOTER ---
st.markdown("""
<div style="text-align: center; color: #94a3b8; padding: 20px;">
    <p><strong>Job-Search-Agent</strong> - AI-Powered Career Guidance</p>
    <p>Version 1.0 | © 2026 Job-Search-Agent</p>
    <p>📧 support@job-search-agent.app</p>
</div>
""", unsafe_allow_html=True)
