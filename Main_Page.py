import streamlit as st
import os
import pypdf
import json
import pandas as pd
from dotenv import load_dotenv
from agent import JobSearchAgent
from supabase import create_client, Client
from groq import Groq
from fpdf import FPDF

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Job-Search-Agent Career Agent", page_icon="🚀", layout="wide")

# --- NEW ORANGE + GOLD NEON UI STYLING ---
st.markdown("""
    <style>
    /* === IMPORTS === */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* === BASE STYLES === */
    .stApp {
        background: #0a0a0f !important;
        background-attachment: fixed;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* === HIDE DEFAULT SIDEBAR === */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* === TOP NAVIGATION BAR === */
    .top-nav-bar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: rgba(10, 10, 15, 0.95);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255, 107, 53, 0.2);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        z-index: 9999;
        box-shadow: 0 4px 30px rgba(255, 107, 53, 0.1);
    }
    
    .nav-logo {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #ff6b35, #f7c531);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255, 107, 53, 0.5);
    }
    
    .hamburger-btn {
        width: 40px;
        height: 40px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        background: rgba(255, 107, 53, 0.1);
        border: 1px solid rgba(255, 107, 53, 0.3);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .hamburger-btn:hover {
        background: rgba(255, 107, 53, 0.2);
        box-shadow: 0 0 20px rgba(255, 107, 53, 0.3);
    }
    
    .hamburger-line {
        width: 20px;
        height: 2px;
        background: linear-gradient(90deg, #ff6b35, #f7c531);
        margin: 3px 0;
        border-radius: 2px;
    }
    
    .user-info {
        color: #888;
        font-size: 0.9rem;
    }
    
    .user-info span {
        color: #f7c531;
        font-weight: 600;
    }
    
    /* === FULL SCREEN OVERLAY MENU === */
    .fullscreen-menu {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(10, 10, 15, 0.98);
        backdrop-filter: blur(30px);
        z-index: 99999;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        opacity: 0;
        visibility: hidden;
        transition: all 0.4s ease;
    }
    
    .fullscreen-menu.active {
        opacity: 1;
        visibility: visible;
    }
    
    .close-btn {
        position: absolute;
        top: 20px;
        right: 30px;
        font-size: 2.5rem;
        color: #ff6b35;
        cursor: pointer;
        transition: all 0.3s ease;
        text-shadow: 0 0 20px rgba(255, 107, 53, 0.5);
    }
    
    .close-btn:hover {
        color: #f7c531;
        transform: rotate(90deg);
        text-shadow: 0 0 30px rgba(247, 197, 49, 0.8);
    }
    
    .menu-items {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 15px;
    }
    
    .menu-item {
        font-size: 1.8rem;
        font-weight: 600;
        color: #666;
        text-decoration: none;
        padding: 15px 40px;
        border-radius: 12px;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        letter-spacing: 1px;
    }
    
    .menu-item:hover, .menu-item.active {
        color: transparent;
        background: linear-gradient(90deg, #ff6b35, #f7c531);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(255, 107, 53, 0.8);
    }
    
    .menu-item.active::before {
        content: '→';
        position: absolute;
        left: 10px;
        color: #ff6b35;
        -webkit-text-fill-color: #ff6b35;
    }
    
    .menu-divider {
        width: 200px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 107, 53, 0.3), transparent);
        margin: 10px 0;
    }
    
    .menu-logout {
        margin-top: 20px;
        font-size: 1.2rem;
        color: #dc2626;
        cursor: pointer;
        padding: 10px 30px;
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .menu-logout:hover {
        background: rgba(220, 38, 38, 0.1);
        box-shadow: 0 0 20px rgba(220, 38, 38, 0.3);
    }
    
    /* === CONTENT AREA === */
    .main-content {
        margin-top: 80px;
        padding: 20px;
    }
    
    /* === CARD STYLES === */
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
    
    /* === TYPOGRAPHY === */
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
    
    /* === METRICS === */
    div[data-testid="stMetricValue"] { 
        color: #ff6b35 !important; 
        text-shadow: 0 0 20px rgba(255, 107, 53, 0.6);
        font-weight: 700;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #f7c531 !important;
    }
    
    /* === INPUTS === */
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
    
    /* === BUTTONS === */
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
    
    /* === SECONDARY BUTTONS === */
    .stButton>button[kind="secondary"] {
        background: transparent !important;
        color: #ff6b35 !important;
        border: 1px solid rgba(255, 107, 53, 0.5) !important;
    }
    
    /* === SELECT BOXES === */
    .stSelectbox>div>div {
        background-color: rgba(255, 107, 53, 0.08) !important;
        border: 1px solid rgba(255, 107, 53, 0.25) !important;
        border-radius: 10px;
    }
    
    /* === FILE UPLOADER === */
    .stFileUploader>div {
        background-color: rgba(255, 107, 53, 0.05) !important;
        border: 2px dashed rgba(255, 107, 53, 0.3) !important;
        border-radius: 12px;
    }
    
    /* === PROGRESS BARS === */
    .stProgress>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    /* === EXPANDERS === */
    .streamlit-expanderHeader {
        background: rgba(255, 107, 53, 0.1) !important;
        border-radius: 10px;
        color: #f7c531 !important;
    }
    
    /* === DIVIDERS === */
    hr {
        border-color: rgba(255, 107, 53, 0.2) !important;
    }
    
    /* === RADIO BUTTONS === */
    .stRadio>div {
        background: rgba(255, 107, 53, 0.05);
        padding: 10px;
        border-radius: 10px;
    }
    
    /* === SLIDER === */
    .stSlider>div>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    /* === SUCCESS/WARNING/ERROR MESSAGES === */
    .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }
    
    .stWarning {
        background: rgba(247, 197, 49, 0.1) !important;
        border: 1px solid rgba(247, 197, 49, 0.3) !important;
    }
    
    .stError {
        background: rgba(220, 38, 38, 0.1) !important;
        border: 1px solid rgba(220, 38, 38, 0.3) !important;
    }
    
    /* === DATAFRAMES === */
    .stDataFrame {
        background: rgba(255, 107, 53, 0.05) !important;
        border-radius: 12px;
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 107, 53, 0.1);
        border-radius: 8px;
        color: #e2e8f0;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
        color: #000 !important;
    }
    
    /* === CHECKBOX === */
    .stCheckbox>label>span {
        color: #e2e8f0 !important;
    }
    
    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0a0a0f;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #ff6b35, #f7c531);
        border-radius: 4px;
    }
    
    /* === ANIMATIONS === */
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 107, 53, 0.3); }
        50% { box-shadow: 0 0 40px rgba(255, 107, 53, 0.6); }
    }
    
    .glow-effect {
        animation: glow 2s ease-in-out infinite;
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

# --- 2. HELPER FUNCTIONS ---
def extract_text(file):
    """Extracts text from uploaded PDF or TXT files"""
    try:
        if file is None: return ""
        if file.type == "application/pdf":
            reader = pypdf.PdfReader(file)
            return "".join([p.extract_text() for p in reader.pages])
        return file.read().decode("utf-8")
    except: return ""

def create_pdf(text):
    """Safe PDF Generator - Fixes White Screen Crash"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=11)
        
        # 1. Sanitize Text (Replace crash-prone characters)
        replacements = {
            ''': "'", ''': "'", '"': '"', '"': '"', '–': '-', '—': '-',
            '•': '-', '…': '...', '\u2022': '-' 
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        # 2. Encode to Latin-1
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, clean_text)
        
        # 3. CRITICAL FIX: Explicitly convert to bytes
        return bytes(pdf.output())
        
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return None

def get_secret(key):
    if key in os.environ: return os.environ[key]
    try: return st.secrets[key]
    except: return None

# --- 3. INITIALIZATION ---
@st.cache_resource
def init_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    if not url or not key: return None
    return create_client(url, key)

try: supabase = init_supabase()
except: supabase = None

if 'agent' not in st.session_state:
    api = get_secret("GEMINI_API_KEY")
    qh = get_secret("QDRANT_HOST")
    qk = get_secret("QDRANT_API_KEY")
    if api and qh: st.session_state.agent = JobSearchAgent(api, qh, qk)
    else: st.session_state.agent = None

if 'groq' not in st.session_state:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key: st.session_state.groq = Groq(api_key=groq_key)
    else: st.session_state.groq = None

# --- 4. AUTH & LOGIC ---
if 'user' not in st.session_state: st.session_state.user = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'show_delete_confirmation' not in st.session_state: st.session_state.show_delete_confirmation = False
if 'show_forgot_password' not in st.session_state: st.session_state.show_forgot_password = False
if 'password_reset_mode' not in st.session_state: st.session_state.password_reset_mode = False
if 'menu_open' not in st.session_state: st.session_state.menu_open = False
if 'current_page' not in st.session_state: st.session_state.current_page = "Main Page"

def login(email, password):
    if not supabase: return st.error("Database error.")
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user.email
        st.session_state.user_id = res.user.id
        # Self-Healing
        try:
            pid = res.user.id
            prof = supabase.table("profiles").select("*").eq("id", pid).execute()
            if not prof.data:
                supabase.table("profiles").insert({"id": pid, "username": email.split('@')[0], "email": email}).execute()
            elif not prof.data[0].get('email'):
                supabase.table("profiles").update({"email": email}).eq("id", pid).execute()
        except: pass
        st.rerun()
    except Exception as e: st.error(f"Login failed: {e}")

def signup(email, password, username):
    if not supabase: return
    try:
        res = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"username": username}}})
        if res.user:
            # Check if profile already exists (handles edge cases)
            try:
                existing = supabase.table("profiles").select("id").eq("id", res.user.id).execute()
                if not existing.data:
                    supabase.table("profiles").insert({"id": res.user.id, "username": username, "email": email}).execute()
            except:
                pass  # Profile insert failed, but auth succeeded - user can still login
        st.success("Account created! Check your email to confirm, then login.")
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            st.warning("This email is already registered. Please login instead.")
        else:
            st.error(f"Signup failed: {e}")

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

def forgot_password(email):
    """Send password reset email to user via Supabase Auth"""
    if not supabase:
        return False, "Database connection error."
    if not email or not email.strip():
        return False, "Please enter your email address."
    
    try:
        # Supabase Auth handles password reset securely
        supabase.auth.reset_password_email(email.strip())
        return True, "Password reset email sent! Check your inbox and follow the link to reset your password."
    except Exception as e:
        error_msg = str(e).lower()
        if "user not found" in error_msg or "invalid" in error_msg:
            return False, "No account found with this email address."
        return False, f"Failed to send reset email: {e}"

def update_password(new_password):
    """Update user password after reset link verification"""
    if not supabase:
        return False, "Database connection error."
    if not new_password or len(new_password) < 6:
        return False, "Password must be at least 6 characters long."
    
    try:
        supabase.auth.update_user({"password": new_password})
        return True, "Password updated successfully! You can now login with your new password."
    except Exception as e:
        return False, f"Failed to update password: {e}"

def check_password_reset_token():
    """Check if user arrived from a password reset link - handles URL fragments"""
    try:
        # First check query parameters
        query_params = st.query_params
        
        # Check if we already detected reset mode from fragment
        if query_params.get("reset_mode") == "true":
            access_token = query_params.get("access_token", "")
            refresh_token = query_params.get("refresh_token", "")
            
            if access_token and supabase:
                try:
                    supabase.auth.set_session(access_token, refresh_token if refresh_token else access_token)
                except:
                    pass
            return True
        
        # Check for tokens in query params (type=recovery indicates password reset)
        if query_params.get("type") == "recovery" or "access_token" in query_params:
            access_token = query_params.get("access_token", "")
            refresh_token = query_params.get("refresh_token", "")
            
            if access_token and supabase:
                try:
                    supabase.auth.set_session(access_token, refresh_token if refresh_token else access_token)
                except:
                    pass
            return True
        
        return False
    except:
        return False

def inject_fragment_handler():
    """Inject JavaScript to handle URL fragments from Supabase password reset"""
    import streamlit.components.v1 as components
    
    # JavaScript that runs in iframe but can access parent window
    js_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <script>
        (function() {
            try {
                // Access parent window URL
                var parentUrl = window.parent.location.href;
                
                // Check if parent URL has a hash with access_token
                if (parentUrl.includes('#') && parentUrl.includes('access_token')) {
                    var hashIndex = parentUrl.indexOf('#');
                    var baseUrl = parentUrl.substring(0, hashIndex);
                    var fragment = parentUrl.substring(hashIndex + 1);
                    
                    // Parse the fragment
                    var params = new URLSearchParams(fragment);
                    var accessToken = params.get('access_token');
                    var refreshToken = params.get('refresh_token');
                    var type = params.get('type');
                    
                    // If this is a recovery flow
                    if (accessToken && type === 'recovery') {
                        // Build new URL with query parameters
                        var newUrl = baseUrl + '?reset_mode=true&type=recovery&access_token=' + 
                            encodeURIComponent(accessToken);
                        if (refreshToken) {
                            newUrl += '&refresh_token=' + encodeURIComponent(refreshToken);
                        }
                        
                        // Redirect parent window
                        window.parent.location.replace(newUrl);
                    }
                }
            } catch (e) {
                // Cross-origin error - try alternative method
                console.log('Fragment handler:', e);
            }
        })();
        </script>
    </head>
    <body></body>
    </html>
    """
    components.html(js_code, height=0, width=0)

def delete_user_account():
    """
    PERMANENTLY deletes user account and ALL associated data from Supabase.
    This includes: analyses, applications, mood_logs, profiles, AND auth.users
    Required for Apple App Store Guideline 5.1.1(v) compliance.
    """
    if not st.session_state.user_id:
        return False, "Not authenticated"
    
    user_id = st.session_state.user_id
    
    # Get service role key for admin operations (REQUIRED for auth deletion)
    service_key = get_secret("SUPABASE_SERVICE_KEY")
    supabase_url = get_secret("SUPABASE_URL")
    
    if not service_key or not supabase_url:
        return False, "Server configuration error. Please contact support."
    
    try:
        # Create admin client with service_role key (has full database access)
        from supabase import create_client
        admin_client = create_client(supabase_url, service_key)
        
        # STEP 1: Delete ALL user data from tables
        try:
            admin_client.table("mood_logs").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"mood_logs deletion: {e}")
        
        try:
            admin_client.table("analyses").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"analyses deletion: {e}")
        
        try:
            admin_client.table("applications").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"applications deletion: {e}")
        
        try:
            admin_client.table("profiles").delete().eq("id", user_id).execute()
        except Exception as e:
            print(f"profiles deletion: {e}")
        
        # STEP 2: Delete from Supabase Authentication
        try:
            admin_client.auth.admin.delete_user(user_id)
        except Exception as e:
            print(f"auth deletion: {e}")
            return False, f"Failed to delete authentication: {e}"
        
        # STEP 3: Sign out current session
        try:
            supabase.auth.sign_out()
        except:
            pass
        
        return True, "Account and all data permanently deleted"
        
    except Exception as e:
        return False, f"Error deleting account: {e}"

def page_delete_account():
    """Account Deletion Page - Required for Apple App Store compliance"""
    st.header("🗑️ Delete Account")
    
    st.markdown("""
    <div style="background: rgba(220, 38, 38, 0.1); border: 1px solid #dc2626; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
        <h3 style="color: #dc2626 !important; margin-top: 0;">⚠️ Warning: This action is permanent</h3>
        <p style="color: #fca5a5 !important;">Deleting your account will:</p>
        <ul style="color: #fca5a5 !important;">
            <li>Permanently delete all your personal data</li>
            <li>Remove all your saved analyses and reports</li>
            <li>Delete your application history and tracking data</li>
            <li>Remove all mood logs and emotional tracking data</li>
            <li>This action <strong>cannot be undone</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"**Account to be deleted:** `{st.session_state.user}`")
    st.markdown("---")
    
    if not st.session_state.show_delete_confirmation:
        st.markdown("To proceed with account deletion, click the button below:")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ I want to delete my account", type="primary", use_container_width=True):
                st.session_state.show_delete_confirmation = True
                st.rerun()
    else:
        st.markdown("""
        <div style="background: rgba(220, 38, 38, 0.2); border: 2px solid #dc2626; border-radius: 10px; padding: 20px; text-align: center;">
            <h3 style="color: #dc2626 !important;">🚨 Final Confirmation Required</h3>
            <p style="color: white !important;">Are you absolutely sure? This will permanently delete your account and all data.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        confirm_text = st.text_input("Type 'DELETE' to confirm:", placeholder="Type DELETE here", key="delete_confirm_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_delete_confirmation = False
                st.rerun()
        
        with col2:
            delete_disabled = confirm_text.upper() != "DELETE"
            if st.button("🗑️ Permanently Delete Account", type="primary", use_container_width=True, disabled=delete_disabled):
                if confirm_text.upper() == "DELETE":
                    with st.spinner("Deleting your account..."):
                        success, message = delete_user_account()
                        if success:
                            st.success("✅ Your account has been deleted.")
                            st.info("You will be redirected to the login page...")
                            for key in list(st.session_state.keys()): 
                                del st.session_state[key]
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                            st.info("Please try again or contact support.")

# --- 5. APP PAGES ---

def page_skill_migration():
    st.header("📈 Skill Migration Analysis")
    
    # Initialize session states for this page
    if 'selected_career_path' not in st.session_state:
        st.session_state.selected_career_path = None
    if 'sprint_generated' not in st.session_state:
        st.session_state.sprint_generated = False
    if 'sprint_plan' not in st.session_state:
        st.session_state.sprint_plan = None
    if 'completed_tasks' not in st.session_state:
        st.session_state.completed_tasks = set()
    
    # --- SECTION 1: CV Upload ---
    st.subheader("1️⃣ Upload Your Document")
    uploaded_cv = st.file_uploader("Upload your CV (PDF/TXT)", type=["pdf", "txt"], key="skill_migration_cv")
    
    if uploaded_cv:
        cv_text = extract_text(uploaded_cv)
        if cv_text and st.session_state.agent:
            if st.button("🚀 Analyze CV", type="primary"):
                with st.spinner("Analyzing your CV..."):
                    try:
                        md, rep, src = st.session_state.agent.generate_strategy(cv_text, "All")
                        st.session_state.results = {"md": md, "rep": rep, "src": src}
                        st.session_state.cv_upload_time = json.dumps({"timestamp": str(pd.Timestamp.now())})
                        
                        # Save to Supabase
                        if supabase and st.session_state.user_id:
                            try:
                                supabase.table("analyses").insert({
                                    "user_id": st.session_state.user_id,
                                    "report_json": rep
                                }).execute()
                            except: pass
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
    
    st.markdown("---")
    
    # Try to get data from Session, otherwise fetch from DB
    report = None
    if "results" in st.session_state and "rep" in st.session_state.results:
        report = st.session_state.results["rep"]
    elif supabase and st.session_state.user_id:
        try:
            data = supabase.table("analyses").select("*").eq("user_id", st.session_state.user_id).order("created_at", desc=True).limit(1).execute()
            if data.data:
                raw_json = data.data[0]['report_json']
                if isinstance(raw_json, str):
                    report = json.loads(raw_json)
                else:
                    report = raw_json
        except Exception as e:
            st.error(f"Could not load history: {e}")

    if report:
        # --- SECTION 2: Profile Scores ---
        st.subheader("2️⃣ Your Profile Scores")
        c1, c2, c3 = st.columns(3)
        with c1:
            score = report.get('predictive_score', 0)
            st.metric("Predictive Match", f"{score}%")
            st.progress(score / 100)
        with c2:
            tech = report.get('tech_score', 0)
            st.metric("Skills Strength", f"{tech}%")
            st.progress(tech / 100)
        with c3:
            weakest_skill = report.get('weakest_link_skill', 'N/A')
            st.error(f"Focus Area: {weakest_skill}")
            st.caption("Prioritize improving this skill.")
        
        st.markdown("---")
        
        # --- SECTION 3: Interactive Career Path Visualizer ---
        st.subheader("3️⃣ Interactive Career Path Visualizer")
        st.caption("👆 Click on a career path to see detailed requirements and timeline")
        
        # Define career paths with detailed data
        career_paths = {
            "Senior Specialist": {
                "color": "#10B981",
                "success_rate": 85,
                "timeline": "6-12 months",
                "target_role": "Team Lead / Senior Engineer",
                "required_skills": ["Advanced Technical Skills", "Project Management", "Mentoring"],
                "skill_gaps": [
                    {"skill": "System Design", "gap": 25, "priority": "High"},
                    {"skill": "Leadership", "gap": 30, "priority": "Medium"},
                    {"skill": "Communication", "gap": 15, "priority": "Low"}
                ],
                "milestones": [
                    "Month 1-2: Complete advanced certifications",
                    "Month 3-4: Lead a small project",
                    "Month 5-6: Mentor junior team members",
                    "Month 7-9: Take ownership of critical systems",
                    "Month 10-12: Apply for senior positions"
                ]
            },
            "Management Track": {
                "color": "#3B82F6",
                "success_rate": 70,
                "timeline": "12-18 months",
                "target_role": "Engineering Manager / Director",
                "required_skills": ["People Management", "Strategic Planning", "Budget Management"],
                "skill_gaps": [
                    {"skill": "People Management", "gap": 40, "priority": "High"},
                    {"skill": "Strategic Thinking", "gap": 35, "priority": "High"},
                    {"skill": "Stakeholder Management", "gap": 25, "priority": "Medium"}
                ],
                "milestones": [
                    "Month 1-3: Leadership training courses",
                    "Month 4-6: Shadow current managers",
                    "Month 7-9: Lead cross-functional projects",
                    "Month 10-12: Manage a small team",
                    "Month 13-18: Transition to full management role"
                ]
            },
            "Domain Expert": {
                "color": "#8B5CF6",
                "success_rate": 60,
                "timeline": "18-24 months",
                "target_role": "Consultant / Advisor / Architect",
                "required_skills": ["Deep Domain Knowledge", "Public Speaking", "Thought Leadership"],
                "skill_gaps": [
                    {"skill": "Industry Expertise", "gap": 45, "priority": "High"},
                    {"skill": "Public Speaking", "gap": 50, "priority": "High"},
                    {"skill": "Writing/Content", "gap": 30, "priority": "Medium"}
                ],
                "milestones": [
                    "Month 1-4: Earn industry certifications",
                    "Month 5-8: Publish articles/blog posts",
                    "Month 9-12: Speak at local meetups",
                    "Month 13-18: Build consulting portfolio",
                    "Month 19-24: Establish thought leadership"
                ]
            }
        }
        
        # Display clickable career path cards
        cols = st.columns(3)
        for idx, (path_name, path_data) in enumerate(career_paths.items()):
            with cols[idx]:
                # Create clickable card
                card_selected = st.session_state.selected_career_path == path_name
                border_style = f"3px solid {path_data['color']}" if card_selected else f"1px solid {path_data['color']}50"
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {path_data['color']}40, {path_data['color']}20); 
                            padding: 20px; border-radius: 12px; border: {border_style}; 
                            cursor: pointer; transition: all 0.3s;">
                    <h4 style="color: {path_data['color']}; margin: 0;">{path_name}</h4>
                    <p style="color: #ccc; font-size: 0.85em; margin: 8px 0;">→ {path_data['target_role']}</p>
                    <p style="color: white; font-weight: bold; font-size: 1.2em;">{path_data['success_rate']}% success rate</p>
                    <p style="color: #aaa; font-size: 0.8em;">⏱️ {path_data['timeline']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Details", key=f"btn_{path_name}", use_container_width=True):
                    st.session_state.selected_career_path = path_name
                    st.rerun()
        
        # Display selected career path details
        if st.session_state.selected_career_path:
            selected_path = career_paths[st.session_state.selected_career_path]
            
            st.markdown("---")
            st.markdown(f"### 📋 {st.session_state.selected_career_path} - Detailed View")
            
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown("**🎯 Required Skill Gaps to Close:**")
                for gap in selected_path['skill_gaps']:
                    priority_color = "#ef4444" if gap['priority'] == "High" else "#f59e0b" if gap['priority'] == "Medium" else "#10b981"
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 4px solid {priority_color};">
                        <strong>{gap['skill']}</strong>: {gap['gap']}% gap 
                        <span style="color: {priority_color}; font-size: 0.8em;">({gap['priority']} Priority)</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with detail_col2:
                st.markdown("**📅 Timeline & Milestones:**")
                for milestone in selected_path['milestones']:
                    st.markdown(f"✅ {milestone}")
        
        st.markdown("---")
        
        # --- SECTION 4: 90-Day Skill Sprint Generator ---
        st.subheader("4️⃣ AI-Powered 90-Day Skill Sprint Generator")
        st.caption(f"Personalized learning plan based on your weakest skill: **{weakest_skill}**")
        
        if st.button("🚀 Generate 90-Day Sprint Plan", type="primary", use_container_width=True):
            with st.spinner("AI is creating your personalized learning plan..."):
                # Generate sprint plan using Groq if available
                if st.session_state.groq:
                    try:
                        prompt = f"""
                        Create a detailed 90-day skill sprint plan for someone who needs to improve their "{weakest_skill}" skill.
                        
                        Format the response EXACTLY as follows (use this exact structure):
                        
                        WEEK 1-2: Foundation
                        - Task: [Specific task]
                        - Resource: [Free course or resource with actual URL if possible]
                        - Project: [Small project to practice]
                        
                        WEEK 3-4: Building Blocks
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Project to build]
                        
                        WEEK 5-6: Intermediate Skills
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Project to build]
                        
                        WEEK 7-8: Advanced Concepts
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Project to build]
                        
                        WEEK 9-10: Real-World Application
                        - Task: [Specific task]
                        - Resource: [Free course or resource]
                        - Project: [Portfolio project]
                        
                        WEEK 11-12: Certification & Portfolio
                        - Task: [Get certified]
                        - Certification: [Recommended certification]
                        - Final Project: [Capstone project]
                        
                        RECOMMENDED CERTIFICATIONS:
                        1. [Certification name and provider]
                        2. [Certification name and provider]
                        3. [Certification name and provider]
                        
                        Keep it practical with free resources from Coursera, YouTube, freeCodeCamp, etc.
                        """
                        
                        completion = st.session_state.groq.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        )
                        st.session_state.sprint_plan = completion.choices[0].message.content
                        st.session_state.sprint_generated = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate plan: {e}")
                else:
                    # Fallback static plan
                    st.session_state.sprint_plan = f"""
**WEEK 1-2: Foundation**
- Task: Understand core concepts of {weakest_skill}
- Resource: YouTube - Search "{weakest_skill} for beginners"
- Project: Create a simple demo project

**WEEK 3-4: Building Blocks**
- Task: Learn intermediate techniques
- Resource: Coursera - Free courses on {weakest_skill}
- Project: Build a practical application

**WEEK 5-6: Intermediate Skills**
- Task: Deep dive into best practices
- Resource: freeCodeCamp tutorials
- Project: Contribute to open source

**WEEK 7-8: Advanced Concepts**
- Task: Master advanced patterns
- Resource: Official documentation
- Project: Complex real-world project

**WEEK 9-10: Real-World Application**
- Task: Apply skills in professional context
- Resource: Industry blogs and case studies
- Project: Portfolio-worthy project

**WEEK 11-12: Certification & Portfolio**
- Task: Get certified and polish portfolio
- Certification: Research top certifications for {weakest_skill}
- Final Project: Capstone demonstrating all skills

**RECOMMENDED CERTIFICATIONS:**
1. Check Coursera for {weakest_skill} certifications
2. LinkedIn Learning certificates
3. Industry-specific certifications
                    """
                    st.session_state.sprint_generated = True
                    st.rerun()
        
        # Display generated sprint plan with progress tracker
        if st.session_state.sprint_generated and st.session_state.sprint_plan:
            st.markdown("---")
            st.markdown("### 📚 Your Personalized 90-Day Plan")
            
            # Parse and display with checkboxes
            plan_lines = st.session_state.sprint_plan.split('\n')
            current_week = ""
            
            for i, line in enumerate(plan_lines):
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('**WEEK') or line.startswith('WEEK'):
                    current_week = line.replace('**', '').replace('*', '')
                    st.markdown(f"#### {current_week}")
                elif line.startswith('- ') or line.startswith('• '):
                    task_key = f"task_{i}"
                    task_text = line[2:].strip()
                    
                    # Checkbox for progress tracking
                    completed = st.checkbox(
                        task_text, 
                        key=task_key,
                        value=task_key in st.session_state.completed_tasks
                    )
                    if completed:
                        st.session_state.completed_tasks.add(task_key)
                    elif task_key in st.session_state.completed_tasks:
                        st.session_state.completed_tasks.remove(task_key)
                        
                elif line.startswith('**RECOMMENDED') or line.startswith('RECOMMENDED'):
                    st.markdown(f"#### 🏆 {line.replace('**', '')}")
                elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                    st.markdown(f"  {line}")
            
            # Progress bar
            total_tasks = len([l for l in plan_lines if l.strip().startswith('- ') or l.strip().startswith('• ')])
            completed_count = len(st.session_state.completed_tasks)
            if total_tasks > 0:
                progress = completed_count / total_tasks
                st.markdown("---")
                st.markdown(f"**📊 Overall Progress: {completed_count}/{total_tasks} tasks completed**")
                st.progress(progress)
        
        st.markdown("---")
        
        # --- SECTION 5: Skill Decay Warning System ---
        st.subheader("5️⃣ Skill Decay Warning System")
        st.caption("⚠️ Track skills that may need refreshing")
        
        # Simulated skill decay data (in production, this would come from user's activity history)
        tech_score = report.get('tech_score', 50)
        
        skill_decay_data = [
            {"skill": weakest_skill, "last_updated": "Recently analyzed", "status": "current", "decay_risk": "Low"},
            {"skill": "Core Technical Skills", "last_updated": "3 months ago", "status": "moderate", "decay_risk": "Medium"},
            {"skill": "Industry Knowledge", "last_updated": "6 months ago", "status": "outdated", "decay_risk": "High"},
        ]
        
        for skill_data in skill_decay_data:
            if skill_data['status'] == 'outdated':
                color = "#ef4444"
                icon = "🔴"
                message = f"⚠️ Your {skill_data['skill']} knowledge may be outdated - last updated {skill_data['last_updated']}"
            elif skill_data['status'] == 'moderate':
                color = "#f59e0b"
                icon = "🟡"
                message = f"⏰ {skill_data['skill']} could use a refresh - last updated {skill_data['last_updated']}"
            else:
                color = "#10b981"
                icon = "🟢"
                message = f"✅ {skill_data['skill']} is up to date - {skill_data['last_updated']}"
            
            st.markdown(f"""
            <div style="background: {color}15; border-left: 4px solid {color}; padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong>{icon} {skill_data['skill']}</strong><br>
                <span style="color: #ccc;">{message}</span><br>
                <span style="color: {color}; font-size: 0.85em;">Decay Risk: {skill_data['decay_risk']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Refresh course suggestions
        with st.expander("📖 Suggested Refresh Courses"):
            st.markdown("""
            **Free Resources to Keep Your Skills Sharp:**
            
            🎓 **Coursera** - Audit courses for free
            - [Browse all free courses](https://www.coursera.org/courses?query=free)
            
            📺 **YouTube Channels:**
            - Traversy Media (Web Development)
            - Tech With Tim (Python)
            - freeCodeCamp (Full tutorials)
            
            📚 **Other Free Resources:**
            - [freeCodeCamp](https://www.freecodecamp.org/)
            - [The Odin Project](https://www.theodinproject.com/)
            - [Khan Academy](https://www.khanacademy.org/)
            - [edX Free Courses](https://www.edx.org/search?tab=course)
            """)
        
        st.markdown("---")
        
        # --- SECTION 6: Skill Gap Analysis Summary ---
        st.subheader("6️⃣ Skill Gap Analysis Summary")
        
        # Create visual skill gap bars
        skills_to_analyze = [
            {"name": "Technical Foundation", "current": tech_score, "target": 90},
            {"name": "Leadership & Soft Skills", "current": report.get('leader_score', 50), "target": 80},
            {"name": weakest_skill, "current": max(20, tech_score - 30), "target": 85},
            {"name": "Industry Knowledge", "current": min(90, tech_score + 10), "target": 85},
        ]
        
        for skill in skills_to_analyze:
            gap = skill['target'] - skill['current']
            gap_color = "#ef4444" if gap > 30 else "#f59e0b" if gap > 15 else "#10b981"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{skill['name']}**")
                st.progress(skill['current'] / 100)
            with col2:
                if gap > 0:
                    st.markdown(f"<span style='color: {gap_color};'>Gap: {gap}%</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: #10b981;'>✅ On target</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 Upload a new CV anytime to refresh your analysis and track your progress!")
        
    else:
        st.warning("No analysis found.")
        st.write("Upload your CV above and click **'Analyze CV'** to see your Skill Migration report.")

def page_cover_letter():
    st.header("✍️ Instant Cover Letter")
    
    c1, c2 = st.columns(2)
    with c1: jd_text = st.text_area("Paste Job Description:", height=300)
    with c2: uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"], key="cl_uploader")
    
    if st.button("Generate Letter", type="primary"):
        if not st.session_state.groq: return st.error("Groq API Key missing.")
        if not uploaded_file: return st.warning("Please upload your CV.")

        try:
            user_cv_text = extract_text(uploaded_file)
            if jd_text and user_cv_text:
                with st.spinner("Writing..."):
                    prompt = f"""
                    You are an expert career coach. Write a professional cover letter.
                    CANDIDATE INFO: {user_cv_text[:4000]} 
                    JOB DESCRIPTION: {jd_text}
                    INSTRUCTIONS: Match skills to job. Professional tone. No placeholders.
                    """
                    completion = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile" 
                    )
                    letter = completion.choices[0].message.content
                    st.subheader("Draft:")
                    st.write(letter)
                    
                    pdf_bytes = create_pdf(letter)
                    if pdf_bytes:
                        st.download_button("📥 Download PDF", pdf_bytes, "cover_letter.pdf", "application/pdf")
                    else:
                        st.download_button("📥 Download Text (Fallback)", letter, "cover_letter.txt", "text/plain")
            else: st.warning("Please provide both CV and Job Description.")
        except Exception as e: st.error(f"Error: {e}")

import re
import numpy as np
import pandas as pd

# --- CV Compiler Helper Functions ---
def calculate_ats_compliance(cv_text, jd_text):
    """Calculate ATS keyword match percentage"""
    if not cv_text or not jd_text: return 0
    cv_words = set(re.findall(r'\b\w{3,}\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w{3,}\b', jd_text.lower()))
    intersection = len(cv_words.intersection(jd_words))
    union = len(cv_words.union(jd_words))
    score = (intersection / union) * 100 if union > 0 else 0
    return int(np.clip(score, 0, 100))

def calculate_human_clarity(text):
    """Calculate readability/clarity score"""
    if not text: return 0
    metric_count = len(re.findall(r'\d[\d,\.]*', text))
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    total_words = len(re.findall(r'\b\w+\b', text))
    avg_words = total_words / len(sentences) if sentences else 0
    clarity = 50
    if 0 < avg_words < 15:
        clarity += (15 - avg_words) * 1.0
    clarity += min(30, metric_count * 5)
    return int(np.clip(clarity, 40, 100))

def fetch_application_ledger(user_id):
    """Fetch user's application history"""
    if not supabase: return pd.DataFrame()
    try:
        res = supabase.table("applications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df.rename(columns={
                "created_at": "Date", "company_name": "Company", "job_id": "JobID",
                "compliance_score": "Compliance", "clarity_score": "Clarity", "outcome": "Outcome"
            })
            return df
    except: pass
    return pd.DataFrame()

def save_application(user_id, company, job_id, comp, clar):
    """Save application to database"""
    if not supabase: return False
    try:
        supabase.table("applications").insert({
            "user_id": user_id, "company_name": company, "job_id": job_id,
            "compliance_score": comp, "clarity_score": clar, "outcome": "Pending"
        }).execute()
        return True
    except: return False

def update_application_status(app_id, new_status):
    """Update application outcome"""
    if not supabase: return
    try:
        supabase.table("applications").update({"outcome": new_status}).eq("id", app_id).execute()
    except: pass

# --- CV Compiler Page ---
def page_cv_compiler():
    st.header("🤖 CV Compiler & Optimizer")
    st.caption("All-in-one: Optimize your CV, check ATS compliance, and track applications")
    
    # --- SECTION 1: Smart CV Tailor ---
    st.subheader("1️⃣ Smart CV Tailor")
    
    col_upload, col_jd = st.columns(2)
    with col_upload:
        uploaded_file = st.file_uploader("Upload your CV (PDF)", type=["pdf"], key="compiler_cv_upload")
    with col_jd:
        jd_text = st.text_area("Paste Job Description:", height=150, key="compiler_jd")
    
    # Extract CV text
    cv_text = ""
    if uploaded_file:
        cv_text = extract_text(uploaded_file)
        st.session_state['compiler_cv_text'] = cv_text
    elif 'compiler_cv_text' in st.session_state:
        cv_text = st.session_state['compiler_cv_text']
    
    if st.button("🚀 Optimize Bullets", type="primary", use_container_width=True):
        if not st.session_state.groq:
            st.error("Groq API Key missing.")
        elif not cv_text or cv_text.strip() == "":
            st.warning("Please upload a CV.")
        elif not jd_text or jd_text.strip() == "":
            st.warning("Please paste the Job Description.")
        else:
            try:
                with st.spinner("AI is optimizing your CV..."):
                    prompt = f"""
                    Act as an ATS Optimization Expert.
                    JOB DESCRIPTION: {jd_text}
                    CURRENT CV: {cv_text[:4000]}
                    
                    TASK: Rewrite the CV bullet points to include relevant keywords from the job description.
                    
                    IMPORTANT FORMATTING RULES:
                    - Output ONLY plain text bullet points
                    - Start each bullet with a dash (-) or bullet (•)
                    - DO NOT use any markdown formatting like ** or * or # or __
                    - DO NOT use bold, italic, or any special formatting
                    - Keep each bullet concise and professional
                    - Focus on action verbs and quantified achievements
                    
                    Output the optimized bullets now:
                    """
                    completion = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile"
                    )
                    if completion and completion.choices:
                        optimized = completion.choices[0].message.content
                        # Clean any remaining markdown formatting
                        optimized = optimized.replace('**', '').replace('__', '').replace('*', '•')
                        if optimized and optimized.strip():
                            st.session_state['compiler_optimized'] = optimized
                            st.session_state['compiler_original'] = cv_text[:1000]
                            st.session_state['compiler_jd_stored'] = jd_text
                        else:
                            st.error("Empty response from AI.")
                    else:
                        st.error("No response received.")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # Display optimization results
    if 'compiler_optimized' in st.session_state:
        st.markdown("---")
        col_orig, col_opt = st.columns(2)
        with col_orig:
            st.info("📄 Original CV Preview")
            st.text(st.session_state.get('compiler_original', '')[:800] + "...")
        with col_opt:
            st.success("✨ Optimized Bullets")
            st.text_area("", st.session_state['compiler_optimized'], height=300, disabled=True, label_visibility="collapsed")
        
        # Download buttons
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            try:
                pdf_bytes = create_pdf(st.session_state['compiler_optimized'])
                if pdf_bytes:
                    st.download_button("📥 Download Optimized PDF", pdf_bytes, "optimized_cv.pdf", "application/pdf", use_container_width=True)
            except:
                pass
        with col_dl2:
            st.download_button("📥 Download as Text", st.session_state['compiler_optimized'], "optimized_cv.txt", "text/plain", use_container_width=True)
    
    # --- SECTION 2: Dual Optimization Dashboard ---
    st.markdown("---")
    st.subheader("2️⃣ Dual Optimization Dashboard")
    
    jd_for_analysis = st.session_state.get('compiler_jd_stored', jd_text)
    
    if cv_text and jd_for_analysis:
        ats_score = calculate_ats_compliance(cv_text, jd_for_analysis)
        clarity_score = calculate_human_clarity(cv_text)
        
        col_ats, col_clarity = st.columns(2)
        
        with col_ats:
            delta_ats = "✅ Good!" if ats_score >= 70 else f"→ Target: 95%"
            st.metric("ATS Compliance", f"{ats_score}%", delta=delta_ats)
            st.progress(ats_score / 100)
            if ats_score < 70:
                st.caption("💡 Tip: Add more keywords from the job description")
        
        with col_clarity:
            delta_clarity = "✅ Good!" if clarity_score >= 75 else f"→ Target: 75%"
            st.metric("Human Clarity", f"{clarity_score}%", delta=delta_clarity)
            st.progress(clarity_score / 100)
            if clarity_score < 75:
                st.caption("💡 Tip: Use shorter sentences and add metrics")
    else:
        st.info("Upload a CV and paste a Job Description to see your optimization scores.")
        ats_score = 0
        clarity_score = 0
    
    # --- SECTION 3: Log Finalized Application ---
    st.markdown("---")
    st.subheader("3️⃣ Log Finalized Application")
    
    col_company, col_job, col_log = st.columns([2, 2, 1])
    company_name = col_company.text_input("Company Name", key="log_company")
    job_title = col_job.text_input("Job Title/ID", key="log_job")
    
    with col_log:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📝 Log Application", type="secondary", use_container_width=True):
            if company_name and job_title:
                if save_application(st.session_state.user_id, company_name, job_title, ats_score, clarity_score):
                    st.success("✅ Application logged!")
                    st.rerun()
                else:
                    st.error("Failed to save.")
            else:
                st.warning("Enter company and job title.")
    
    # --- SECTION 4: Application History Ledger ---
    st.markdown("---")
    st.subheader("4️⃣ Application History Ledger")
    
    df_ledger = fetch_application_ledger(st.session_state.user_id)
    
    if not df_ledger.empty:
        # Display table
        st.dataframe(
            df_ledger[['Company', 'JobID', 'Outcome', 'Compliance', 'Clarity']],
            use_container_width=True,
            hide_index=True
        )
        
        # Update outcome
        st.caption("Update Application Status")
        col_sel, col_status, col_update = st.columns([3, 2, 1])
        
        options = {f"{row['Company']} - {row['JobID']}": row['id'] for _, row in df_ledger.iterrows()}
        selected = col_sel.selectbox("Select Application", list(options.keys()), key="update_select")
        new_status = col_status.selectbox("New Status", ['Pending', 'Interview', 'Rejected', 'Offer'], key="update_status")
        
        with col_update:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Update", use_container_width=True):
                update_application_status(options[selected], new_status)
                st.success("Updated!")
                st.rerun()
    else:
        st.info("No applications logged yet. Start tracking your job applications above!")

def page_interview_sim():
    st.header("🎤 Voice Interview Simulator")
    
    if 'interview_q' not in st.session_state:
        st.session_state.interview_q = "Tell me about yourself?"
    
    jd_context = st.text_input("Enter Job Role (e.g. 'Senior Python Dev'):")
    if st.button("Generate Question"):
        if st.session_state.groq:
            try:
                q_resp = st.session_state.groq.chat.completions.create(
                    messages=[{"role": "user", "content": f"Ask a tough behavioural question for {jd_context}."}],
                    model="llama-3.1-8b-instant"
                )
                st.session_state.interview_q = q_resp.choices[0].message.content
            except Exception as e: st.error(f"Error: {e}")
    
    st.markdown(f"### 🤖 AI asks: *{st.session_state.interview_q}*")
    audio_val = st.audio_input("Record your answer")
    
    if audio_val:
        if not st.session_state.groq: st.error("Groq API Key missing.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    transcription = st.session_state.groq.audio.transcriptions.create(
                        file=("audio.wav", audio_val, "audio/wav"),
                        model="whisper-large-v3", 
                        response_format="text"
                    )
                    st.info(f"🗣 You said: '{transcription}'")
                    feedback = st.session_state.groq.chat.completions.create(
                        messages=[{"role": "user", "content": f"Rate this interview answer 1-10: '{transcription}' for question '{st.session_state.interview_q}'"}],
                        model="llama-3.1-8b-instant"
                    )
                    st.success("Feedback:")
                    st.write(feedback.choices[0].message.content)
                except Exception as e: st.error(f"Error: {e}")

# --- 6. NEW MENU SYSTEM ---

def render_top_nav():
    """Render the top navigation bar with hamburger menu"""
    username = st.session_state.user.split('@')[0] if st.session_state.user else "User"
    
    st.markdown(f"""
    <div class="top-nav-bar">
        <div class="nav-logo">🚀 Job-Search-Agent</div>
        <div class="user-info">Welcome, <span>{username}</span></div>
    </div>
    """, unsafe_allow_html=True)

def render_menu():
    """Render the navigation menu using Streamlit components"""
    # Add spacing for top nav
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    
    # Menu items matching the screenshot
    menu_items = [
        ("🏠", "Main Page"),
        ("🧘", "Emotional Tracker"),
        ("🔄", "Feedback Loop"),
        ("📈", "Skill Migration"),
        ("🤖", "CV Compiler"),
        ("🔒", "Privacy Policy"),
        ("🔑", "Reset Password"),
        ("💬", "Support"),
        ("⚙️", "Account Settings"),
    ]
    
    # Sidebar-style menu at the top
    st.markdown("""
    <style>
    .menu-container {
        background: rgba(255, 107, 53, 0.05);
        border: 1px solid rgba(255, 107, 53, 0.2);
        border-radius: 16px;
        padding: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create horizontal menu
    cols = st.columns(len(menu_items))
    for idx, (icon, name) in enumerate(menu_items):
        with cols[idx]:
            is_active = st.session_state.current_page == name
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon}", key=f"menu_{name}", help=name, use_container_width=True):
                st.session_state.current_page = name
                st.rerun()
    
    # Show current page name
    st.markdown(f"""
    <div style="text-align: center; margin: 10px 0 20px 0;">
        <span style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.2rem; font-weight: 600;">
            {st.session_state.current_page}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Logout button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col3:
        if st.button("🚪 Logout", key="logout_btn"):
            logout()

# --- 7. MAIN APP ---

def main():
    # Inject JavaScript to handle URL fragments from Supabase password reset
    inject_fragment_handler()
    
    # Check for password reset token in URL first
    is_password_reset = check_password_reset_token()
    if is_password_reset:
        st.session_state.password_reset_mode = True
    
    if not st.session_state.user:
        with st.container():
            c1, c2, c3 = st.columns([1,1,1])
            with c2:
                # Check if user is in password reset mode (came from email link)
                if st.session_state.password_reset_mode:
                    st.header("🔐 Set New Password")
                    st.caption("Enter your new password below.")
                    
                    new_password = st.text_input("New Password", type="password", key="new_pwd_input")
                    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pwd_input")
                    
                    col_update, col_cancel = st.columns(2)
                    with col_update:
                        if st.button("✅ Update Password", type="primary", use_container_width=True):
                            if new_password != confirm_password:
                                st.error("Passwords do not match!")
                            elif len(new_password) < 6:
                                st.error("Password must be at least 6 characters long.")
                            else:
                                success, message = update_password(new_password)
                                if success:
                                    st.success(message)
                                    st.session_state.password_reset_mode = False
                                    # Clear URL parameters
                                    st.query_params.clear()
                                    st.info("Redirecting to login page...")
                                    import time
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(message)
                    with col_cancel:
                        if st.button("← Back to Login", use_container_width=True):
                            st.session_state.password_reset_mode = False
                            st.query_params.clear()
                            st.rerun()
                
                # Check if showing forgot password form
                elif st.session_state.show_forgot_password:
                    st.header("Job-Search-Agent Login")
                    st.subheader("🔑 Reset Password")
                    st.caption("Enter your email address and we'll send you a link to reset your password.")
                    reset_email = st.text_input("Email Address", key="reset_email_input")
                    
                    col_reset, col_back = st.columns(2)
                    with col_reset:
                        if st.button("📧 Send Reset Link", type="primary", use_container_width=True):
                            success, message = forgot_password(reset_email)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    with col_back:
                        if st.button("← Back to Login", use_container_width=True):
                            st.session_state.show_forgot_password = False
                            st.rerun()
                else:
                    # Normal login/signup flow
                    st.markdown("""
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="background: linear-gradient(90deg, #ff6b35, #f7c531); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem;">
                            🚀 Job-Search-Agent
                        </h1>
                        <p style="color: #888;">AI-Powered Career Guidance</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    mode = st.radio("Mode", ["Login", "Sign Up"], horizontal=True)
                    email = st.text_input("Email")
                    pwd = st.text_input("Password", type="password")
                    if mode == "Sign Up":
                        user = st.text_input("Username")
                        if st.button("Sign Up", type="primary", use_container_width=True): signup(email, pwd, user)
                    else:
                        if st.button("Login", type="primary", use_container_width=True): login(email, pwd)
                        # Forgot Password link
                        st.markdown("---")
                        if st.button("🔑 Forgot Password?", type="secondary", use_container_width=True):
                            st.session_state.show_forgot_password = True
                            st.rerun()
        return

    # === LOGGED IN USER - SHOW NEW MENU SYSTEM ===
    
    # Render top navigation
    render_top_nav()
    
    # Render menu
    render_menu()
    
    # Route to correct page based on selection
    if st.session_state.current_page == "Main Page":
        st.title("🚀 Career Strategy Dashboard")
        with st.container():
            c1, c2 = st.columns([2,1])
            with c1:
                role = st.selectbox("Target Role", ["All", "Data Science", "Sales", "Engineering"])
                f = st.file_uploader("Upload CV for Strategy", type=["pdf", "txt"])
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Generate Strategy", type="primary"):
                    if f and st.session_state.agent:
                        with st.spinner("Agent working..."):
                            txt = extract_text(f)
                            md, rep, src = st.session_state.agent.generate_strategy(txt, role)
                            st.session_state.results = {"md": md, "rep": rep, "src": src}
                            
                            # Save to Supabase
                            if supabase and st.session_state.user_id:
                                try:
                                    supabase.table("analyses").insert({
                                        "user_id": st.session_state.user_id,
                                        "report_json": rep
                                    }).execute()
                                except: pass
                            st.rerun()

        if "results" in st.session_state:
            res = st.session_state.results
            with st.container():
                st.metric("Match Score", f"{res['rep'].get('predictive_score')}%")
                st.markdown(res['md'])
                
    elif st.session_state.current_page == "Emotional Tracker":
        st.switch_page("pages/1_Emotional_Tracker.py")
        
    elif st.session_state.current_page == "Feedback Loop":
        st.switch_page("pages/2_Feedback_Loop.py")
        
    elif st.session_state.current_page == "Skill Migration":
        page_skill_migration()
        
    elif st.session_state.current_page == "CV Compiler":
        page_cv_compiler()
        
    elif st.session_state.current_page == "Privacy Policy":
        st.header("🔒 Privacy Policy")
        st.markdown("""
        ## Privacy Policy for Job-Search-Agent
        
        **Last Updated: January 2026**
        
        ### Information We Collect
        - **Account Information:** Email address and username for authentication
        - **CV/Resume Data:** Documents you upload for analysis
        - **Usage Data:** Interaction with our AI features
        - **Voice Data:** Temporary recordings for interview simulation (not stored permanently)
        
        ### How We Use Your Data
        - To provide personalized career guidance
        - To analyze your CV and generate recommendations
        - To track your job applications
        - To improve our AI models and services
        
        ### Data Security
        - All data is encrypted in transit and at rest
        - We use industry-standard security practices
        - Your data is stored securely on Supabase
        
        ### Your Rights
        - Access your personal data
        - Delete your account and all associated data
        - Export your data
        - Opt-out of non-essential data collection
        
        ### Contact
        For privacy inquiries: jobsearchagent26@gmail.com
        """)
        
    elif st.session_state.current_page == "Reset Password":
        st.header("🔑 Reset Password")
        st.caption("Enter your email to receive a password reset link.")
        
        reset_email = st.text_input("Email Address", key="reset_page_email")
        if st.button("📧 Send Reset Link", type="primary"):
            success, message = forgot_password(reset_email)
            if success:
                st.success(message)
            else:
                st.error(message)
        
    elif st.session_state.current_page == "Support":
        st.switch_page("pages/Support.py")
        
    elif st.session_state.current_page == "Account Settings":
        page_delete_account()

if __name__ == "__main__":
    main()
