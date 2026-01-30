import streamlit as st
import os
from supabase import create_client

st.set_page_config(page_title="Reset Password - Job-Search-Agent", page_icon="🔐", layout="wide")

# --- NEW ORANGE + GOLD NEON UI STYLING (MATCHING MAIN APP) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    .stApp {
        background: #0a0a0f !important;
        background-attachment: fixed;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* HIDE SIDEBAR */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* HIDE SIDEBAR BUTTON */
    button[kind="header"] {
        display: none !important;
    }
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Card styles */
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
    
    div[data-testid="stMetricValue"] { 
        color: #ff6b35 !important; 
        text-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
        font-weight: 700;
    }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: rgba(255, 107, 53, 0.08) !important;
        color: white !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #ff6b35 !important;
        box-shadow: 0 0 15px rgba(255, 107, 53, 0.3) !important;
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(255, 107, 53, 0.4);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 35px rgba(255, 107, 53, 0.6);
        transform: translateY(-2px);
    }
    
    .stSelectbox>div>div {
        background-color: rgba(255, 107, 53, 0.08) !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    .stProgress>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    hr {
        border-color: rgba(255, 107, 53, 0.2) !important;
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 10px;
    }
    
    /* Error message styling */
    .stError {
        background-color: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 10px;
    }
    
    /* Warning message styling */
    .stWarning {
        background-color: rgba(245, 158, 11, 0.1) !important;
        border: 1px solid rgba(245, 158, 11, 0.3) !important;
        border-radius: 10px;
    }
    
    /* Info message styling */
    .stInfo {
        background-color: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize Supabase
def get_secret(key):
    if key in os.environ: return os.environ[key]
    try: return st.secrets[key]
    except: return None

@st.cache_resource
def init_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

try:
    supabase = init_supabase()
except:
    supabase = None

# Initialize session state
if 'reset_token_set' not in st.session_state:
    st.session_state.reset_token_set = False
if 'password_updated' not in st.session_state:
    st.session_state.password_updated = False

def set_session_from_params():
    """Try to set session from URL parameters"""
    try:
        query_params = st.query_params
        access_token = query_params.get("access_token", "")
        refresh_token = query_params.get("refresh_token", "")
        token_type = query_params.get("type", "")
        
        if access_token and supabase and token_type == "recovery":
            try:
                supabase.auth.set_session(access_token, refresh_token if refresh_token else access_token)
                st.session_state.reset_token_set = True
                return True
            except Exception as e:
                st.error(f"Session error: {e}")
                return False
        return False
    except:
        return False

def update_password_with_token(new_password, token_hash, email=None):
    """Update user password using the recovery token hash"""
    if not supabase:
        return False, "Database connection error."
    if not new_password or len(new_password) < 6:
        return False, "Password must be at least 6 characters long."
    
    try:
        # For Supabase recovery, we need to verify the OTP token first
        # The token from email template {{ .Token }} is a token_hash for verify_otp
        verify_result = supabase.auth.verify_otp({
            "token_hash": token_hash,
            "type": "recovery"
        })
        
        # After verification, the session is set and we can update the password
        if verify_result and verify_result.user:
            result = supabase.auth.update_user({"password": new_password})
            return True, "Password updated successfully! You can now login with your new password."
        else:
            return False, "Token verification failed. Please request a new reset link."
            
    except Exception as e:
        error_msg = str(e).lower()
        if "expired" in error_msg:
            return False, "Your reset link has expired. Please request a new password reset link."
        elif "invalid" in error_msg or "otp" in error_msg:
            return False, "Invalid or expired token. Please request a new password reset link."
        return False, f"Failed to update password: {e}"

# Main Logo
st.markdown("""
<div style="text-align: center; margin: 30px 0;">
    <h1 style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-style: italic; margin: 0;">
        🚀 Job-Search-Agent
    </h1>
    <p style="color: #888; margin: 5px 0 0 0;">AI-Powered Career Guidance</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Main Page Content
st.markdown("""
<h1 style="text-align: center; font-size: 2rem;">
    🔐 Reset Your Password
</h1>
""", unsafe_allow_html=True)

# Check for tokens in URL query parameters
query_params = st.query_params
has_token = "access_token" in query_params

# Also check if type is recovery (but don't require it)
access_token = query_params.get("access_token", "")
refresh_token = query_params.get("refresh_token", "")
token_type = query_params.get("type", "")
query_params = st.query_params
has_token = "access_token" in query_params and query_params.get("type") == "recovery"

# Center the content
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.session_state.password_updated:
        st.success("✅ Your password has been updated successfully!")
        st.info("You can now close this page and login with your new password.")
        if st.button("← Go to Login Page", type="primary", use_container_width=True):
            st.switch_page("Main_Page.py")

    elif has_token or st.session_state.reset_token_set:
        # Token detected - show the password reset form
        st.caption("Enter your new password below.")
        
        with st.form("reset_password_form"):
            new_password = st.text_input("New Password", type="password", key="new_pwd")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pwd")
            
            submitted = st.form_submit_button("✅ Update Password", type="primary", use_container_width=True)
            
            if submitted:
                if new_password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters long.")
                else:
                    # Use the access_token as token_hash for verify_otp
                    success, message = update_password_with_token(new_password, access_token)
                    if success:
                        st.session_state.password_updated = True
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        if st.button("← Back to Login", use_container_width=True):
            st.query_params.clear()
            st.switch_page("Main_Page.py")

    else:
        st.warning("⚠️ No valid password reset token found in URL.")
        
        st.markdown("---")
        st.subheader("📧 Manual Token Entry")
        st.caption("If you clicked the reset link but see this message, please copy the token from your URL and paste it below.")
        
        st.markdown("""
        **How to find your token:**
        1. Look at your browser's address bar
        2. Find `access_token=` followed by a long string
        3. Copy that entire string (the token)
        4. Paste it below
        """)
        
        with st.form("manual_token_form"):
            manual_token = st.text_input("Paste your access_token here:", key="manual_token")
            token_submitted = st.form_submit_button("🔓 Verify Token", type="primary", use_container_width=True)
            
            if token_submitted and manual_token:
                # Redirect with the token as query parameter
                st.query_params["access_token"] = manual_token
                st.query_params["type"] = "recovery"
                st.rerun()
        
        st.markdown("---")
        st.markdown("""
        **Or request a new reset link:**
        1. Go to the login page
        2. Click "Forgot Password?"
        3. Enter your email address
        4. Check your email for a new reset link
        """)
        
        if st.button("← Go to Login Page", type="primary", use_container_width=True):
            st.switch_page("Main_Page.py")
