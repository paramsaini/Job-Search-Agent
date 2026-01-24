import streamlit as st
import os
from supabase import create_client

st.set_page_config(page_title="Reset Password - Aequor", page_icon="🔐", layout="wide")

# Apply same styling as main app
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

def update_password(new_password, access_token, refresh_token):
    """Update user password using the recovery token"""
    if not supabase:
        return False, "Database connection error."
    if not new_password or len(new_password) < 6:
        return False, "Password must be at least 6 characters long."
    
    try:
        # First, set the session using the recovery token
        if access_token:
            try:
                # For recovery tokens, we need to use verify_otp or set_session
                session = supabase.auth.set_session(access_token, refresh_token if refresh_token else access_token)
            except Exception as session_error:
                # If set_session fails, try to exchange the token
                try:
                    # Try verifying as OTP token
                    session = supabase.auth.verify_otp({
                        "token_hash": access_token,
                        "type": "recovery"
                    })
                except:
                    pass
        
        # Now update the password
        result = supabase.auth.update_user({"password": new_password})
        return True, "Password updated successfully! You can now login with your new password."
    except Exception as e:
        error_msg = str(e)
        if "session" in error_msg.lower() or "token" in error_msg.lower():
            return False, "Your reset link may have expired. Please request a new password reset link."
        return False, f"Failed to update password: {e}"

# Main Page Content
st.title("🔐 Reset Your Password")

# Check for tokens in URL query parameters
query_params = st.query_params
has_token = "access_token" in query_params

# Also check if type is recovery (but don't require it)
access_token = query_params.get("access_token", "")
refresh_token = query_params.get("refresh_token", "")
token_type = query_params.get("type", "")
query_params = st.query_params
has_token = "access_token" in query_params and query_params.get("type") == "recovery"

if st.session_state.password_updated:
    st.success("✅ Your password has been updated successfully!")
    st.info("You can now close this page and login with your new password.")
    if st.button("← Go to Login Page", type="primary"):
        st.switch_page("streamlit_app.py")

elif has_token or st.session_state.reset_token_set:
    # Try to set session if not already done
    if not st.session_state.reset_token_set and access_token:
        if supabase:
            try:
                supabase.auth.set_session(access_token, refresh_token if refresh_token else access_token)
                st.session_state.reset_token_set = True
            except Exception as e:
                st.warning(f"Token validation issue: {e}")
    
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
                success, message = update_password(new_password, access_token, refresh_token)
                if success:
                    st.session_state.password_updated = True
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    st.markdown("---")
    if st.button("← Back to Login"):
        st.query_params.clear()
        st.switch_page("streamlit_app.py")

else:
    st.warning("⚠️ No valid password reset token found in URL.")
    
    st.markdown("---")
    st.subheader("🔧 Manual Token Entry")
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
    
    if st.button("← Go to Login Page", type="primary"):
        st.switch_page("streamlit_app.py")
