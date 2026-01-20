import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
from supabase import create_client

# --- Configuration ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Supabase Init ---
@st.cache_resource
def init_supabase():
    # Helper to get secrets from EITHER Railway (Env) OR Local (File)
    def get_secret(key):
        if key in os.environ:
            return os.environ[key]
        try:
            return st.secrets[key]
        except:
            return None

    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key:
        return None
    return create_client(url, key)

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
            # Rename for compatibility with chart logic
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
    # Style injection kept from original
    st.markdown(f"""
    <style>
    .resilience-card {{
        padding: 20px; border-radius: 10px; border: 2px solid {ACCENT_ORANGE};
        background: {BG_DARK}; box-shadow: 0 0 15px {ACCENT_ORANGE}50; text-align: center; margin-bottom: 20px;
    }}
    .resilience-score {{ font-size: 4rem; font-weight: bold; color: {ACCENT_CYAN}; text-shadow: 0 0 10px {ACCENT_CYAN}; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🧘 Aequor: Emotional Endurance</h1>', unsafe_allow_html=True)
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
    <div class="resilience-card" style="border-color: {color}; box-shadow: 0 0 15px {color}50;">
        <p style="color: {color}; font-size: 1.2rem; margin: 0;">Current Resilience Status:</p>
        <div class="resilience-score" style="color: {color}; text-shadow: 0 0 10px {color}80;">{resilience_score}</div>
        <p style="color: {color}; font-weight: bold; margin: 5px 0 0 0;">{status}</p>
        <p style="color: #ccc; font-size: 0.9rem; margin-top: 5px;">*AI Insight: {tip}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Logging Form ---
    st.subheader("Daily Check-in")
    with st.form("mood_form"):
        c1, c2 = st.columns(2)
        mood = c1.slider("Mood (1-10)", 1, 10, 5)
        activity = c2.slider("Activity Level (0-5)", 0, 5, 3)
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Log Emotional Data", type="primary"):
            log_mood_to_db(st.session_state.user_id, mood, activity, notes)
            st.rerun()

    # --- History Chart ---
    if not df_history.empty:
        st.subheader("History & Trends")
        chart_df = df_history.set_index('Date')[['Mood', 'Activity']]
        st.line_chart(chart_df, color=[ACCENT_CYAN, ACCENT_ORANGE])

emotional_tracker_page()
