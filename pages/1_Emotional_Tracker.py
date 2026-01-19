import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np

# --- Configuration (Copied from main app for consistency) ---
BG_DARK = "#000000"
ACCENT_CYAN = "#00E0FF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#10B981"
ACCENT_YELLOW = "#F59E0B"

# --- Initialization ---
if 'mood_history' not in st.session_state:
    # DataFrame to store mood (1-10) and activity (0-5, proxy for application intensity)
    st.session_state['mood_history'] = pd.DataFrame(columns=['Date', 'Mood', 'Activity', 'Notes'])

if 'resilience_score' not in st.session_state:
    st.session_state['resilience_score'] = 75 # Starting score

# --- Core Logic ---

def calculate_resilience(df):
    """Calculates a simple Resilience Score (0-100) based on recent mood and activity."""
    if df.empty:
        return 75
    
    # Simple weighted average: Mood is 70% of score, Recent Activity is 30%
    recent_df = df.tail(7) 
    avg_mood = recent_df['Mood'].mean() * 10
    avg_activity = recent_df['Activity'].mean() * 20
    
    # Calculate difference between emotional input and effort output
    # If Mood > Activity, score is boosted. If Mood < Activity (Burnout Risk), score is penalized.
    resilience = (0.7 * avg_mood) + (0.3 * avg_activity)
    
    return int(np.clip(resilience, 30, 100)) # Clamp score between 30 and 100

def log_mood_entry(mood, activity, notes):
    """Logs the new mood and recalculates the resilience score."""
    new_entry = pd.DataFrame([{
        'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Mood': mood,
        'Activity': activity,
        'Notes': notes
    }])
    st.session_state['mood_history'] = pd.concat([st.session_state['mood_history'], new_entry], ignore_index=True)
    st.session_state['resilience_score'] = calculate_resilience(st.session_state['mood_history'])
    st.success("Mood and Activity Logged! Resilience Score Updated.")

# --- Page Render Function ---

def emotional_tracker_page():
    
    st.markdown(f"""
    <style>
    /* Styling for the Resilience Card */
    .resilience-card {{
        padding: 20px;
        border-radius: 10px;
        border: 2px solid {ACCENT_ORANGE};
        background: {BG_DARK};
        box-shadow: 0 0 15px {ACCENT_ORANGE}50;
        text-align: center;
        margin-bottom: 20px;
    }}
    .resilience-score {{
        font-size: 4rem;
        font-weight: bold;
        color: {ACCENT_CYAN};
        text-shadow: 0 0 10px {ACCENT_CYAN};
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # --- New Name Integration ---
    st.markdown(f'<h1 class="holo-text" style="color:{ACCENT_ORANGE}; text-align: center;">🧘 Aequor: Emotional Endurance</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <p style="text-align: center; color: {ACCENT_CYAN}; font-size: 1.1em; font-weight: 500; text-shadow: 0 0 2px {ACCENT_CYAN}40;">
        **Optimize Your Inner Game:** Track your **Emotional Input** (Mood) against your **Career Output** (Activity) to calculate your live **Resilience Score**. Defeat burnout before it starts.
    </p>
    """, unsafe_allow_html=True)
    st.markdown("---")
    # ---------------------------

    # --- Resilience Score Display ---
    current_score = st.session_state['resilience_score']
    
    # Determine Status
    if current_score >= 80:
        status = "Optimal Momentum 💪"
        tip = "Keep this structure! You're converting effort into positive feeling."
        color = ACCENT_GREEN
    elif current_score >= 60:
        status = "Steady State 😌"
        tip = "Maintain awareness. Use a Weakest Link resource from the main page."
        color = ACCENT_YELLOW
    else:
        status = "Burnout Risk! ⚠️"
        tip = "Take a mandatory break or focus on a low-stress activity. Quality over quantity now."
        color = ACCENT_ORANGE
    
    # Trigger image suggestion for visualization
    st.markdown(f"""
    <div class="resilience-card" style="border-color: {color}; box-shadow: 0 0 15px {color}50;">
        <p style="color: {color}; font-size: 1.2rem; margin: 0;">Current Resilience Status:</p>
        <div class="resilience-score" style="color: {color}; text-shadow: 0 0 10px {color}80;">{current_score}</div>
        <p style="color: {color}; font-weight: bold; margin: 5px 0 0 0;">{status}</p>
        <p style="color: #ccc; font-size: 0.9rem; margin-top: 5px;">*AI Insight: {tip}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Logging Section ---
    st.subheader("Daily Check-in")
    
    with st.form("mood_form"):
        col_mood, col_activity = st.columns(2)
        
        with col_mood:
            mood = st.slider(
                "1. Current Emotional State (1: Drained ➡️ 10: Motivated)",
                1, 10, 5, key="mood_slider"
            )
        
        with col_activity:
            activity = st.slider(
                "2. Application Intensity Today (1: Browsed ➡️ 5: 5+ Applications)",
                1, 5, 3, key="activity_slider"
            )
            
        notes = st.text_area("Optional: Notes on today's triggers (e.g., 'Rejection letter', 'Great interview').", key="notes_input")
        
        submitted = st.form_submit_button("Log Emotional Data", type="primary")
        
        if submitted:
            log_mood_entry(mood, activity, notes)
            st.rerun() 
            

    # --- History and Visualization ---
    st.subheader("History & Trends")
    
    if not st.session_state['mood_history'].empty:
        # Display the trend chart
        df_history = st.session_state['mood_history'].copy()
        df_history['Date'] = pd.to_datetime(df_history['Date'])
        df_history = df_history.set_index('Date')
        
        st.markdown("", unsafe_allow_html=True)
        st.line_chart(df_history[['Mood', 'Activity']], use_container_width=True)
        st.markdown(f"<p style='color:{ACCENT_CYAN}; font-size: 0.9rem;'>*When the 'Mood' line dips below the 'Activity' line, you are over-extending, risking burnout.</p>", unsafe_allow_html=True)
        
        st.caption("Raw Data Log:")
        st.dataframe(df_history.tail(10))

# Execute the page render function
emotional_tracker_page()
