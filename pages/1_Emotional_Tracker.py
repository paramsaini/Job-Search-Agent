import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
from supabase import create_client
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Emotional Tracker - Job-Search-Agent", page_icon="🧘", layout="wide")

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
    
    .stSlider>div>div>div>div {
        background: linear-gradient(90deg, #ff6b35, #f7c531) !important;
    }
    
    /* Back button style */
    .back-btn {
        background: rgba(255, 107, 53, 0.1);
        border: 1px solid rgba(255, 107, 53, 0.3);
        border-radius: 10px;
        padding: 10px 20px;
        color: #ff6b35;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .back-btn:hover {
        background: rgba(255, 107, 53, 0.2);
        box-shadow: 0 0 15px rgba(255, 107, 53, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Configuration ---
BG_DARK = "#0a0a0f"
ACCENT_ORANGE = "#ff6b35"
ACCENT_GOLD = "#f7c531"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    def get_secret(key):
        if key in os.environ:
            return os.environ[key]
        try:
            return st.secrets[key]
        except:
            return None

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key: return None
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    supabase = None

# --- Logic ---

def fetch_mood_history(user_id):
    """Retrieves full mood history from Supabase."""
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table("mood_logs").select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=False).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.rename(columns={"mood_score": "Mood", "activity_score": "Activity", "created_at": "Date"})
            return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
    return pd.DataFrame()

def calculate_resilience(df):
    """Calculates Resilience Score (0-100) from DB history."""
    if df.empty: return 75
    
    recent_df = df.tail(7) 
    avg_mood = recent_df['Mood'].mean() * 10
    avg_activity = recent_df['Activity'].mean() * 20
    
    resilience = (0.7 * avg_mood) + (0.3 * avg_activity)
    return int(np.clip(resilience, 30, 100))

def log_mood_to_db(user_id, mood, activity, notes):
    """Inserts new entry to Supabase."""
    if not supabase: return
    try:
        supabase.table("mood_logs").insert({
            "user_id": user_id,
            "mood_score": mood,
            "activity_score": activity,
            "notes": notes
        }).execute()
        st.success("✅ Logged to Cloud Database!")
    except Exception as e:
        st.error(f"Save Failed: {e}")

# --- Page Render ---

def emotional_tracker_page():
    # Back to Main Page button
    if st.button("← Back to Main Page", key="back_btn"):
        st.switch_page("Main_Page.py")
    
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
    
    # Custom styled header
    st.markdown(f"""
    <h1 style="text-align: center; font-size: 2.5rem;">
        🧘 Emotional Endurance Tracker
    </h1>
    """, unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.get('user_id'):
        st.warning("🔒 Please log in to track your resilience.")
        return

    # Load Data
    df_history = fetch_mood_history(st.session_state.user_id)
    resilience_score = calculate_resilience(df_history)

    # --- Resilience Card ---
    if resilience_score >= 80:
        status, color = "Optimal Momentum 💪", ACCENT_GREEN
        tip = "Keep this structure! You're converting effort into positive feeling."
    elif resilience_score >= 60:
        status, color = "Steady State 😌", ACCENT_YELLOW
        tip = "Maintain awareness. Use a Weakest Link resource from the main page."
    else:
        status, color = "Burnout Risk! ⚠️", ACCENT_ORANGE
        tip = "Take a mandatory break or focus on a low-stress activity."
    
    st.markdown(f"""
    <div style="padding: 30px; border-radius: 16px; border: 2px solid {color};
        background: rgba(255, 107, 53, 0.05); box-shadow: 0 0 25px {color}40; text-align: center; margin-bottom: 20px;">
        <p style="color: {color}; font-size: 1.3rem; margin: 0;">Current Resilience Status:</p>
        <div style="font-size: 5rem; font-weight: bold; color: {color}; text-shadow: 0 0 30px {color}80;">{resilience_score}</div>
        <p style="color: {color}; font-weight: bold; margin: 5px 0 0 0; font-size: 1.2rem;">{status}</p>
        <p style="color: #ccc; font-size: 0.95rem; margin-top: 10px;">*AI Insight: {tip}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Logging Form ---
    st.subheader("Daily Check-in")
    with st.form("mood_form"):
        c1, c2 = st.columns(2)
        mood = c1.slider("Mood (1-10)", 1, 10, 5)
        activity = c2.slider("Activity Level (0-5)", 0, 5, 3)
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Log Emotional Data", type="primary", use_container_width=True):
            log_mood_to_db(st.session_state.user_id, mood, activity, notes)
            st.rerun()

    # --- History Chart ---
    if not df_history.empty:
        st.subheader("History & Trends")
        chart_df = df_history.set_index('Date')[['Mood', 'Activity']]
        st.line_chart(chart_df, color=[ACCENT_ORANGE, ACCENT_GOLD])

emotional_tracker_page()
