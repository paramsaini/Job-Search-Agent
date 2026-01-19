import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
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
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- Logic ---

def fetch_mood_history(user_id):
    """Retrieves full mood history from Supabase."""
    try:
        response = supabase.table("mood_logs").select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=False).execute() # Ascending for chart
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['created_at'] = pd.to_datetime(df['created_at'])
            return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
    return pd.DataFrame()

def calculate_resilience(df):
    """Calculates Resilience Score (0-100) from DB history."""
    if df.empty: return 75
    
    recent_df = df.tail(7) 
    avg_mood = recent_df['mood_score'].mean() * 10
    avg_activity = recent_df['activity_score'].mean() * 20
    
    resilience = (0.7 * avg_mood) + (0.3 * avg_activity)
    return int(np.clip(resilience, 30, 100))

def log_mood_to_db(user_id, mood, activity, notes):
    """Inserts new entry to Supabase."""
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
    elif resilience_score >= 60:
        status, color = "Steady State 😌", ACCENT_YELLOW
    else:
        status, color = "Burnout Risk! ⚠️", ACCENT_ORANGE
    
    st.markdown(f"""
    <div style="padding: 20px; border-radius: 10px; border: 2px solid {color}; background: {BG_DARK}; text-align: center; margin-bottom: 20px;">
        <p style="color: {color}; font-size: 1.2rem; margin: 0;">Live Resilience Score</p>
        <div style="font-size: 4rem; font-weight: bold; color: {color};">{resilience_score}</div>
        <p style="color: white; font-weight: bold;">{status}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- Logging Form ---
    st.subheader("Daily Check-in")
    with st.form("mood_form"):
        c1, c2 = st.columns(2)
        mood = c1.slider("Mood (1-10)", 1, 10, 5)
        activity = c2.slider("Activity Level (0-5)", 0, 5, 3)
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Log Entry", type="primary"):
            log_mood_to_db(st.session_state.user_id, mood, activity, notes)
            st.rerun()

    # --- History Chart ---
    if not df_history.empty:
        st.markdown("---")
        st.subheader("Trend Analysis")
        chart_df = df_history.set_index('created_at')[['mood_score', 'activity_score']]
        st.line_chart(chart_df, color=[ACCENT_CYAN, ACCENT_ORANGE])

emotional_tracker_page()
