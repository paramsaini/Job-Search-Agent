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

def update_password(new_password):
    """Update user password"""
    if not supabase:
        return False, "Database connection error."
    if not new_password or len(new_password) < 6:
        return False, "Password must be at least 6 characters long."
    
    try:
        supabase.auth.update_user({"password": new_password})
        return True, "Password updated successfully! You can now login with your new password."
    except Exception as e:
        return False, f"Failed to update password: {e}"

# Main Page Content
st.title("🔐 Reset Your Password")

# Check for tokens in URL
query_params = st.query_params
has_token = "access_token" in query_params and query_params.get("type") == "recovery"

if st.session_state.password_updated:
    st.success("✅ Your password has been updated successfully!")
    st.info("You can now close this page and login with your new password.")
    if st.button("← Go to Login Page", type="primary"):
        st.switch_page("streamlit_app.py")

elif has_token or st.session_state.reset_token_set:
    # Try to set session if not already done
    if not st.session_state.reset_token_set:
        set_session_from_params()
    
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
                success, message = update_password(new_password)
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
    st.warning("⚠️ No valid password reset token found.")
    st.markdown("""
    **To reset your password:**
    1. Go to the login page
    2. Click "Forgot Password?"
    3. Enter your email address
    4. Check your email for the reset link
    5. Click the reset link in your email
    """)
    
    st.markdown("---")
    if st.button("← Go to Login Page", type="primary"):
        st.switch_page("streamlit_app.py")
